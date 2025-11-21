"""
Background Task Processing
Async job processing without Celery (simpler for MVP)
"""

import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import json

from ..db.database import SessionLocal
from ..db.models import AnalysisJob, Result, Query
from ..core.industry_detector import IndustryDetector
from ..core.query_generator import QueryGenerator
from ..services.service_manager import AIServiceManager
from ..core.mention_detector import MentionDetector
from ..utils.logger import setup_logger

logger = setup_logger("worker")


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
        logger.info(f"[{job_id}] Step 1: Detecting industry...")
        detector = IndustryDetector()
        industry = detector.detect_industry(brand_name, website_url)
        
        job.industry = industry
        job.progress = 15
        db.commit()
        logger.info(f"[{job_id}] Industry detected: {industry}")
        
        # Step 2: Generate Queries (25%)
        logger.info(f"[{job_id}] Step 2: Generating queries...")
        generator = QueryGenerator()
        
        # Generate queries with timeout (max 30 seconds)
        try:
            queries = await asyncio.wait_for(
                asyncio.to_thread(generator.generate_queries, industry, brand_name, query_count),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"[{job_id}] Query generation timeout, using templates only")
            queries = generator.generate_queries(industry, brand_name, query_count // 2)
        
        # Bulk insert queries (faster than one-by-one)
        db.bulk_save_objects([Query(job_id=job_id, query_text=q) for q in queries])
        db.commit()
        
        job.progress = 25
        job.total_queries = len(queries)
        db.commit()
        logger.info(f"[{job_id}] Generated {len(queries)} queries in parallel")
        
        # Step 3: Test with LLMs (25-90%)
        logger.info(f"[{job_id}] Step 3: Testing queries across AI models...")
        service_manager = AIServiceManager()
        mention_detector = MentionDetector(brand_name)
        
        # Get available models
        available_models = service_manager.get_available_models()
        if not available_models:
            logger.error(f"[{job_id}] No AI models available!")
            job.status = 'failed'
            job.error_message = "No AI API keys configured"
            db.commit()
            return
        
        logger.info(f"[{job_id}] Testing with models: {', '.join(available_models)}")
        
        total_tests = len(queries)
        completed_tests = 0
        results_batch = []
        
        # Process in batches of 10 queries (truly parallel)
        batch_size = 5  # Reduced from 10 for stability
        for i in range(0, len(queries), batch_size):
            batch = queries[i:i+batch_size]
            
            # Create tasks for all queries in batch - TRUE PARALLELISM
            batch_tasks = []
            for query_text in batch:
                batch_tasks.append(service_manager.query_all(query_text))
            
            # Execute ALL queries in batch simultaneously with timeout
            try:
                logger.info(f"[{job_id}] Executing batch of {len(batch)} queries in parallel...")
                batch_results = await asyncio.wait_for(
                    asyncio.gather(*batch_tasks, return_exceptions=True),
                    timeout=20.0  # 20 second timeout per batch
                )
            except asyncio.TimeoutError:
                logger.warning(f"[{job_id}] Batch timeout, skipping...")
                completed_tests += len(batch)
                continue
            
            # Process all results from batch
            for query_text, results_dict in zip(batch, batch_results):
                if isinstance(results_dict, Exception):
                    logger.error(f"[{job_id}] Query failed: {str(results_dict)[:100]}")
                    completed_tests += 1
                    continue
                
                if not isinstance(results_dict, dict):
                    logger.error(f"[{job_id}] Invalid result type: {type(results_dict)}")
                    completed_tests += 1
                    continue
                
                # Analyze each model's result
                for model_name, llm_result in results_dict.items():
                    if not llm_result.get('success'):
                        logger.debug(f"[{job_id}] {model_name} failed: {llm_result.get('error', 'Unknown')[:50]}")
                        continue
                    
                    analysis = mention_detector.analyze_response(llm_result['response'])
                    
                    # Add to batch (bulk insert later)
                    # Convert tokens dict to JSON string for SQLite
                    tokens = llm_result.get('tokens')
                    tokens_str = json.dumps(tokens) if tokens else None
                    
                    # Get sentiment with fallback for old code
                    sentiment = analysis.get('sentiment', 'N/A')
                    sentiment_score = analysis.get('sentiment_score', 0.5)
                    
                    results_batch.append(Result(
                        job_id=job_id,
                        query_text=query_text,
                        model=model_name,
                        brand_mentioned=analysis['mentioned'],
                        mention_confidence=analysis['confidence'],
                        match_type=analysis['match_type'],
                        brand_rank=analysis['rank'],
                        rank_context=analysis.get('rank_context', ''),
                        competitors=analysis['competitors'],
                        competitor_count=len(analysis['competitors']),
                        full_response=llm_result['response'],
                        response_length=len(llm_result['response']),
                        tokens_used=tokens_str,
                        sentiment=sentiment,
                        sentiment_score=sentiment_score,
                        error=llm_result.get('error'),
                        citations=llm_result.get('citations')
                    ))
                
                completed_tests += 1
            
            # Bulk insert results for this batch (MUCH FASTER)
            if results_batch:
                try:
                    db.bulk_save_objects(results_batch)
                    db.commit()
                    logger.info(f"[{job_id}] Saved {len(results_batch)} results")
                    results_batch = []
                except Exception as e:
                    logger.error(f"[{job_id}] DB error: {str(e)}")
                    db.rollback()
            
            # Update progress
            progress = 25 + int((completed_tests / total_tests) * 65)
            job.progress = min(progress, 90)
            db.commit()
            logger.info(f"[{job_id}] Progress: {job.progress}% ({completed_tests}/{total_tests})")
        
        # Step 4: Calculate Final Scores (90-100%)
        logger.info(f"[{job_id}] Step 4: Calculating visibility scores...")
        
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
        
        logger.info(f"[{job_id}] ✅ Analysis completed! Score: {scores['overall_score']}")
        
    except Exception as e:
        logger.error(f"[{job_id}] ❌ Error: {str(e)}")
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
