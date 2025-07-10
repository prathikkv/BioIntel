"""
Simple Vercel-compatible entry point for BioIntel.AI
This is a minimal version for initial deployment testing
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import os
import time

# Create minimal FastAPI app
app = FastAPI(
    title="BioIntel.AI",
    description="Free AI-powered bioinformatics platform",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to BioIntel.AI",
        "status": "running",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "database": os.getenv("DATABASE_URL", "sqlite:///./biointel.db"),
        "message": "BioIntel.AI is running successfully on Vercel!"
    }

@app.get("/api/health")
async def api_health():
    """API health check"""
    return await health_check()

# For Vercel compatibility
def handler(request):
    """Vercel handler function"""
    return app