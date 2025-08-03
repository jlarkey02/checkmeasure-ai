from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pdf_processing.pdf_analyzer import PDFAnalyzer
from pdf_processing.joist_detector import JoistDetector
from pdf_processing.pdf_scale_calculator import PDFScaleCalculator, COMMON_SCALES
from utils.dependency_checker import DependencyChecker
from utils.error_logger import error_logger, log_error, log_warning, log_info
import traceback
import logging
import json
import gc  # Garbage collection
import fitz  # PyMuPDF

# Try to import advanced modules lazily based on environment flag to avoid heavy startup
import os
ENABLE_HEAVY_PDF_IMPORTS = os.getenv("ENABLE_HEAVY_PDF_IMPORTS", "false").lower() == "true"

ADVANCED_PDF_AVAILABLE = False
ADVANCED_JOIST_AVAILABLE = False
CLAUDE_VISION_AVAILABLE = False
HYBRID_ANALYZER_AVAILABLE = False

if ENABLE_HEAVY_PDF_IMPORTS:
    try:
        from pdf_processing.advanced_pdf_analyzer import AdvancedPDFAnalyzer
        ADVANCED_PDF_AVAILABLE = True
        log_info("Advanced PDF analyzer imported successfully", "pdf_processing.imports")
    except Exception as e:
        log_error(e, "pdf_processing.imports", additional_info={"module": "advanced_pdf_analyzer"})

    try:
        from pdf_processing.advanced_joist_detector import AdvancedJoistDetector
        ADVANCED_JOIST_AVAILABLE = True
        log_info("Advanced joist detector imported successfully", "pdf_processing.imports")
    except Exception as e:
        log_error(e, "pdf_processing.imports", additional_info={"module": "advanced_joist_detector"})

    try:
        from pdf_processing.claude_vision_analyzer import ClaudeVisionAnalyzer
        CLAUDE_VISION_AVAILABLE = True
        log_info("Claude Vision analyzer imported successfully", "pdf_processing.imports")
    except Exception as e:
        log_error(e, "pdf_processing.imports", additional_info={"module": "claude_vision_analyzer"})

    try:
        from pdf_processing.hybrid_analyzer import HybridPDFAnalyzer
        HYBRID_ANALYZER_AVAILABLE = True
        log_info("Hybrid PDF analyzer imported successfully", "pdf_processing.imports")
    except Exception as e:
        log_error(e, "pdf_processing.imports", additional_info={"module": "hybrid_analyzer"})

# If heavy imports are disabled, advanced features remain unavailable and their endpoints will return 503 as intended.

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

class ExtractionResult(BaseModel):
    measurements: List[dict]
    extracted_text: str
    confidence: float

class JoistDetectionResult(BaseModel):
    detected_joists: int
    joist_labels: List[dict]
    auto_population_data: Optional[dict] = None

class JoistMeasurementRequest(BaseModel):
    joist_label: str

class AdvancedAnalysisResult(BaseModel):
    page_count: int
    extraction_methods: List[str]
    overall_confidence: float
    text_extraction_count: int
    line_detection_count: int
    joist_detection_count: int
    processing_log: List[str]

class ClaudeVisionResult(BaseModel):
    detected_joists: int
    claude_reasoning: str
    overall_confidence: float
    processing_time_ms: float
    cost_estimate_usd: Optional[float]
    form_data: dict
    joist_details: List[dict]

class AreaAnalysisRequest(BaseModel):
    selection_areas: List[SelectionArea]

