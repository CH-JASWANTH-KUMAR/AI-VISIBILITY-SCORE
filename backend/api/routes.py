"""
FastAPI Routes
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import uuid
import os

from .schemas import AnalyzeRequest, JobStatusResponse, ReportResponse, DownloadResponse
from ..db.database import get_db
from ..db.models import AnalysisJob, Result
from ..workers.tasks import process_analysis_job

router = APIRouter()


@router.post("/analyze", response_model=dict, status_code=202)
async def create_analysis(
    request: AnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Start brand visibility analysis
    Returns job_id for tracking progress
    """
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Create job record
    job = AnalysisJob(
        job_id=job_id,
        brand_name=request.brand_name,
        website_url=request.website_url,
        status='pending',
        progress=0
    )
    db.add(job)
    db.commit()
    
    # Queue background task
    background_tasks.add_task(
        process_analysis_job,
        job_id=job_id,
        brand_name=request.brand_name,
        website_url=request.website_url,
        query_count=request.query_count
    )
    
    return {
        "job_id": job_id,
        "status": "pending",
        "message": f"Analysis started for {request.brand_name}"
    }


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """
    Get analysis job status
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job.to_dict()


@router.get("/report/{job_id}")
async def get_report(job_id: str, db: Session = Depends(get_db)):
    """
    Get full analysis report
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != 'completed':
        raise HTTPException(
            status_code=400,
            detail=f"Job status is '{job.status}'. Wait for completion."
        )
    
    # Get all results
    results = db.query(Result).filter(Result.job_id == job_id).all()
    
    if not results:
        raise HTTPException(status_code=404, detail="No results found")
    
    # Convert to dict
    results_data = [r.to_dict() for r in results]
    
    # Calculate additional metrics
    from ..core.visibility_scorer import VisibilityScorer
    scorer = VisibilityScorer(job.brand_name)
    
    # Prepare results in scorer format
    scorer_results = []
    for r in results_data:
        scorer_results.append({
            'mentioned': r['brand_mentioned'],
            'rank': r['brand_rank'],
            'competitors': r['competitors'] or [],
            'response': r['full_response'] or '',
            'model': r['model'],
            'intent_category': r['intent_category']
        })
    
    # Calculate scores
    visibility_scores = scorer.calculate_visibility_score(scorer_results)
    category_breakdown = scorer.category_breakdown(scorer_results)
    model_breakdown = scorer.model_breakdown(scorer_results)
    top_competitors = scorer.get_top_competitors(scorer_results, 10)
    
    return {
        "job_id": job_id,
        "brand_name": job.brand_name,
        "industry": job.industry,
        "overall_score": visibility_scores['overall_score'],
        "visibility_breakdown": visibility_scores,
        "results": results_data,
        "top_competitors": [{"name": name, "mentions": count} for name, count in top_competitors],
        "model_breakdown": model_breakdown,
        "category_breakdown": category_breakdown
    }


@router.get("/download/{job_id}/{format}")
async def download_report(
    job_id: str,
    format: str,
    db: Session = Depends(get_db)
):
    """
    Download report as Excel or CSV
    format: 'excel' or 'csv'
    """
    from fastapi.responses import FileResponse
    import os
    
    if format not in ['excel', 'csv']:
        raise HTTPException(status_code=400, detail="Format must be 'excel' or 'csv'")
    
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != 'completed':
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    # Get results
    results = db.query(Result).filter(Result.job_id == job_id).all()
    results_data = [r.to_dict() for r in results]
    
    # Generate report
    from ..core.report_generator import ReportGenerator
    from ..core.visibility_scorer import VisibilityScorer
    
    scorer = VisibilityScorer(job.brand_name)
    scorer_results = []
    for r in results_data:
        scorer_results.append({
            'query': r['query_text'],
            'mentioned': r['brand_mentioned'],
            'confidence': r['mention_confidence'],
            'match_type': r['match_type'],
            'rank': r['brand_rank'],
            'rank_context': r['rank_context'],
            'competitors': r['competitors'] or [],
            'competitor_count': r['competitor_count'],
            'response': r['full_response'] or '',
            'model': r['model'],
            'timestamp': r['timestamp'],
            'tokens': r['tokens_used'],
            'error': r['error'],
            'citations': r['citations'],
            'intent_category': r['intent_category']
        })
    
    visibility_scores = scorer.calculate_visibility_score(scorer_results)
    
    generator = ReportGenerator(job.brand_name, job.industry or "Unknown")
    df, summary_df, category_df, model_df = generator.generate_report(
        scorer_results,
        visibility_scores
    )
    
    # Save file
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    if format == 'excel':
        filepath = generator.save_excel(df, summary_df, category_df, model_df, output_dir)
    else:
        filepath = generator.save_csv(df, output_dir)
    
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type='application/octet-stream'
    )


@router.get("/jobs")
async def list_jobs(limit: int = 20, db: Session = Depends(get_db)):
    """
    List recent analysis jobs
    """
    jobs = db.query(AnalysisJob)\
        .order_by(AnalysisJob.created_at.desc())\
        .limit(limit)\
        .all()
    
    return [job.to_dict() for job in jobs]


