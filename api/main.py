from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import logging
import sys
import os

# Add the project root to Python path for local development
if os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'services')):
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Try importing from parent directory structure (for Vercel)
try:
    from services.auth_service import AuthService
    from services.bioinformatics_service import BioinformaticsService
    from services.literature_service import LiteratureService
    from services.free_ai_service import FreeAIService
    from services.bio_apis_service import BioinformaticsAPIsService
    from services.public_datasets_service import PublicDatasetsService
    from services.analysis_templates_service import AnalysisTemplatesService
    from services.research_workflows_service import ResearchWorkflowsService
    from services.enterprise_service import EnterpriseService
    from models.database import engine, Base
    from utils.security import SecurityUtils
    from utils.logging import setup_logging
    from utils.config import get_settings
except ImportError:
    # Try importing from same directory (alternative structure)
    import sys
    import os
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    
    from services.auth_service import AuthService
    from services.bioinformatics_service import BioinformaticsService
    from services.literature_service import LiteratureService
    from services.free_ai_service import FreeAIService
    from services.bio_apis_service import BioinformaticsAPIsService
    from services.public_datasets_service import PublicDatasetsService
    from services.analysis_templates_service import AnalysisTemplatesService
    from services.research_workflows_service import ResearchWorkflowsService
    from services.enterprise_service import EnterpriseService
    from models.database import engine, Base
    from utils.security import SecurityUtils
    from utils.logging import setup_logging
    from utils.config import get_settings

# Initialize settings and logging
settings = get_settings()
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BioIntel.AI - Bioinformatics Assistant",
    description="AI-powered bioinformatics platform for gene expression analysis and literature summarization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Security middleware
class SecurityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Add security headers
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        return response

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
        
        return response

# Add middleware
app.add_middleware(SecurityMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Trusted hosts (for production)
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["biointel.ai", "*.biointel.ai", "*.vercel.app"]
    )

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Initialize services
        await AuthService.initialize()
        await BioinformaticsService.initialize()
        await LiteratureService.initialize()
        await FreeAIService.initialize()
        await BioinformaticsAPIsService.initialize()
        await PublicDatasetsService.initialize()
        await AnalysisTemplatesService.initialize()
        await ResearchWorkflowsService.initialize()
        await EnterpriseService.initialize()
        
        logger.info("BioIntel.AI API started successfully")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "error": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint for monitoring"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }
    
    # Check database connectivity
    try:
        from models.database import engine
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check optional dependencies
    try:
        from services.bioinformatics_service import SKLEARN_AVAILABLE, PLOTTING_AVAILABLE
        from services.free_ai_service import TRANSFORMERS_AVAILABLE
        from services.reports_service import WEASYPRINT_AVAILABLE, DOCX_AVAILABLE
        
        health_status["features"] = {
            "machine_learning": SKLEARN_AVAILABLE,
            "plotting": PLOTTING_AVAILABLE,
            "ai_processing": TRANSFORMERS_AVAILABLE,
            "pdf_generation": WEASYPRINT_AVAILABLE,
            "docx_generation": DOCX_AVAILABLE
        }
    except Exception as e:
        health_status["features"] = f"error: {str(e)}"
    
    return health_status

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to BioIntel.AI - Bioinformatics Assistant",
        "version": "1.0.0",
        "documentation": "/docs",
        "health": "/health"
    }

# Import and include routers
from api.auth import router as auth_router
from api.bioinformatics import router as bio_router
from api.literature import router as literature_router
from api.reports import router as reports_router
from api.enterprise import router as enterprise_router
from api.workflows import router as workflows_router

# Include API routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(bio_router, prefix="/api/bio", tags=["Bioinformatics"])
app.include_router(literature_router, prefix="/api/literature", tags=["Literature"])
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"])
app.include_router(enterprise_router, prefix="/api/enterprise", tags=["Enterprise"])
app.include_router(workflows_router, prefix="/api/workflows", tags=["Workflows"])

# For Vercel deployment
def handler(request, response):
    """Vercel handler function"""
    return app(request, response)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)