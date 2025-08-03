from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback
import sys
import os

# Create a minimal version for Vercel deployment
app = FastAPI(
    title="Building Measurements API (Demo)",
    description="Construction material calculation assistant - Demo version",
    version="1.0.0-demo"
)

# Configure CORS for all origins in demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Try to import routers, but handle missing dependencies gracefully
try:
    from api.routers import calculations, materials
    app.include_router(calculations.router, prefix="/api/calculations", tags=["calculations"])
    app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
except ImportError as e:
    print(f"Warning: Some routers could not be imported: {e}")

@app.get("/")
async def root():
    return {
        "message": "Building Measurements API is running (Demo Version)",
        "note": "This is a limited demo version. Some features like PDF processing are disabled.",
        "endpoints": [
            "/api/calculations/joists",
            "/api/materials/",
            "/health"
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "demo"}

@app.get("/api/test")
async def test_endpoint():
    return {"message": "API is working!", "timestamp": os.environ.get("VERCEL_GIT_COMMIT_SHA", "local")}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "note": "This is a demo version with limited functionality"
        }
    )

# Export for Vercel
app = app