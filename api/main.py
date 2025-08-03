from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import time
import os

# Simple FastAPI app for Vercel deployment
app = FastAPI(
    title="CheckMeasureAI API",
    description="Construction material calculation assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple models
class CalculationRequest(BaseModel):
    element_code: str
    dimensions: Dict[str, float]
    metadata: Dict[str, Any] = {}

class ElementTypesResponse(BaseModel):
    element_types: list

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "deployment": "vercel-simplified",
        "timestamp": time.strftime('%Y-%m-%d %H:%M:%S'),
        "environment": "production"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "CheckMeasureAI API is running",
        "deployment": "vercel-simplified",
        "status": "online",
        "features": {
            "calculations": "available",
            "materials": "available",
            "pdf_processing": "limited",
            "agents": "available"
        }
    }

# Basic calculation endpoint
@app.post("/api/calculations/calculate")
async def calculate(request: CalculationRequest):
    """Simplified calculation endpoint for Vercel compatibility"""
    try:
        # Simple calculation logic for demonstration
        if request.element_code == "J1":
            length = request.dimensions.get("length", 4.0)
            width = request.dimensions.get("width", 0.2)
            
            # Basic joist calculation
            cutting_list = [
                {
                    "element_code": "J1",
                    "member_description": "Joist",
                    "size": "200x45 LVL",
                    "length_m": length,
                    "quantity": 1,
                    "cutting_length_mm": int(length * 1000),
                    "comments": "Standard joist - simplified calculation"
                }
            ]
            
            return {
                "element_code": request.element_code,
                "calculations": {
                    "span_length": length,
                    "joist_size": "200x45 LVL",
                    "spacing": "450mm"
                },
                "cutting_list": cutting_list,
                "formatted_output": f"J1 Joist Calculation\nSpan: {length}m\nSize: 200x45 LVL\nQuantity: 1\n\nCutting List:\n- 1x 200x45 LVL @ {length}m",
                "deployment": "vercel-simplified"
            }
        else:
            return {
                "element_code": request.element_code,
                "message": "Element type not yet supported in simplified mode",
                "deployment": "vercel-simplified"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation failed: {str(e)}")

# Element types endpoint
@app.get("/api/calculations/element-types")
async def get_element_types():
    """Return available element types"""
    return {
        "element_types": [
            {
                "code": "J1",
                "description": "Joist - Floor/Ceiling",
                "category": "structural",
                "calculator_type": "joist",
                "active": True
            },
            {
                "code": "B1", 
                "description": "Bearer - Floor/Ceiling",
                "category": "structural",
                "calculator_type": "bearer",
                "active": True
            }
        ]
    }

# Basic PDF processing endpoint
@app.post("/api/pdf/calculate-dimensions")
async def calculate_dimensions():
    """Simplified PDF processing endpoint"""
    return {
        "width_m": 4.0,
        "height_m": 3.0,
        "scale_used": "1:100 at A3",
        "confidence": 1.0,
        "method": "simplified"
    }

# Basic agents endpoints
@app.get("/api/agents/status")
async def agent_status():
    return {
        "agents": [],
        "system_status": "running",
        "deployment": "vercel-simplified"
    }

@app.get("/api/agents/capabilities")
async def agent_capabilities():
    return {
        "agent_types": ["joist_calculation", "bearer_calculation"],
        "capabilities": ["joist_calculation", "bearer_calculation"],
        "deployment": "vercel-simplified"
    }

# Catch-all for debugging
@app.get("/api/{path:path}")
async def catch_all(path: str):
    return {
        "message": f"Endpoint /{path} not yet implemented in simplified mode",
        "deployment": "vercel-simplified",
        "available_endpoints": [
            "/health",
            "/api/calculations/calculate",
            "/api/calculations/element-types",
            "/api/pdf/calculate-dimensions",
            "/api/agents/status",
            "/api/agents/capabilities"
        ]
    }

# Export for Vercel
handler = app