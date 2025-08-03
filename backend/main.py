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
print("=== BACKEND STARTING ===")
print("="*50)
print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"PID: {os.getpid()}")

# Import routers with error handling
print("\n✓ Importing routers...")
try:
    from api.routers import calculations, materials, projects, pdf_processing, debug, agents
    print("  ✓ All routers imported successfully")
except Exception as e:
    print(f"  ✗ ERROR importing routers: {e}")
    traceback.print_exc()
    sys.exit(1)

app = FastAPI(
    title="Building Measurements API",
    description="Construction material calculation assistant for Australian residential projects",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
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
            "path": request.url.path
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
    print("  ✓ PDF processing router registered at /api/pdf")
    
    app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
    print("  ✓ Debug router registered at /api/debug")
    
    app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
    print("  ✓ Agents router registered at /api/agents")
    
except Exception as e:
    print(f"\n✗ ERROR registering routers: {e}")
    traceback.print_exc()

@app.get("/")
async def root():
    return {"message": "Building Measurements API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

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
    return {"total_routes": len(routes), "routes": sorted(routes, key=lambda x: x['path'])}

@app.on_event("startup")
async def startup_event():
    """Log when the application starts"""
    print("\n" + "="*50)
    print("=== BACKEND READY ===")
    print("="*50)
    
    log_info(f"Backend starting up - PID: {os.getpid()}", "main.startup")
    log_info(f"Running with timeout_keep_alive=0, no worker recycling", "main.startup")
    
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
                    
        # Temporarily disable health monitor to test if it's causing issues
        # # Start a background task to monitor health
        # import asyncio
        # async def health_monitor():
        #     """Monitor backend health every 5 seconds"""
        #     start_time = time.time()
        #     while True:
        #         uptime = time.time() - start_time
        #         print(f"\n[HEALTH] Backend alive for {uptime:.1f}s - PID: {os.getpid()}")
        #         await asyncio.sleep(5)
        # 
        # # Start health monitor in background
        # asyncio.create_task(health_monitor())
        # print("\n✓ Health monitor started")
        print("\n✓ Health monitor disabled for testing")
        
    except Exception as e:
        print(f"\n✗ ERROR in startup: {e}")
        traceback.print_exc()
    
    # Set up signal handlers to understand shutdowns
    def signal_handler(sig, frame):
        sig_names = {
            signal.SIGINT: "SIGINT (Ctrl+C)",
            signal.SIGTERM: "SIGTERM (Termination)",
            signal.SIGHUP: "SIGHUP (Hangup)",
            signal.SIGUSR1: "SIGUSR1 (User-defined 1)",
            signal.SIGUSR2: "SIGUSR2 (User-defined 2)",
            signal.SIGKILL: "SIGKILL (Kill)",
            signal.SIGQUIT: "SIGQUIT (Quit)"
        }
        sig_name = sig_names.get(sig, f"Unknown signal {sig}")
        print(f"\n[SIGNAL] Received signal: {sig_name}")
        log_info(f"Received signal: {sig_name} - Backend shutting down", "main.signal_handler")
        
        # Don't call sys.exit() here - let uvicorn handle the shutdown properly
        # Just log that we received the signal
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGHUP, signal_handler)
    log_info("Signal handlers registered", "main.startup")

@app.on_event("shutdown")
async def shutdown_event():
    """Log when the application shuts down"""
    log_info("Backend shutdown event triggered", "main.shutdown")
    log_info(f"Process {os.getpid()} ending", "main.shutdown")

if __name__ == "__main__":
    import uvicorn
    import atexit
    
    def on_exit():
        print("\n" + "="*50)
        print("=== BACKEND SHUTTING DOWN ===")
        print("="*50)
        print(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        import traceback
        traceback.print_stack()
    
    atexit.register(on_exit)
    
    print("\n✓ Starting Uvicorn server...")
    try:
        uvicorn.run(
            app, 
            host="127.0.0.1", 
            port=8000,
            timeout_keep_alive=0,  # No timeout for keep-alive connections
            ws_ping_interval=None,  # Disable WebSocket ping (we don't use WS)
            ws_ping_timeout=None,   # Disable WebSocket timeout
            limit_max_requests=None, # No request limit - don't recycle workers
            log_level="info"
        )
    except Exception as e:
        print(f"\n✗ ERROR: Uvicorn crashed: {e}")
        traceback.print_exc()
    finally:
        print("\n✓ Uvicorn server stopped")