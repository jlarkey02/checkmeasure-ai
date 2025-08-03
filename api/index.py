# Vercel serverless function handler
import sys
import os

# Add backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the Vercel-compatible FastAPI app
try:
    from backend.main_vercel import app
    print("✓ Loaded Vercel-compatible backend")
except ImportError as e:
    print(f"⚠️ Vercel backend failed, falling back to main: {e}")
    from backend.main import app

# Export handler for Vercel
handler = app