class AreaAnalysisResult(BaseModel):
    successful_areas: int
    total_areas: int
    detected_elements: List[dict]
    overall_confidence: float
    combined_reasoning: str
    processing_time_ms: float
    total_cost_estimate_usd: Optional[float]
    form_data: dict
    scale_notation: str
    measurements: Optional[dict] = None

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and analyze a PDF drawing"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        analyzer = PDFAnalyzer()
        
        # Save uploaded file temporarily
        content = await file.read()
        
        # Analyze PDF
        analysis_result = analyzer.analyze_pdf(content)
        
        return PDFAnalysisResult(
            scale=analysis_result.get("scale"),
            dimensions=analysis_result.get("dimensions", []),
            text_blocks=analysis_result.get("text_blocks", []),
            page_info=analysis_result.get("page_info", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing PDF: {str(e)}")

@router.post("/extract")
async def extract_measurements(
    file: UploadFile = File(...),
    selection_areas: List[SelectionArea] = []
):
    """Extract measurements from selected areas of the PDF"""
    try:
        analyzer = PDFAnalyzer()
        
        # Save uploaded file temporarily
        content = await file.read()
        
        # Extract measurements from selected areas
        results = []
        for area in selection_areas:
            extraction_result = analyzer.extract_from_area(content, area)
            results.append(extraction_result)
        
        return {"extractions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting measurements: {str(e)}")

@router.post("/detect-joists")
async def detect_joists(file: UploadFile = File(...)):
    """Detect joist labels and specifications in PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        detector = JoistDetector()
        content = await file.read()
        
        # Detect joist labels
        joist_labels = detector.detect_joist_labels(content)
        
        # Convert to serializable format
        labels_data = []
        for joist in joist_labels:
            labels_data.append({
                'label': joist.label,
                'specification': joist.specification,
                'dimensions': joist.dimensions,
                'bbox': joist.bbox,
                'page_number': joist.page_number,
                'confidence': joist.confidence
            })
        
        return JoistDetectionResult(
            detected_joists=len(joist_labels),
            joist_labels=labels_data
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting joists: {str(e)}")

@router.post("/auto-populate")
async def auto_populate_form(file: UploadFile = File(...)):
    """Auto-populate calculation form based on detected joist labels"""
    global _last_detection_details
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        import datetime
        detector = JoistDetector()
        content = await file.read()
        
        # Get all detected joists for debugging
        all_joists = detector.detect_joist_labels(content)
        
        # Auto-populate form data
        form_data = detector.auto_populate_calculation_form(content)
        
        # Store detailed debug information
        _last_detection_details = {
            "timestamp": datetime.datetime.now().isoformat(),
            "method_used": "basic_text_extraction",
            "pdf_filename": file.filename,
            "pdf_size_bytes": len(content),
            "total_joists_found": len(all_joists),
            "joist_details": [
                {
                    "label": joist.label,
                    "specification": joist.specification,
                    "page_number": joist.page_number,
                    "confidence": joist.confidence,
                    "dimensions": joist.dimensions,
                    "bbox_location": joist.bbox
                }
                for joist in all_joists
            ],
            "form_data_generated": form_data,
            "detection_methods_tried": ["basic_text_extraction"],
            "fallback_chain": ["claude_vision_failed", "advanced_ocr_failed", "basic_extraction_succeeded"]
        }
        
        return {"form_data": form_data}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error auto-populating form: {str(e)}")

@router.post("/extract-joist-measurements")
async def extract_joist_measurements(
    request: JoistMeasurementRequest,
    file: UploadFile = File(...)
):
    """Extract measurements for a specific joist label"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        detector = JoistDetector()
        content = await file.read()
        
        # Extract measurements for specific joist
        measurements = detector.extract_joist_measurements(content, request.joist_label)
        
        if not measurements:
            raise HTTPException(
                status_code=404, 
                detail=f"Joist label '{request.joist_label}' not found in PDF"
            )
        
        return measurements
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting joist measurements: {str(e)}")

@router.post("/debug-text-extraction")
async def debug_text_extraction(file: UploadFile = File(...)):
    """Debug endpoint to see all extracted text from PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        analyzer = PDFAnalyzer()
        content = await file.read()
        
        # Get detailed analysis
        analysis = analyzer.analyze_pdf(content)
        
        # Extract all text for debugging
        all_text = []
        for text_block in analysis['text_blocks']:
            all_text.append({
                'text': text_block.text,
                'page': text_block.page_number,
                'font_size': text_block.font_size,
                'bbox': text_block.bbox
            })
        
        return {
            "total_text_blocks": len(all_text),
            "text_blocks": all_text,
            "page_count": analysis.get('page_count', 0),
            "scale": analysis.get('scale'),
            "dimensions_found": len(analysis.get('dimensions', []))
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")

@router.post("/debug-joist-detection")
async def debug_joist_detection(file: UploadFile = File(...)):
    """Debug endpoint to show step-by-step joist detection process"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # First test basic PDF analysis
        analyzer = PDFAnalyzer()
        content = await file.read()
        
        # Basic PDF analysis
        analysis = analyzer.analyze_pdf(content)
        text_blocks = analysis.get('text_blocks', [])
        
        debug_info = {
            "step_1_text_extraction": {
                "total_blocks": len(text_blocks),
                "sample_text": [getattr(block, 'text', str(block)) for block in text_blocks[:10]],
                "analysis_keys": list(analysis.keys())
            },
            "step_2_label_search": [],
            "step_3_specification_search": [],
            "step_4_detected_joists": [],
            "errors": []
        }
        
        # Test joist detection if we have text blocks
        if text_blocks:
            try:
                detector = JoistDetector()
                
                # Test pattern matching on each text block
                for i, text_block in enumerate(text_blocks):
                    text_content = getattr(text_block, 'text', str(text_block))
                    
                    # Test joist label patterns manually
                    for pattern in detector.joist_label_patterns:
                        import re
                        matches = re.findall(pattern, text_content, re.IGNORECASE)
                        if matches:
                            debug_info["step_2_label_search"].append({
                                "block_index": i,
                                "text": text_content,
                                "pattern": pattern,
                                "matches": matches,
                                "page": getattr(text_block, 'page_number', 0)
                            })
                
                # Try full detection
                joist_labels = detector.detect_joist_labels(content)
                for joist in joist_labels:
                    debug_info["step_4_detected_joists"].append({
                        "label": joist.label,
                        "specification": joist.specification,
                        "dimensions": joist.dimensions,
                        "confidence": joist.confidence
                    })
                    
            except Exception as detector_error:
                debug_info["errors"].append(f"Detector error: {str(detector_error)}")
        else:
            debug_info["errors"].append("No text blocks extracted from PDF")
        
        return debug_info
    
    except Exception as e:
        return {
            "error": f"Critical error: {str(e)}",
            "step_1_text_extraction": {"total_blocks": 0, "sample_text": [], "analysis_keys": []},
            "step_2_label_search": [],
            "step_3_specification_search": [],
            "step_4_detected_joists": [],
            "errors": [str(e)]
        }

@router.post("/analyze-advanced")
async def analyze_pdf_advanced(file: UploadFile = File(...)):
    """DISABLED - Advanced PDF analysis using OCR, computer vision, and multi-method extraction
    
    This endpoint has been disabled because:
    1. Computer vision libraries (EasyOCR, OpenCV) were causing process death
    2. Current workflow doesn't use AI analysis - users manually select areas
    3. Simple math-based approach is more reliable and faster
    """
    raise HTTPException(
        status_code=501, 
        detail="Advanced CV analysis disabled - use /calculate-dimensions for math-based measurement"
    )
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        analyzer = AdvancedPDFAnalyzer()
        content = await file.read()
        
        # Perform advanced analysis
        analysis_result = analyzer.analyze_pdf_advanced(content)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=500, detail=analysis_result["error"])
        
        # Find structural elements
        structural_elements = analyzer.find_joist_elements(analysis_result)
        
        return AdvancedAnalysisResult(
            page_count=analysis_result.get("page_count", 0),
            extraction_methods=analysis_result.get("extraction_methods", []),
            overall_confidence=analysis_result.get("overall_confidence", 0.0),
            text_extraction_count=len(analysis_result.get("extracted_text", [])),
            line_detection_count=len(analysis_result.get("detected_lines", [])),
            joist_detection_count=len(structural_elements),
            processing_log=analysis_result.get("processing_log", [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced analysis failed: {str(e)}")

@router.post("/detect-joists-advanced")
async def detect_joists_advanced(file: UploadFile = File(...)):
    """DISABLED - Advanced joist detection using multiple methods (OCR, CV, pattern matching)
    
    This endpoint has been disabled because computer vision libraries were causing process death.
    Use manual area selection with /calculate-dimensions instead.
    """
    raise HTTPException(
        status_code=501, 
        detail="Advanced joist detection disabled - use manual area selection"
    )
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        detector = AdvancedJoistDetector()
        content = await file.read()
        
        # Detect joists using advanced methods
        joist_labels = detector.detect_joists_advanced(content)
        
        # Convert to serializable format
        labels_data = []
        for joist in joist_labels:
            labels_data.append({
                'label': joist.label,
                'specification': joist.specification,
                'dimensions': joist.dimensions,
                'bbox': joist.bbox,
                'page_number': joist.page_number,
                'confidence': joist.confidence,
                'detection_methods': joist.detection_methods,
                'spatial_elements': {
                    k: v for k, v in joist.spatial_elements.items() 
                    if not isinstance(v, (list, dict)) or len(str(v)) < 1000  # Limit large objects
                }
            })
        
        return {
            "detected_joists": len(joist_labels),
            "joist_labels": labels_data,
            "analysis_summary": {
                "total_detections": len(joist_labels),
                "high_confidence_detections": len([j for j in joist_labels if j.confidence > 0.7]),
                "detection_methods_used": list(set(sum([j.detection_methods for j in joist_labels], []))),
                "average_confidence": sum([j.confidence for j in joist_labels]) / len(joist_labels) if joist_labels else 0.0
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advanced joist detection failed: {str(e)}")

@router.post("/auto-populate-advanced")
async def auto_populate_form_advanced(file: UploadFile = File(...)):
    """DISABLED - Auto-populate calculation form using advanced detection methods
    
    This endpoint has been disabled because it relies on computer vision libraries
    that were causing memory pressure and process death. Use manual input instead.
    """
    raise HTTPException(
        status_code=501, 
        detail="Auto-populate disabled - use manual form input"
    )
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    debug_log = []
    
    try:
        log_info("Starting advanced auto-population", "pdf_processing.auto_populate_advanced")
        debug_log.append("Starting advanced auto-population")
        
        content = await file.read()
        debug_log.append(f"PDF file read successfully, size: {len(content)} bytes")
        
        # Check if advanced modules are available
        if not ADVANCED_JOIST_AVAILABLE:
            log_warning("Advanced joist detector not available, falling back to basic", 
                       "pdf_processing.auto_populate_advanced")
            debug_log.append("Advanced joist detector not available - falling back to basic")
            
            # Fall back to basic auto-populate
            try:
                detector = JoistDetector()
                form_data = detector.auto_populate_calculation_form(content)
                form_data['debug_log'] = debug_log
                form_data['fallback_used'] = True
                return {"form_data": form_data}
            except Exception as fallback_error:
                error_id = log_error(fallback_error, "pdf_processing.auto_populate_advanced.fallback")
                return {
                    'form_data': {
                        'error': f'Both advanced and basic auto-population failed: {str(fallback_error)}',
                        'debug_log': debug_log,
                        'error_id': error_id
                    }
                }
        
        try:
            detector = AdvancedJoistDetector()
            debug_log.append("Advanced joist detector initialized successfully")
            
            # Detect joists using advanced methods
            joist_labels = detector.detect_joists_advanced(content)
            debug_log.append(f"Advanced joist detection completed, found {len(joist_labels)} joists")
            
            if not joist_labels:
                debug_log.append("No joists found with advanced detection - trying basic fallback")
                
                # Fall back to basic detection
                try:
                    basic_detector = JoistDetector()
                    basic_form_data = basic_detector.auto_populate_calculation_form(content)
                    basic_form_data['debug_log'] = debug_log
                    basic_form_data['fallback_used'] = True
                    return {"form_data": basic_form_data}
                except Exception as basic_error:
                    error_id = log_error(basic_error, "pdf_processing.auto_populate_advanced.basic_fallback")
                    return {
                        'form_data': {
                            'error': 'No joist labels detected using any method',
                            'debug_log': debug_log,
                            'basic_error': str(basic_error),
                            'error_id': error_id
                        }
                    }
            
            # Find the best joist for auto-population (highest confidence)
            best_joist = max(joist_labels, key=lambda x: x.confidence)
            debug_log.append(f"Best joist selected: {best_joist.label} (confidence: {best_joist.confidence:.2f})")
            
            # Build enhanced form data
            form_data = {
                'detected_joists': len(joist_labels),
                'primary_joist_label': best_joist.label,
                'auto_populated': True,
                'detection_methods': best_joist.detection_methods,
                'confidence': best_joist.confidence,
                'debug_log': debug_log
            }
            
            # Add specification data if available
            if best_joist.dimensions:
                debug_log.append(f"Processing dimensions: {list(best_joist.dimensions.keys())}")
                
                if 'spacing_mm' in best_joist.dimensions and best_joist.dimensions['spacing_mm'] is not None:
                    form_data['joist_spacing'] = best_joist.dimensions['spacing_mm'] / 1000  # Convert to meters
                    debug_log.append(f"Joist spacing detected: {form_data['joist_spacing']}m")
                
                if 'width_mm' in best_joist.dimensions and 'depth_mm' in best_joist.dimensions:
                    form_data['material_detected'] = f"{best_joist.dimensions['width_mm']}x{best_joist.dimensions['depth_mm']}"
                    if 'material_type' in best_joist.dimensions:
                        form_data['material_detected'] += f" {best_joist.dimensions['material_type']}"
                    debug_log.append(f"Material detected: {form_data['material_detected']}")
                
                if 'material_description' in best_joist.dimensions:
                    form_data['material_specification'] = best_joist.dimensions['material_description']
            
            # Try to extract span length from spatial elements
            if 'nearby_measurements' in best_joist.spatial_elements:
                measurements = best_joist.spatial_elements['nearby_measurements']
                debug_log.append(f"Analyzing {len(measurements)} nearby measurements for span length")
                
                # Look for reasonable span lengths (1-10 meters)
                for measurement in measurements:
                    # Parse measurement text for dimensions
                    import re
                    dimension_matches = re.findall(r'(\d+\.?\d*)\s*(m|mm|cm)', measurement.get('text', ''), re.IGNORECASE)
                    for value, unit in dimension_matches:
                        value_meters = float(value)
                        if unit.lower() == 'mm':
                            value_meters /= 1000
                        elif unit.lower() == 'cm':
                            value_meters /= 100
                        
                        if 1.0 <= value_meters <= 10.0:  # Reasonable span length
                            form_data['span_length'] = value_meters
                            debug_log.append(f"Span length detected: {value_meters}m")
                            break
                    if 'span_length' in form_data:
                        break
            
            # Add all detected joists for reference
            form_data['all_detected_joists'] = [
                {
                    'label': j.label,
                    'specification': j.specification,
                    'confidence': j.confidence,
                    'methods': j.detection_methods
                } for j in joist_labels
            ]
            
            # Add analysis metadata
            form_data['analysis_metadata'] = {
                'total_detection_methods': len(set(sum([j.detection_methods for j in joist_labels], []))),
                'best_confidence': best_joist.confidence,
                'specification_completeness': len(best_joist.dimensions) / 5.0  # Max 5 possible dimensions
            }
            
            log_info(f"Advanced auto-population successful: {len(joist_labels)} joists detected", 
                    "pdf_processing.auto_populate_advanced")
            
            return {"form_data": form_data}
        
        except Exception as e:
            error_id = log_error(e, "pdf_processing.auto_populate_advanced.advanced_detection",
                               {"file_size": len(content)})
            debug_log.append(f"ERROR in advanced detection: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            
            # Try basic fallback
            try:
                log_info("Attempting basic fallback after advanced failure", 
                        "pdf_processing.auto_populate_advanced.fallback")
                basic_detector = JoistDetector()
                basic_form_data = basic_detector.auto_populate_calculation_form(content)
                basic_form_data['debug_log'] = debug_log
                basic_form_data['fallback_used'] = True
                basic_form_data['advanced_error'] = str(e)
                basic_form_data['error_id'] = error_id
                return {"form_data": basic_form_data}
            except Exception as fallback_error:
                fallback_error_id = log_error(fallback_error, "pdf_processing.auto_populate_advanced.fallback_error")
                return {
                    'form_data': {
                        'error': f'Both advanced and basic detection failed',
                        'advanced_error': str(e),
                        'basic_error': str(fallback_error),
                        'debug_log': debug_log,
                        'error_id': error_id,
                        'fallback_error_id': fallback_error_id
                    }
                }
    
    except Exception as e:
        error_id = log_error(e, "pdf_processing.auto_populate_advanced.critical")
        debug_log.append(f"CRITICAL ERROR: {str(e)}")
        debug_log.append(f"Error ID: {error_id}")
        
        return {
            'form_data': {
                'error': f'Critical error in auto-population: {str(e)}',
                'debug_log': debug_log,
                'error_id': error_id,
                'traceback': traceback.format_exc()
            }
        }

@router.get("/debug/dependencies")
async def check_dependencies():
    """Check all system dependencies and return detailed status"""
    try:
        log_info("Starting dependency check", "pdf_processing.debug")
        checker = DependencyChecker()
        result = checker.check_all_dependencies()
        
        # Add module availability status
        result['module_availability'] = {
            'advanced_pdf_analyzer': ADVANCED_PDF_AVAILABLE,
            'advanced_joist_detector': ADVANCED_JOIST_AVAILABLE
        }
        
        log_info(f"Dependency check completed. All OK: {result['all_dependencies_ok']}", 
                "pdf_processing.debug")
        
        return result
    except Exception as e:
        error_id = log_error(e, "pdf_processing.debug.dependencies")
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "error_id": error_id,
            "traceback": traceback.format_exc()
        })

@router.get("/debug/errors")
async def get_error_log():
    """Get recent error log for debugging"""
    try:
        return {
            "error_summary": error_logger.get_error_summary(),
            "recent_errors": error_logger.get_recent_errors(20),
            "module_status": {
                "advanced_pdf_available": ADVANCED_PDF_AVAILABLE,
                "advanced_joist_available": ADVANCED_JOIST_AVAILABLE
            }
        }
    except Exception as e:
        error_id = log_error(e, "pdf_processing.debug.errors")
        return {
            "error": str(e),
            "error_id": error_id
        }

@router.post("/debug/test-advanced")
async def test_advanced_processing(file: UploadFile = File(...)):
    """Test advanced processing step by step for debugging"""
    debug_log = []
    
    try:
        log_info("Starting advanced processing test", "pdf_processing.debug.test")
        debug_log.append("Starting advanced processing test")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        content = await file.read()
        debug_log.append(f"PDF file read successfully, size: {len(content)} bytes")
        
        # Test 1: Check if advanced modules are available
        debug_log.append(f"Advanced PDF analyzer available: {ADVANCED_PDF_AVAILABLE}")
        debug_log.append(f"Advanced joist detector available: {ADVANCED_JOIST_AVAILABLE}")
        
        if not ADVANCED_PDF_AVAILABLE:
            debug_log.append("ERROR: Advanced PDF analyzer not available - falling back to basic")
            return {
                "success": False,
                "error": "Advanced PDF analyzer not available",
                "debug_log": debug_log,
                "fallback": "Use basic PDF processing"
            }
        
        # Test 2: Try to initialize advanced analyzer
        try:
            analyzer = AdvancedPDFAnalyzer()
            debug_log.append("Advanced PDF analyzer initialized successfully")
        except Exception as e:
            error_id = log_error(e, "pdf_processing.debug.test.analyzer_init")
            debug_log.append(f"ERROR initializing advanced analyzer: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            return {
                "success": False,
                "error": str(e),
                "error_id": error_id,
                "debug_log": debug_log
            }
        
        # Test 3: Try basic PDF analysis
        try:
            analysis_result = analyzer.analyze_pdf_advanced(content)
            debug_log.append("PDF analysis completed")
            
            if "error" in analysis_result:
                debug_log.append(f"PDF analysis returned error: {analysis_result['error']}")
                return {
                    "success": False,
                    "error": analysis_result["error"],
                    "debug_log": debug_log
                }
            
            debug_log.append(f"Text extraction count: {len(analysis_result.get('extracted_text', []))}")
            debug_log.append(f"Line detection count: {len(analysis_result.get('detected_lines', []))}")
            debug_log.append(f"Overall confidence: {analysis_result.get('overall_confidence', 0)}")
            
        except Exception as e:
            error_id = log_error(e, "pdf_processing.debug.test.analysis", 
                               {"file_size": len(content)})
            debug_log.append(f"ERROR during PDF analysis: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            return {
                "success": False,
                "error": str(e),
                "error_id": error_id,
                "debug_log": debug_log,
                "traceback": traceback.format_exc()
            }
        
        # Test 4: Try joist detection
        if not ADVANCED_JOIST_AVAILABLE:
            debug_log.append("WARNING: Advanced joist detector not available")
            return {
                "success": True,
                "warning": "Joist detector not available",
                "debug_log": debug_log,
                "analysis_result": {
                    "text_count": len(analysis_result.get('extracted_text', [])),
                    "line_count": len(analysis_result.get('detected_lines', [])),
                    "confidence": analysis_result.get('overall_confidence', 0)
                }
            }
        
        try:
            detector = AdvancedJoistDetector()
            debug_log.append("Advanced joist detector initialized successfully")
            
            joist_labels = detector.detect_joists_advanced(content)
            debug_log.append(f"Joist detection completed, found {len(joist_labels)} joists")
            
            return {
                "success": True,
                "debug_log": debug_log,
                "analysis_result": {
                    "text_count": len(analysis_result.get('extracted_text', [])),
                    "line_count": len(analysis_result.get('detected_lines', [])),
                    "confidence": analysis_result.get('overall_confidence', 0),
                    "joist_count": len(joist_labels)
                }
            }
            
        except Exception as e:
            error_id = log_error(e, "pdf_processing.debug.test.joist_detection")
            debug_log.append(f"ERROR during joist detection: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            return {
                "success": False,
                "error": str(e),
                "error_id": error_id,
                "debug_log": debug_log,
                "traceback": traceback.format_exc()
            }
        
    except Exception as e:
        error_id = log_error(e, "pdf_processing.debug.test.general")
        debug_log.append(f"CRITICAL ERROR: {str(e)}")
        debug_log.append(f"Error ID: {error_id}")
        return {
            "success": False,
            "error": str(e),
            "error_id": error_id,
            "debug_log": debug_log,
            "traceback": traceback.format_exc()
        }

@router.post("/debug/basic-test")
async def test_basic_processing(file: UploadFile = File(...)):
    """Test basic processing to ensure fallback works"""
    debug_log = []
    
    try:
        debug_log.append("Starting basic processing test")
        
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="File must be a PDF")
        
        content = await file.read()
        debug_log.append(f"PDF file read successfully, size: {len(content)} bytes")
        
        # Test basic analyzer
        try:
            analyzer = PDFAnalyzer()
            debug_log.append("Basic PDF analyzer initialized")
            
            analysis_result = analyzer.analyze_pdf(content)
            debug_log.append("Basic PDF analysis completed")
            debug_log.append(f"Text blocks found: {len(analysis_result.get('text_blocks', []))}")
            debug_log.append(f"Dimensions found: {len(analysis_result.get('dimensions', []))}")
            
        except Exception as e:
            error_id = log_error(e, "pdf_processing.debug.basic.analysis")
            debug_log.append(f"ERROR in basic analysis: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            return {
                "success": False,
                "error": str(e),
                "error_id": error_id,
                "debug_log": debug_log
            }
        
        # Test basic joist detector
        try:
            detector = JoistDetector()
            debug_log.append("Basic joist detector initialized")
            
            joist_labels = detector.detect_joist_labels(content)
            debug_log.append(f"Basic joist detection completed, found {len(joist_labels)} joists")
            
            return {
                "success": True,
                "debug_log": debug_log,
                "analysis_result": {
                    "text_blocks": len(analysis_result.get('text_blocks', [])),
                    "dimensions": len(analysis_result.get('dimensions', [])),
                    "joists": len(joist_labels)
                }
            }
            
        except Exception as e:
            error_id = log_error(e, "pdf_processing.debug.basic.joist_detection")
            debug_log.append(f"ERROR in basic joist detection: {str(e)}")
            debug_log.append(f"Error ID: {error_id}")
            return {
                "success": False,
                "error": str(e),
                "error_id": error_id,
                "debug_log": debug_log
            }
        
    except Exception as e:
        error_id = log_error(e, "pdf_processing.debug.basic.general")
        debug_log.append(f"CRITICAL ERROR: {str(e)}")
        debug_log.append(f"Error ID: {error_id}")
        return {
            "success": False,
            "error": str(e),
            "error_id": error_id,
            "debug_log": debug_log,
            "traceback": traceback.format_exc()
        }

@router.post("/analyze-claude-vision")
async def analyze_pdf_with_claude_vision(file: UploadFile = File(...)):
    """Analyze PDF using Claude Vision API for joist detection"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Check if Claude Vision is available
        if not CLAUDE_VISION_AVAILABLE:
            raise HTTPException(
                status_code=503, 
                detail="Claude Vision analyzer not available. Check API key configuration."
            )
        
        log_info("Starting Claude Vision analysis", "pdf_processing.claude_vision")
        
        # Read PDF content
        content = await file.read()
        
        # Initialize Claude Vision analyzer
        analyzer = ClaudeVisionAnalyzer()
        
        # Analyze with Claude Vision
        result = analyzer.analyze_pdf_with_claude(content)
        
        # Convert to API response format
        response = ClaudeVisionResult(
            detected_joists=len(result.detected_joists),
            claude_reasoning=result.claude_reasoning,
            overall_confidence=result.overall_confidence,
            processing_time_ms=result.processing_time_ms,
            cost_estimate_usd=result.cost_estimate_usd,
            form_data=analyzer.create_form_data_from_result(result),
            joist_details=[
                {
                    "label": joist.label,
                    "specification": joist.specification,
                    "location": joist.location,
                    "confidence": joist.confidence,
                    "reasoning": joist.reasoning,
                    "measurements": joist.measurements
                }
                for joist in result.detected_joists
            ]
        )
        
        log_info(f"Claude Vision analysis completed successfully: {len(result.detected_joists)} joists found", 
                "pdf_processing.claude_vision")
        
        return response
        
    except Exception as e:
        error_id = log_error(e, "pdf_processing.claude_vision.analyze", additional_info={
            "file_size": len(content) if 'content' in locals() else 0
        })
        
        # Check for specific API key errors
        if "api_key" in str(e).lower() or "anthropic" in str(e).lower():
            raise HTTPException(
                status_code=401, 
                detail=f"Claude Vision API authentication failed. Please check ANTHROPIC_API_KEY environment variable. Error ID: {error_id}"
            )
        
        raise HTTPException(
            status_code=500, 
            detail=f"Claude Vision analysis failed: {str(e)}. Error ID: {error_id}"
        )

@router.post("/auto-populate-claude-vision")
async def auto_populate_form_with_claude_vision(file: UploadFile = File(...)):
    """Auto-populate calculation form using Claude Vision with enhanced fallback"""
    global _last_detection_details
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    debug_log = []
    
    try:
        log_info("Starting Claude Vision auto-population", "pdf_processing.claude_auto_populate")
        debug_log.append("Starting Claude Vision auto-population")
        
        content = await file.read()
        debug_log.append(f"PDF file read successfully, size: {len(content)} bytes")
        
        # Try Claude Vision first (if available and configured)
        if CLAUDE_VISION_AVAILABLE:
            try:
                debug_log.append("Attempting Claude Vision analysis")
                analyzer = ClaudeVisionAnalyzer()
                result = analyzer.analyze_pdf_with_claude(content)
                form_data = analyzer.create_form_data_from_result(result)
                
                # Store detailed debug information
                import datetime
                _last_detection_details = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "method_used": "claude_vision",
                    "pdf_filename": file.filename,
                    "pdf_size_bytes": len(content),
                    "total_joists_found": len(result.detected_joists),
                    "claude_reasoning": result.claude_reasoning,
                    "overall_confidence": result.overall_confidence,
                    "processing_time_ms": result.processing_time_ms,
                    "cost_estimate_usd": result.cost_estimate_usd,
                    "joist_details": [
                        {
                            "label": joist.label,
                            "specification": joist.specification,
                            "confidence": joist.confidence,
                            "reasoning": joist.reasoning,
                            "measurements": joist.measurements,
                            "location": joist.location
                        }
                        for joist in result.detected_joists
                    ],
                    "form_data_generated": form_data,
                    "detection_methods_tried": ["claude_vision"],
                    "fallback_chain": ["claude_vision_succeeded"]
                }
                
                # Add debug information
                form_data['debug_log'] = debug_log
                form_data['method_used'] = 'claude_vision'
                
                debug_log.append(f"Claude Vision successful: {len(result.detected_joists)} joists detected")
                
                return {"form_data": form_data}
                
            except Exception as claude_error:
                error_id = log_error(claude_error, "pdf_processing.claude_auto_populate.claude_vision")
                debug_log.append(f"Claude Vision failed: {str(claude_error)}")
                debug_log.append(f"Error ID: {error_id}")
                
                # Continue to fallback methods
                pass
        else:
            debug_log.append("Claude Vision not available - checking for API key")
        
        # Fallback to advanced auto-populate
        debug_log.append("Falling back to advanced auto-populate")
        
        if ADVANCED_JOIST_AVAILABLE:
            try:
                detector = AdvancedJoistDetector()
                joist_labels = detector.detect_joists_advanced(content)
                
                if joist_labels:
                    # Build fallback form data
                    best_joist = max(joist_labels, key=lambda x: x.confidence)
                    form_data = {
                        'detected_joists': len(joist_labels),
                        'primary_joist_label': best_joist.label,
                        'confidence': best_joist.confidence,
                        'method_used': 'advanced_ocr_fallback',
                        'debug_log': debug_log,
                        'claude_vision_attempted': True,
                        'all_detected_joists': [
                            {
                                'label': j.label,
                                'specification': j.specification,
                                'confidence': j.confidence,
                                'methods': j.detection_methods
                            } for j in joist_labels
                        ]
                    }
                    
                    debug_log.append(f"Advanced fallback successful: {len(joist_labels)} joists")
                    return {"form_data": form_data}
                    
            except Exception as advanced_error:
                error_id = log_error(advanced_error, "pdf_processing.claude_auto_populate.advanced_fallback")
                debug_log.append(f"Advanced fallback failed: {str(advanced_error)}")
        
        # Final fallback to basic detection
        debug_log.append("Falling back to basic detection")
        try:
            detector = JoistDetector()
            basic_form_data = detector.auto_populate_calculation_form(content)
            basic_form_data['debug_log'] = debug_log
            basic_form_data['method_used'] = 'basic_fallback'
            basic_form_data['claude_vision_attempted'] = True
            
            debug_log.append("Basic fallback completed")
            return {"form_data": basic_form_data}
            
        except Exception as basic_error:
            error_id = log_error(basic_error, "pdf_processing.claude_auto_populate.basic_fallback")
            debug_log.append(f"All methods failed. Final error: {str(basic_error)}")
            
            return {
                'form_data': {
                    'error': 'All auto-population methods failed',
                    'debug_log': debug_log,
                    'claude_vision_attempted': True,
                    'error_id': error_id,
                    'suggestion': 'Please check your ANTHROPIC_API_KEY environment variable or try manual input'
                }
            }
            
    except Exception as e:
        error_id = log_error(e, "pdf_processing.claude_auto_populate.general")
        debug_log.append(f"CRITICAL ERROR: {str(e)}")
        
        return {
            'form_data': {
                'error': f'Critical error in Claude Vision auto-population: {str(e)}',
                'debug_log': debug_log,
                'error_id': error_id,
                'traceback': traceback.format_exc()
            }
        }

@router.post("/analyze-selected-areas")
async def analyze_selected_areas(
    file: UploadFile = File(...),
    request: str = Form(...)
) -> AreaAnalysisResult:
    """Analyze user-selected areas with Claude Vision AI"""
    global _last_detection_details
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not CLAUDE_VISION_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Claude Vision is not available. Check ANTHROPIC_API_KEY environment variable."
        )
    
    try:
        import datetime, json
        import os
        import psutil
        
        # Log request start with detailed info
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        log_info(f"Starting selected areas analysis - Memory: {memory_info.rss / 1024 / 1024:.1f}MB, PID: {os.getpid()}", "pdf_processing.area_analysis")
        
        content = await file.read()
        log_info(f"PDF file read - Size: {len(content) / 1024:.1f}KB", "pdf_processing.area_analysis")
        
        # Parse the JSON request
        try:
            request_data = json.loads(request)
            selection_areas = request_data.get("selection_areas", [])
            scale_notation = request_data.get("scale_notation", "1:100 at A3")  # Default scale
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request parameter")
        
        # Initialize Claude Vision analyzer
        try:
            log_info("Initializing Claude Vision analyzer...", "pdf_processing.analyzer_init")
            analyzer = ClaudeVisionAnalyzer()
            log_info("Claude Vision analyzer initialized successfully", "pdf_processing.analyzer_init")
        except Exception as init_error:
            error_id = log_error(init_error, "pdf_processing.analyzer_init")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to initialize Claude Vision analyzer: {str(init_error)}. Error ID: {error_id}"
            )
        
        # Analyze the selected areas (without scale_factor)
        try:
            area_result = analyzer.analyze_selected_areas(content, selection_areas, None)
        except Exception as analysis_error:
            error_id = log_error(analysis_error, "pdf_processing.area_analysis_failed", 
                               additional_info={"areas_count": len(selection_areas)})
            # More specific error handling
            if "anthropic" in str(analysis_error).lower():
                raise HTTPException(
                    status_code=401,
                    detail=f"Claude Vision API error: {str(analysis_error)}. Error ID: {error_id}"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Area analysis failed: {str(analysis_error)}. Error ID: {error_id}"
                )
        
        # Calculate measurements using PDF scale calculator
        measurements = None
        if selection_areas:
            pdf_doc = None
            try:
                # Open PDF to get page dimensions
                pdf_doc = fitz.open(stream=content, filetype="pdf")
                page = pdf_doc[0]  # Assuming first page for now
                
                # Get PDF page dimensions in mm
                pdf_width_mm = page.rect.width * 0.3528
                pdf_height_mm = page.rect.height * 0.3528
                
                # Initialize scale calculator
                scale_calc = PDFScaleCalculator(scale_notation)
                
                # For now, measure the first selected area
                area = selection_areas[0]
                measurements = scale_calc.measure_area(
                    area.get("x", 0),
                    area.get("y", 0),
                    area.get("x", 0) + area.get("width", 0),
                    area.get("y", 0) + area.get("height", 0),
                    pdf_width_mm,
                    pdf_height_mm
                )
                
                log_info(f"Calculated measurements: {measurements}", "pdf_processing.scale_calculation")
                
            except Exception as e:
                log_error(e, "pdf_processing.scale_calculation")
                measurements = None
            finally:
                if pdf_doc:
                    pdf_doc.close()
        
        # Generate form data from the area analysis
        form_data = analyzer.create_form_data_from_area_analysis(area_result)
        
        # Add measurements to form data if available
        if measurements:
            form_data["measurements"] = measurements
        
        # Store debug information
        _last_detection_details = {
            "timestamp": datetime.datetime.now().isoformat(),
            "method_used": "claude_vision_area_analysis",
            "pdf_filename": file.filename,
            "pdf_size_bytes": len(content),
            "areas_analyzed": len(selection_areas),
            "successful_areas": area_result.get("successful_areas", 0),
            "area_details": [
                {
                    "calculation_type": area.get("calculation_type"),
                    "coordinates": {"x": area.get("x"), "y": area.get("y"), "width": area.get("width"), "height": area.get("height")},
                    "page_number": area.get("page_number")
                }
                for area in selection_areas
            ],
            "detected_elements": area_result.get("detected_elements", []),
            "overall_confidence": area_result.get("overall_confidence", 0.0),
            "combined_reasoning": area_result.get("combined_reasoning", ""),
            "processing_time_ms": area_result.get("processing_time_ms", 0),
            "total_cost_estimate_usd": area_result.get("total_cost_estimate_usd", 0),
            "form_data_generated": form_data,
            "detection_methods_tried": ["claude_vision_area_analysis"]
        }
        
        # Log request completion
        memory_info_end = process.memory_info()
        log_info(f"Request completed successfully - Memory: {memory_info_end.rss / 1024 / 1024:.1f}MB (delta: {(memory_info_end.rss - memory_info.rss) / 1024 / 1024:.1f}MB)", 
                "pdf_processing.area_analysis")
        
        # Return structured result
        return AreaAnalysisResult(
            successful_areas=area_result.get("successful_areas", 0),
            total_areas=area_result.get("total_areas", 0),
            detected_elements=area_result.get("detected_elements", []),
            overall_confidence=area_result.get("overall_confidence", 0.0),
            combined_reasoning=area_result.get("combined_reasoning", ""),
            processing_time_ms=area_result.get("processing_time_ms", 0),
            total_cost_estimate_usd=area_result.get("total_cost_estimate_usd", 0),
            form_data=form_data,
            scale_notation=scale_notation,
            measurements=measurements
        )
        
    except Exception as e:
        error_id = log_error(e, "pdf_processing.analyze_selected_areas")
        raise HTTPException(
            status_code=500,
            detail=f"Area analysis failed: {str(e)}. Error ID: {error_id}"
        )

# Global variable to store last detection details for debugging
_last_detection_details = {}

@router.get("/debug/last-detection") 
async def get_last_detection_details():
    """Get detailed breakdown of the last joist detection"""
    if not _last_detection_details:
        return {
            "status": "no_detection_data",
            "message": "No recent detection data available. Run auto-populate first."
        }
    
    return {
        "status": "success",
        "detection_details": _last_detection_details,
        "timestamp": _last_detection_details.get("timestamp", "unknown")
    }

@router.post("/analyze-with-assumptions")
async def analyze_pdf_with_assumptions(
    file: UploadFile = File(...),
    override_scale: Optional[str] = Form(None)
):
    """
    Analyze PDF using hybrid approach with assumptions display
    """
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    if not HYBRID_ANALYZER_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Hybrid analyzer is not available. Check dependencies."
        )
    
    try:
        import tempfile
        import os
        
        # Save uploaded file temporarily
        content = await file.read()
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Initialize Claude Vision if available
            claude_vision = None
            if CLAUDE_VISION_AVAILABLE:
                try:
                    claude_vision = ClaudeVisionAnalyzer()
                except Exception as e:
                    log_warning(f"Failed to initialize Claude Vision: {e}", "pdf_processing.analyze_with_assumptions")
            
            # Use hybrid analyzer with Claude Vision
            analyzer = HybridPDFAnalyzer(claude_vision_analyzer=claude_vision)
            results = analyzer.analyze_pdf(tmp_path)
            
            # Override scale if provided
            if override_scale:
                # Update scale in results
                scale_parts = override_scale.split(':')
                if len(scale_parts) == 2 and scale_parts[0] == '1':
                    scale_factor = float(scale_parts[1])
                    results['scale'].scale_ratio = override_scale
                    results['scale'].scale_factor = scale_factor
                    results['scale'].method = 'manual'
                    results['scale'].confidence = 100.0
                    
                    # Update scale assumption
                    for assumption in results['assumptions']:
                        if assumption.id == 'scale-1':
                            assumption.value = override_scale
                            assumption.source = 'manual'
                            assumption.confidence = 100.0
            
            # Convert dataclasses to dicts for JSON response
            return {
                'scale': {
                    'scale_ratio': results['scale'].scale_ratio,
                    'scale_factor': results['scale'].scale_factor,
                    'confidence': results['scale'].confidence,
                    'method': results['scale'].method,
                    'source_text': results['scale'].source_text,
                    'page_number': results['scale'].page_number
                },
                'joists': [
                    {
                        'label': j.label,
                        'joist_type': j.joist_type,
                        'sublabel': j.sublabel,
                        'dimensions': j.dimensions,
                        'material': j.material,
                        'location': j.location,
                        'confidence': j.confidence
                    }
                    for j in results['joists']
                ],
                'joist_patterns': [
                    {
                        'label': p.label,
                        'bounding_box': p.bounding_box,
                        'orientation': p.orientation,
                        'confidence': p.confidence,
                        'characteristics': p.characteristics,
                        'nearby_text': p.nearby_text
                    }
                    for p in results.get('joist_patterns', [])
                ],
                'joist_measurements': [
                    {
                        'pattern_label': m.pattern_label,
                        'horizontal_span_m': m.horizontal_span_m,
                        'vertical_span_m': m.vertical_span_m,
                        'joist_count': m.joist_count,
                        'confidence': m.confidence,
                        'measurement_method': m.measurement_method,
                        'line_details': m.line_details,
                        'line_coordinates': m.line_coordinates
                    }
                    for m in results.get('joist_measurements', [])
                ],
                'assumptions': [
                    {
                        'id': a.id,
                        'category': a.category,
                        'description': a.description,
                        'value': a.value,
                        'confidence': a.confidence,
                        'source': a.source,
                        'editable': a.editable
                    }
                    for a in results['assumptions']
                ]
            }
            
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        error_id = log_error(e, "pdf_processing.analyze_with_assumptions")
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}. Error ID: {error_id}"
        )

@router.get("/test")
async def test_pdf_processing():
    """Test endpoint for PDF processing"""
    return {
        "message": "PDF processing module is ready",
        "advanced_capabilities": {
            "advanced_pdf_analyzer": ADVANCED_PDF_AVAILABLE,
            "advanced_joist_detector": ADVANCED_JOIST_AVAILABLE,
            "claude_vision_analyzer": CLAUDE_VISION_AVAILABLE
        },
        "debug_endpoints": [
            "/api/pdf/debug/dependencies",
            "/api/pdf/debug/errors", 
            "/api/pdf/debug/test-advanced",
            "/api/pdf/debug/basic-test",
            "/api/pdf/debug/last-detection"
        ],
        "claude_vision_endpoints": [
            "/api/pdf/analyze-claude-vision",
            "/api/pdf/auto-populate-claude-vision",
            "/api/pdf/analyze-selected-areas"
        ],
        "scale_endpoints": [
            "/api/pdf/scale-notations"
        ]
    }

@router.get("/scale-notations")
async def get_scale_notations():
    """Get list of common scale notations for UI"""
    return {
        "common_scales": COMMON_SCALES,
        "default": "1:100 at A3"
    }

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

@router.post("/calculate-dimensions", response_model=DimensionCalculationResponse)
async def calculate_dimensions(
    file: UploadFile = File(...),
    request: str = Form(...)
) -> DimensionCalculationResponse:
    """Calculate real-world dimensions from PDF coordinates - no AI needed"""
    
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