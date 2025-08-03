from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import json

# Create a minimal FastAPI app for Vercel
app = FastAPI(title="CheckMeasureAI API", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "CheckMeasureAI API is running",
        "deployment": "vercel-minimal",
        "status": "online"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "deployment": "vercel-minimal"
    }

@app.get("/api/calculations/element-types")
async def element_types():
    return {
        "element_types": [
            {
                "code": "J1",
                "description": "Joist - Floor/Ceiling", 
                "category": "structural",
                "calculator_type": "joist",
                "active": True
            }
        ]
    }

@app.post("/api/calculations/calculate")
async def calculate(request_data: dict = None):
    return {
        "element_code": "J1",
        "calculations": {"span_length": 4.0},
        "cutting_list": [{"element_code": "J1", "quantity": 1}],
        "formatted_output": "Basic calculation result",
        "deployment": "vercel-minimal"
    }

# Export for Vercel
handler = app