"""
Background Task Processing
Async job processing without Celery (simpler for MVP)
"""

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..db.models import AnalysisJob, Result, Query
from ..core.industry_detector import IndustryDetector
from ..core.query_generator import QueryGenerator
from ..core.llm_tester import LLMTester
from ..core.mention_detector import MentionDetector


async def process_analysis_job_async(
    job_id: str,
    brand_name: str,
    website_url: str,
    query_count: int = 60
):
    """
    Main async processing function
    """
    db = SessionLocal()
    
    try:
        # Update job status
        job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
        if not job:
            return
        
        job.status = 'processing'
        job.progress = 5
        db.commit()
        
        # Step 1: Detect Industry (10%)
        print(f"[{job_id}] Step 1: Detecting industry...")
        detector = IndustryDetector()
        industry = detector.detect_industry(brand_name, website_url)
        
        job.industry = industry
        job.progress = 15
        db.commit()
        print(f"[{job_id}] Industry detected: {industry}")
        
        # Step 2: Generate Queries (25%)
        print(f"[{job_id}] Step 2: Generating queries...")
        generator = QueryGenerator()
        queries = generator.generate_queries(industry, brand_name, query_count)
        
        # Save queries
        for query_text in queries:
            query = Query(job_id=job_id, query_text=query_text)
            db.add(query)
        db.commit()
        
        job.progress = 25
        job.total_queries = len(queries)
        db.commit()
        print(f"[{job_id}] Generated {len(queries)} queries")
        
        # Step 3: Test with LLMs (25-90%)
        print(f"[{job_id}] Step 3: Testing queries across AI models...")
        tester = LLMTester()
        mention_detector = MentionDetector(brand_name)
        
        total_tests = len(queries)
        completed_tests = 0
        
        # Process in batches of 5
        for i in range(0, len(queries), 5):
            batch = queries[i:i+5]
            
            for query_text in batch:
                # Test across all models
                results = await tester.test_single_query(query_text)
                
                # Analyze each result
                for llm_result in results:
                    analysis = mention_detector.analyze_response(llm_result['response'])
                    
                    # Store result
                    result = Result(
                        job_id=job_id,
                        query_text=query_text,
                        model=llm_result['model'],
                        brand_mentioned=analysis['mentioned'],
                        mention_confidence=analysis['confidence'],
                        match_type=analysis['match_type'],
                        brand_rank=analysis['rank'],
                        rank_context=analysis.get('rank_context', ''),
                        competitors=analysis['competitors'],
                        competitor_count=len(analysis['competitors']),
                        full_response=llm_result['response'],
                        response_length=len(llm_result['response']),
                        tokens_used=llm_result.get('tokens'),
                        error=llm_result.get('error'),
                        citations=llm_result.get('citations')
                    )
                    db.add(result)
                
                completed_tests += 1
                
                # Update progress
                progress = 25 + int((completed_tests / total_tests) * 65)
                job.progress = min(progress, 90)
                db.commit()
                
                print(f"[{job_id}] Progress: {job.progress}% ({completed_tests}/{total_tests})")
            
            # Small delay between batches
            await asyncio.sleep(0.5)
        
        # Step 4: Calculate Final Scores (90-100%)
        print(f"[{job_id}] Step 4: Calculating visibility scores...")
        
        all_results = db.query(Result).filter(Result.job_id == job_id).all()
        
        from ..core.visibility_scorer import VisibilityScorer
        scorer = VisibilityScorer(brand_name)
        
        scorer_results = []
        for r in all_results:
            scorer_results.append({
                'mentioned': r.brand_mentioned,
                'rank': r.brand_rank,
                'competitors': r.competitors or [],
                'response': r.full_response or '',
                'model': r.model
            })
        
        scores = scorer.calculate_visibility_score(scorer_results)
        
        job.overall_score = scores['overall_score']
        job.mention_rate = scores['mention_rate']
        job.total_mentions = scores['mentions']
        job.progress = 100
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        db.commit()
        
        print(f"[{job_id}] Analysis completed! Score: {scores['overall_score']}")
        
    except Exception as e:
        print(f"[{job_id}] Error: {str(e)}")
        job.status = 'failed'
        job.error_message = str(e)
        db.commit()
    
    finally:
        db.close()


def process_analysis_job(
    job_id: str,
    brand_name: str,
    website_url: str,
    query_count: int = 60
):
    """
    Wrapper to run async function in background
    """
    asyncio.run(process_analysis_job_async(
        job_id, brand_name, website_url, query_count
    ))