@router.delete("/job/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """
    Delete analysis job and its results
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Delete results
    db.query(Result).filter(Result.job_id == job_id).delete()
    
    # Delete job
    db.delete(job)
    db.commit()
    
    return {"message": f"Job {job_id} deleted successfully"}


@router.get("/advanced-analytics/{job_id}")
async def get_advanced_analytics(job_id: str, db: Session = Depends(get_db)):
    """
    Get ALL 10 differentiating features for a completed job
    Features:
    1. Why Not Mentioned analysis
    2. Competitor Reverse Engineering
    3. Improvement Simulator
    4. Sentiment Analysis
    5. Model Behavior Insights
    6. Query Difficulty Scoring
    7. Context-Aware Recommendations
    8. Missed Opportunities Detection
    9. Competitor Dominance Clustering
    10. Visibility Timeline Projection
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != 'completed':
        raise HTTPException(status_code=400, detail="Analysis not complete yet")
    
    # Get results
    results = db.query(Result).filter(Result.job_id == job_id).all()
    results_data = [r.to_dict() for r in results]
    
    # Import all feature modules
    from ..core.gap_analyzer import GapAnalyzer
    from ..core.competitor_insights import CompetitorInsights
    from ..core.improvement_simulator import ImprovementSimulator
    from ..core.model_behavior import ModelBehaviorAnalyzer
    from ..core.advanced_analytics import AdvancedAnalytics
    from ..core.visibility_scorer import VisibilityScorer
    
    # Get current score
    scorer = VisibilityScorer(job.brand_name)
    scorer_results = []
    for r in results_data:
        scorer_results.append({
            'mentioned': r['brand_mentioned'],
            'rank': r['brand_rank'],
            'competitors': r['competitors'] or [],
            'response': r['full_response'] or '',
            'model': r['model'],
            'intent_category': r['intent_category'],
            'sentiment': r.get('sentiment', 'N/A')
        })
    
    visibility_scores = scorer.calculate_visibility_score(scorer_results)
    current_score = visibility_scores['overall_score']
    
    # Feature #1: Gap Analysis (Why Not Mentioned)
    gap_analyzer = GapAnalyzer(job.brand_name)
    gap_analysis = gap_analyzer.analyze_non_mentions(scorer_results)
    
    # Feature #2: Competitor Insights
    comp_insights = CompetitorInsights(job.brand_name, job.industry or "Unknown")
    competitor_analysis = comp_insights.analyze_competitors(scorer_results)
    
    # Feature #4: Sentiment already in results (added to mention_detector)
    sentiment_summary = {
        'positive': len([r for r in results_data if r.get('sentiment') == 'Positive']),
        'neutral': len([r for r in results_data if r.get('sentiment') == 'Neutral']),
        'negative': len([r for r in results_data if r.get('sentiment') == 'Negative']),
        'hesitant': len([r for r in results_data if r.get('sentiment') == 'Hesitant'])
    }
    
    # Feature #5: Model Behavior
    model_analyzer = ModelBehaviorAnalyzer(job.brand_name)
    model_insights = model_analyzer.analyze_model_patterns(scorer_results)
    
    # Features #6-10: Advanced Analytics Bundle
    advanced = AdvancedAnalytics(job.brand_name, job.industry or "Unknown", current_score)
    advanced_results = advanced.run_full_analysis(
        scorer_results,
        gap_analysis,
        competitor_analysis
    )
    
    return {
        'job_id': job_id,
        'brand_name': job.brand_name,
        'current_score': current_score,
        
        # All 10 features
        'feature_1_gap_analysis': gap_analysis,
        'feature_2_competitor_insights': competitor_analysis,
        'feature_4_sentiment_analysis': sentiment_summary,
        'feature_5_model_behavior': model_insights,
        'feature_6_query_difficulty': advanced_results['query_difficulty'],
        'feature_7_recommendations': advanced_results['recommendations'],
        'feature_8_missed_opportunities': advanced_results['missed_opportunities'],
        'feature_9_competitor_clusters': advanced_results['competitor_clusters'],
        'feature_10_timeline': advanced_results['improvement_timeline'],
        
        'summary': {
            'total_features': 10,
            'differentiation_level': 'Maximum',
            'standout_features': [
                'Why Not Mentioned Explanations',
                'AI-Powered Competitor Strategy',
                'Improvement Simulator',
                'Multi-Model Behavior Analysis',
                'Missed Opportunities Detection'
            ]
        }
    }


@router.post("/simulate-improvement/{job_id}")
async def simulate_improvement(
    job_id: str,
    improvements: dict,
    db: Session = Depends(get_db)
):
    """
    Feature #3: Run improvement simulation with user inputs
    
    Request body example:
    {
        "new_tagline": "Affordable gourmet meals delivered daily",
        "new_features": ["Custom meal plans", "Dietary filters"],
        "new_keywords": ["budget meal kit", "healthy delivery"],
        "page_updates": ["Pricing comparison page", "Customer reviews page"],
        "pricing_strategy": "Introduce $6.99/serving starter plan"
    }
    """
    job = db.query(AnalysisJob).filter(AnalysisJob.job_id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != 'completed':
        raise HTTPException(status_code=400, detail="Analysis not complete")
    
    # Get results
    results = db.query(Result).filter(Result.job_id == job_id).all()
    results_data = [r.to_dict() for r in results]
    
    # Get current score
    from ..core.visibility_scorer import VisibilityScorer
    from ..core.improvement_simulator import ImprovementSimulator
    
    scorer = VisibilityScorer(job.brand_name)
    scorer_results = []
    for r in results_data:
        scorer_results.append({
            'mentioned': r['brand_mentioned'],
            'rank': r['brand_rank'],
            'competitors': r['competitors'] or [],
            'response': r['full_response'] or '',
            'model': r['model'],
            'intent_category': r['intent_category']
        })
    
    visibility_scores = scorer.calculate_visibility_score(scorer_results)
    current_score = visibility_scores['overall_score']
    
    # Run simulation
    simulator = ImprovementSimulator(job.brand_name, job.industry or "Unknown", current_score)
    simulation_result = simulator.simulate_improvement(scorer_results, improvements)
    
    return {
        'job_id': job_id,
        'brand_name': job.brand_name,
        'simulation': simulation_result,
        'improvements_tested': improvements
    }
