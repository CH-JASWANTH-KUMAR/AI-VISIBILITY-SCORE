"""
Demo Data Caching Script
Run this before hackathon demo to cache example brand results
"""

import asyncio
from backend.core.industry_detector import IndustryDetector
from backend.core.query_generator import QueryGenerator
from backend.core.llm_tester import LLMTester
from backend.core.mention_detector import MentionDetector
from backend.core.visibility_scorer import VisibilityScorer
from backend.core.report_generator import ReportGenerator
from backend.db.database import SessionLocal, init_db
from backend.db.models import AnalysisJob, Result, Query
from datetime import datetime
import uuid


async def create_demo_data(brand_name, website_url):
    """Create cached demo data for a brand"""
    print(f"\n{'='*60}")
    print(f"Creating demo data for: {brand_name}")
    print(f"{'='*60}\n")
    
    db = SessionLocal()
    job_id = str(uuid.uuid4())
    
    try:
        # Step 1: Detect Industry
        print("Step 1: Detecting industry...")
        detector = IndustryDetector()
        industry = detector.detect_industry(brand_name, website_url)
        print(f"✓ Industry: {industry}")
        
        # Create job
        job = AnalysisJob(
            job_id=job_id,
            brand_name=brand_name,
            website_url=website_url,
            industry=industry,
            status='processing',
            progress=15
        )
        db.add(job)
        db.commit()
        
        # Step 2: Generate Queries
        print("\nStep 2: Generating queries...")
        generator = QueryGenerator()
        queries = generator.generate_queries(industry, brand_name, 20)  # Use 20 for demo
        print(f"✓ Generated {len(queries)} queries")
        
        # Save queries
        for query_text in queries:
            query = Query(job_id=job_id, query_text=query_text)
            db.add(query)
        db.commit()
        
        # Step 3: Test with LLMs
        print("\nStep 3: Testing with AI models (this will take 5-10 minutes)...")
        tester = LLMTester()
        mention_detector = MentionDetector(brand_name)
        
        for i, query_text in enumerate(queries):
            print(f"  Testing query {i+1}/{len(queries)}: {query_text[:50]}...")
            
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
                    error=llm_result.get('error')
                )
                db.add(result)
            
            db.commit()
        
        # Step 4: Calculate Scores
        print("\nStep 4: Calculating scores...")
        all_results = db.query(Result).filter(Result.job_id == job_id).all()
        
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
        job.total_queries = len(queries)
        job.progress = 100
        job.status = 'completed'
        job.completed_at = datetime.utcnow()
        db.commit()
        
        print(f"\n{'='*60}")
        print(f"✓ Demo data created successfully!")
        print(f"  Job ID: {job_id}")
        print(f"  Overall Score: {scores['overall_score']:.1f}")
        print(f"  Mentions: {scores['mentions']}/{len(queries)}")
        print(f"{'='*60}\n")
        
        return job_id
        
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        job.status = 'failed'
        job.error_message = str(e)
        db.commit()
        raise
    
    finally:
        db.close()


async def main():
    """Create demo data for multiple brands"""
    print("\n" + "="*60)
    print("AI VISIBILITY TRACKER - DEMO DATA GENERATOR")
    print("="*60)
    
    # Initialize database
    print("\nInitializing database...")
    init_db()
    print("✓ Database ready")
    
    # Demo brands
    demo_brands = [
        ("HelloFresh", "https://www.hellofresh.com"),
        ("Sunbasket", "https://www.sunbasket.com"),
    ]
    
    for brand_name, website_url in demo_brands:
        try:
            await create_demo_data(brand_name, website_url)
        except Exception as e:
            print(f"Failed to create demo data for {brand_name}: {e}")
            continue
    
    print("\n" + "="*60)
    print("✓ ALL DEMO DATA CREATED SUCCESSFULLY!")
    print("="*60)
    print("\nYou can now access the dashboard at:")
    print("http://localhost:3000/dashboard/{job_id}")
    print("\nOr start a new analysis at:")
    print("http://localhost:3000")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
