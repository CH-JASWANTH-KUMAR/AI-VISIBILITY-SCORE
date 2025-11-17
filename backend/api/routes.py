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
