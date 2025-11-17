"""
Database Models
SQLAlchemy models for PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class AnalysisJob(Base):
    """Track analysis jobs"""
    __tablename__ = 'analysis_jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    brand_name = Column(String(200), nullable=False)
    website_url = Column(String(500), nullable=False)
    industry = Column(String(100))
    status = Column(String(50), default='pending')  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100
    
    # Results
    overall_score = Column(Float)
    mention_rate = Column(Float)
    total_queries = Column(Integer)
    total_mentions = Column(Integer)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'brand_name': self.brand_name,
            'website_url': self.website_url,
            'industry': self.industry,
            'status': self.status,
            'progress': self.progress,
            'overall_score': self.overall_score,
            'mention_rate': self.mention_rate,
            'total_queries': self.total_queries,
            'total_mentions': self.total_mentions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


class Query(Base):
    """Store generated queries"""
    __tablename__ = 'queries'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), index=True, nullable=False)
    query_text = Column(Text, nullable=False)
    intent_category = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Result(Base):
    """Store individual query results"""
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), index=True, nullable=False)
    query_id = Column(Integer)
    query_text = Column(Text, nullable=False)
    
    # Model info
    model = Column(String(100), nullable=False)
    
    # Brand detection
    brand_mentioned = Column(Boolean, default=False)
    mention_confidence = Column(Float)
    match_type = Column(String(50))
    brand_rank = Column(Integer)
    rank_context = Column(Text)
    
    # Competitors
    competitors = Column(JSON)  # List of competitor names
    competitor_count = Column(Integer, default=0)
    
    # Response data
    full_response = Column(Text)
    response_length = Column(Integer)
    tokens_used = Column(Integer)
    
    # Metadata
    intent_category = Column(String(100))
    timestamp = Column(DateTime, default=datetime.utcnow)
    error = Column(Text)
    citations = Column(JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'query_text': self.query_text,
            'model': self.model,
            'brand_mentioned': self.brand_mentioned,
            'mention_confidence': self.mention_confidence,
            'match_type': self.match_type,
            'brand_rank': self.brand_rank,
            'rank_context': self.rank_context,
            'competitors': self.competitors,
            'competitor_count': self.competitor_count,
            'full_response': self.full_response,
            'response_length': self.response_length,
            'tokens_used': self.tokens_used,
            'intent_category': self.intent_category,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'error': self.error,
            'citations': self.citations
        }
