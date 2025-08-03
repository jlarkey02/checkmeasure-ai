from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from utils.error_logger import error_logger, log_error, log_warning, log_info
import traceback
import logging
import json
import gc  # Garbage collection

# Graceful PyMuPDF import for Vercel compatibility
PYMUPDF_AVAILABLE = False
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
    log_info("PyMuPDF imported successfully", "pdf_processing.imports")
except ImportError:
    log_warning("PyMuPDF not available - PDF processing limited", "pdf_processing.imports")
    fitz = None

# Import dependencies with fallbacks
if PYMUPDF_AVAILABLE:
    try:
        from pdf_processing.pdf_analyzer import PDFAnalyzer
        from pdf_processing.joist_detector import JoistDetector
        from pdf_processing.pdf_scale_calculator import PDFScaleCalculator, COMMON_SCALES
        from utils.dependency_checker import DependencyChecker
    except ImportError as e:
        log_warning(f"PDF processing modules not available: {e}", "pdf_processing.imports")
        PYMUPDF_AVAILABLE = False

# Try to import advanced modules lazily based on environment flag to avoid heavy startup
import os
ENABLE_HEAVY_PDF_IMPORTS = os.getenv("ENABLE_HEAVY_PDF_IMPORTS", "false").lower() == "true"

router = APIRouter()

class PDFAnalysisResult(BaseModel):
    scale: Optional[str] = None
    dimensions: List[dict] = []
    text_blocks: List[dict] = []
    page_info: dict

class SelectionArea(BaseModel):
    x: float
    y: float
    width: float
    height: float
    page_number: int
    calculation_type: str  # "joist", "beam", "wall", "rafter"

class DimensionCalculationRequest(BaseModel):
    """Simple request for dimension calculation without AI"""
    area_coordinates: Dict[str, float]  # x, y, width, height
    page_number: int
    scale_notation: str = "1:100 at A3"

class DimensionCalculationResponse(BaseModel):
    """Simple response with calculated dimensions"""
    width_mm: float
    height_mm: float
    width_m: float
    height_m: float
    area_m2: float
    scale_used: str

def _check_pymupdf_available():
    """Helper to check if PyMuPDF is available and raise appropriate error"""
    if not PYMUPDF_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="PDF processing not available in this deployment. PyMuPDF dependency not installed."
        )

@router.get("/test")
async def test_pdf_processing():
    """Test endpoint for PDF processing"""
    return {
        "message": "PDF processing module is ready",
        "pymupdf_available": PYMUPDF_AVAILABLE,
        "deployment_mode": "vercel_compatible",
        "available_endpoints": [
            "/api/pdf/calculate-dimensions" if PYMUPDF_AVAILABLE else None,
            "/api/pdf/scale-notations"
        ],
        "disabled_endpoints": [
            "/api/pdf/upload",
            "/api/pdf/extract", 
            "/api/pdf/detect-joists",
            "/api/pdf/auto-populate"
        ] if not PYMUPDF_AVAILABLE else []
    }

@router.get("/scale-notations")
async def get_scale_notations():
    """Get list of common scale notations for UI"""
    if PYMUPDF_AVAILABLE:
        return {
            "common_scales": COMMON_SCALES,
            "default": "1:100 at A3"
        }
    else:
        # Fallback scale notations
        return {
            "common_scales": [
                "1:50 at A4", "1:50 at A3", "1:50 at A2", "1:50 at A1", "1:50 at A0",
                "1:100 at A4", "1:100 at A3", "1:100 at A2", "1:100 at A1", "1:100 at A0",
                "1:200 at A4", "1:200 at A3", "1:200 at A2", "1:200 at A1", "1:200 at A0"
            ],
            "default": "1:100 at A3"
        }

@router.post("/calculate-dimensions", response_model=DimensionCalculationResponse)
async def calculate_dimensions(
    file: UploadFile = File(...),
    request: str = Form(...)
) -> DimensionCalculationResponse:
    """Calculate real-world dimensions from PDF coordinates - no AI needed"""
    
    _check_pymupdf_available()
    
    # Add comprehensive logging
    print("\n" + "="*60)
    print("[CALCULATE-DIMENSIONS] Endpoint called")
    print(f"[CALCULATE-DIMENSIONS] File: {file.filename if file else 'None'}")
    print(f"[CALCULATE-DIMENSIONS] Request string length: {len(request) if request else 0}")
    
    try:
        print(f"[CALCULATE-DIMENSIONS] Raw request: {request[:200]}..." if len(request) > 200 else f"[CALCULATE-DIMENSIONS] Raw request: {request}")
    except Exception as e:
        print(f"[CALCULATE-DIMENSIONS] Error printing request: {e}")
    
    if not file or not file.filename.endswith('.pdf'):
        print("[CALCULATE-DIMENSIONS] Invalid file - not a PDF")
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    pdf_doc = None
    try:
        # Parse request
        print("[CALCULATE-DIMENSIONS] Parsing JSON request...")
        request_data = json.loads(request)
        print(f"[CALCULATE-DIMENSIONS] Request data keys: {list(request_data.keys())}")
        
        area = request_data.get("area_coordinates", {})
        scale_notation = request_data.get("scale_notation", "1:100 at A3")
        
        print(f"[CALCULATE-DIMENSIONS] Area coordinates: {area}")
        print(f"[CALCULATE-DIMENSIONS] Scale notation: {scale_notation}")
        
        # Read PDF to get page dimensions
        print("[CALCULATE-DIMENSIONS] Reading PDF content...")
        content = await file.read()
        print(f"[CALCULATE-DIMENSIONS] PDF size: {len(content)} bytes")
        
        print("[CALCULATE-DIMENSIONS] Opening PDF with fitz...")
        pdf_doc = fitz.open(stream=content, filetype="pdf")
        print(f"[CALCULATE-DIMENSIONS] PDF opened successfully, pages: {len(pdf_doc)}")
        
        # Get page dimensions
        page_index = request_data.get("page_number", 1) - 1  # Convert to 0-based
        print(f"[CALCULATE-DIMENSIONS] Requested page: {page_index + 1} (0-based: {page_index})")
        
        if page_index < 0 or page_index >= len(pdf_doc):
            print(f"[CALCULATE-DIMENSIONS] Invalid page number: {page_index + 1}")
            raise HTTPException(status_code=400, detail="Invalid page number")
            
        page = pdf_doc[page_index]
        pdf_width_mm = page.rect.width * 0.3528
        pdf_height_mm = page.rect.height * 0.3528
        print(f"[CALCULATE-DIMENSIONS] Page dimensions: {pdf_width_mm:.2f}mm x {pdf_height_mm:.2f}mm")
        
        # Initialize scale calculator
        print(f"[CALCULATE-DIMENSIONS] Creating PDFScaleCalculator with notation: {scale_notation}")
        scale_calc = PDFScaleCalculator(scale_notation)
        
        # Calculate dimensions
        x1 = area.get("x", 0)
        y1 = area.get("y", 0)
        x2 = area.get("x", 0) + area.get("width", 0)
        y2 = area.get("y", 0) + area.get("height", 0)
        
        print(f"[CALCULATE-DIMENSIONS] Measuring area: ({x1}, {y1}) to ({x2}, {y2})")
        measurements = scale_calc.measure_area(x1, y1, x2, y2, pdf_width_mm, pdf_height_mm)
        print(f"[CALCULATE-DIMENSIONS] Measurements calculated: {measurements}")
        
        result = DimensionCalculationResponse(
            width_mm=measurements['width_mm'],
            height_mm=measurements['height_mm'],
            width_m=measurements['width_m'],
            height_m=measurements['height_m'],
            area_m2=measurements['area_m2'],
            scale_used=measurements['scale_used']
        )
        
        print(f"[CALCULATE-DIMENSIONS] Returning successful response")
        print("="*60)
        return result
        
    except json.JSONDecodeError as e:
        print(f"[CALCULATE-DIMENSIONS] JSON decode error: {e}")
        print("="*60)
        raise HTTPException(status_code=400, detail="Invalid JSON in request")
    except HTTPException as e:
        print(f"[CALCULATE-DIMENSIONS] HTTP exception: {e.detail}")
        print("="*60)
        raise
    except Exception as e:
        print(f"[CALCULATE-DIMENSIONS] Unexpected error: {type(e).__name__}: {str(e)}")
        print(f"[CALCULATE-DIMENSIONS] Traceback:")
        traceback.print_exc()
        print("="*60)
        log_error(e, "pdf_processing.calculate_dimensions")
        raise HTTPException(status_code=500, detail=f"Dimension calculation failed: {str(e)}")
    finally:
        print("[CALCULATE-DIMENSIONS] Cleanup phase...")
        if pdf_doc:
            try:
                pdf_doc.close()
                print("[CALCULATE-DIMENSIONS] PDF document closed")
            except Exception as e:
                print(f"[CALCULATE-DIMENSIONS] Error closing PDF: {e}")
        # Force garbage collection to free memory
        try:
            gc.collect()
            print("[CALCULATE-DIMENSIONS] Garbage collection completed")
        except Exception as e:
            print(f"[CALCULATE-DIMENSIONS] Error during GC: {e}")
        print("="*60 + "\n")

# Disabled endpoints for Vercel deployment
@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """DISABLED - Upload and analyze a PDF drawing"""
    raise HTTPException(
        status_code=503, 
        detail="PDF upload disabled in Vercel deployment. Use /calculate-dimensions for basic functionality."
    )

@router.post("/extract")
async def extract_measurements(
    file: UploadFile = File(...),
    selection_areas: List[SelectionArea] = []
):
    """DISABLED - Extract measurements from selected areas of the PDF"""
    raise HTTPException(
        status_code=503, 
        detail="PDF extraction disabled in Vercel deployment. Use /calculate-dimensions for basic functionality."
    )

@router.post("/detect-joists")
async def detect_joists(file: UploadFile = File(...)):
    """DISABLED - Detect joist labels and specifications in PDF"""
    raise HTTPException(
        status_code=503, 
        detail="Joist detection disabled in Vercel deployment. Use manual calculation with /api/calculations/calculate."
    )

@router.post("/auto-populate")
async def auto_populate_form(file: UploadFile = File(...)):
    """DISABLED - Auto-populate calculation form based on detected joist labels"""
    raise HTTPException(
        status_code=503, 
        detail="Auto-populate disabled in Vercel deployment. Please use manual form input."
    )