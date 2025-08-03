from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from utils.error_logger import log_error, log_info
import traceback
import signal
import sys
import os
import time

print("\n" + "="*50)
print("=== BACKEND STARTING (VERCEL MODE) ===")
print("="*50)
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"PID: {os.getpid()}")

# Import routers with error handling - using Vercel-compatible versions
print("\n✓ Importing routers...")
try:
    from api.routers import calculations, materials, projects, debug, agents
    from api.routers import pdf_processing_vercel as pdf_processing
    print("  ✓ All routers imported successfully (Vercel mode)")
except Exception as e:
    print(f"  ✗ ERROR importing routers: {e}")
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(
    title="Building Measurements API (Vercel)",
    description="Construction material calculation assistant for Australian residential projects - Vercel deployment",
    version="1.0.0"
)

# Configure CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for Vercel deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests for debugging"""
    start_time = time.time()
    
    # Log the incoming request
    print(f"\n[REQUEST] {request.method} {request.url.path}?{request.url.query}")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Log the response
        print(f"[RESPONSE] {response.status_code} - {process_time:.3f}s")
        
        # Special logging for 404s
        if response.status_code == 404:
            print(f"[WARNING] 404 Not Found for: {request.url.path}")
            print("[DEBUG] Available routes:")
            for route in app.routes:
                if hasattr(route, 'path'):
                    print(f"  - {route.path}")
        
        return response
    except Exception as e:
        print(f"[ERROR] Request failed: {str(e)}")
        raise

# Global exception handler to prevent server crashes
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions to prevent server crashes"""
    error_id = log_error(exc, "global_exception_handler", additional_info={
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc()
    })
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "error_id": error_id,
            "path": request.url.path,
            "deployment": "vercel"
        }
    )

# Include routers with logging
print("\n✓ Registering routers...")
try:
    app.include_router(calculations.router, prefix="/api/calculations", tags=["calculations"])
    print("  ✓ Calculations router registered at /api/calculations")
    
    app.include_router(materials.router, prefix="/api/materials", tags=["materials"])
    print("  ✓ Materials router registered at /api/materials")
    
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    print("  ✓ Projects router registered at /api/projects")
    
    app.include_router(pdf_processing.router, prefix="/api/pdf", tags=["pdf"])
    print("  ✓ PDF processing router registered at /api/pdf (Vercel compatible)")
    
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
    print("  ✓ Debug router registered at /api/debug")
    
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    print("  ✓ Agents router registered at /api/agents")
    
except Exception as e:
    print(f"\n✗ ERROR registering routers: {e}")
    traceback.print_exc()

@app.get("/")
async def root():
    return {
        "message": "Building Measurements API is running",
        "deployment": "vercel",
        "features": {
            "calculations": "available",
            "materials": "available", 
            "pdf_processing": "limited",
            "agents": "available"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "deployment": "vercel",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S')
    }

@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": route.name if hasattr(route, 'name') else None
            })
    return {
        "total_routes": len(routes), 
        "routes": sorted(routes, key=lambda x: x['path']),
        "deployment": "vercel"
    }

@app.on_event("startup")
async def startup_event():
    """Log when the application starts"""
    print("\n" + "="*50)
    print("=== BACKEND READY (VERCEL) ===")
    print("="*50)
    
    log_info(f"Backend starting up in Vercel mode - PID: {os.getpid()}", "main.startup")
    
    # Check element registry initialization
    try:
        from core.calculators.element_types import element_registry
        print(f"\n✓ Element registry initialized with {len(element_registry._types)} types")
        log_info(f"Element registry initialized with {len(element_registry._types)} types", "main.startup")
        
        # List all registered routes
        print("\n✓ Registered API routes:")
        for route in app.routes:
            if hasattr(route, 'path') and hasattr(route, 'methods'):
                if route.path.startswith('/api'):
                    methods = ', '.join(route.methods)
                    print(f"  - {methods} {route.path}")
                    
        print("\n✓ Vercel deployment ready")
        
    except Exception as e:
        print(f"\n✗ ERROR in startup: {e}")
        traceback.print_exc()

@app.on_event("shutdown")
async def shutdown_event():
    """Log when the application shuts down"""
    log_info("Backend shutdown event triggered (Vercel)", "main.shutdown")
    log_info(f"Process {os.getpid()} ending", "main.shutdown")

if __name__ == "__main__":
    import uvicorn
    
    print("\n✓ Starting Uvicorn server in Vercel mode...")
    try:
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"\n✗ ERROR: Uvicorn crashed: {e}")
        traceback.print_exc()
    finally:
        print("\n✓ Uvicorn server stopped")