"""
FastAPI Main Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import logging
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()

from .routes import router
from ..db.database import init_db
from ..utils.logger import setup_logger
from ..services.service_manager import AIServiceManager

# Setup logging
logger = setup_logger("ai_visibility_api", level="INFO")

# Create FastAPI app
app = FastAPI(
    title="AI Visibility Score Tracker API",
    description="Track brand visibility across AI models (ChatGPT, Claude, Perplexity, Gemini)",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api/v1", tags=["Analysis"])


@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    logger.info("🚀 Starting AI Visibility Score Tracker...")
    
    # Initialize database
    logger.info("📊 Initializing database...")
    init_db()
    
    # Initialize AI services and validate API keys
    logger.info("🔑 Validating API keys...")
    service_manager = AIServiceManager()
    available_models = service_manager.get_available_models()
    
    if not available_models:
        logger.error("❌ No AI API keys configured! Please add keys to .env file")
        logger.error("   Required: OPENAI_API_KEY or GOOGLE_API_KEY")
    else:
        logger.info(f"✅ Available AI models: {', '.join(available_models)}")
    
    # Validate critical environment variables
    required_vars = ["DATABASE_URL"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.warning(f"⚠️  Missing optional environment variables: {', '.join(missing_vars)}")
    
    logger.info("✅ Application started successfully")
    logger.info(f"📍 API available at: http://localhost:{os.getenv('PORT', 8000)}")
    logger.info(f"📖 Docs available at: http://localhost:{os.getenv('PORT', 8000)}/docs")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Visibility Score Tracker",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "services": {
            "api": "running",
            "worker": "available"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging"""
    logger.error(f"❌ Unhandled exception: {type(exc).__name__}: {str(exc)}")
    logger.error(f"   Request: {request.method} {request.url}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "backend.api.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )
