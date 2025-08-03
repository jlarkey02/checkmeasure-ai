# Vercel serverless function handler
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the simplified FastAPI app
try:
    from main import app
    print("✓ Loaded simplified Vercel backend")
except ImportError as e:
    print(f"⚠️ Import failed: {e}")
    # Create a minimal FastAPI app as last resort
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def root():
        return {"error": "Backend import failed", "details": str(e)}
    
    @app.get("/health")
    def health():
        return {"status": "error", "message": "Import failed"}

# Export handler for Vercel
handler = app