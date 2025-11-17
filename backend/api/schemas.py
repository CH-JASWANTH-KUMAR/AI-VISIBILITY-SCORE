"""
Pydantic Models for API Request/Response Validation
"""

from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List
from datetime import datetime


class AnalyzeRequest(BaseModel):
    """Request to analyze brand visibility"""
    brand_name: str = Field(..., min_length=1, max_length=200, description="Brand name to analyze")
    website_url: str = Field(..., description="Brand website URL")
    query_count: Optional[int] = Field(60, ge=10, le=100, description="Number of queries to generate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brand_name": "HelloFresh",
                "website_url": "https://www.hellofresh.com",
                "query_count": 60
            }
        }


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    brand_name: str
    website_url: str
    industry: Optional[str]
    status: str
    progress: int
    overall_score: Optional[float]
    mention_rate: Optional[float]
    total_queries: Optional[int]
    total_mentions: Optional[int]
    created_at: Optional[str]
    completed_at: Optional[str]
    error_message: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "abc123",
                "brand_name": "HelloFresh",
                "website_url": "https://www.hellofresh.com",
                "industry": "Meal Kits & Food Delivery",
                "status": "completed",
                "progress": 100,
                "overall_score": 78.5,
                "mention_rate": 65.0,
                "total_queries": 60,
                "total_mentions": 39,
                "created_at": "2025-11-16T10:00:00",
                "completed_at": "2025-11-16T10:15:00",
                "error_message": None
            }
        }


class QueryResult(BaseModel):
    """Individual query result"""
    query_text: str
    model: str
    brand_mentioned: bool
    mention_confidence: Optional[float]
    brand_rank: Optional[int]
    competitors: List[str]
    intent_category: Optional[str]
    full_response: str


class ReportResponse(BaseModel):
    """Full report data"""
    job_id: str
    brand_name: str
    industry: str
    overall_score: float
    visibility_breakdown: dict
    results: List[QueryResult]
    top_competitors: List[dict]
    model_breakdown: dict
    category_breakdown: dict


class DownloadResponse(BaseModel):
    """Download link response"""
    download_url: str
    filename: str
    format: str  # 'excel' or 'csv'
