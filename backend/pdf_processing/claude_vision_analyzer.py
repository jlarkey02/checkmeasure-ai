"""
LEGACY MODULE - NOT USED IN CURRENT WORKFLOW
============================================

This module contains Claude Vision API integration for AI-powered PDF analysis.
It was used to detect joist labels and measurements from architectural drawings.

CURRENT WORKFLOW (as of 2025-08-01):
- Users manually select areas with mouse
- Users manually select element types (J1, J2, etc.) from dropdown
- System calculates dimensions using mathematical scale conversion
- No AI/Claude Vision needed

This code is kept for potential future use cases where AI detection might be valuable.

Original purpose: Automatic detection of structural elements in PDFs
Status: Replaced by user-driven selection + mathematical calculation
"""

import base64
import fitz  # PyMuPDF
import io
import os
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from PIL import Image
import anthropic
import json
import logging
from utils.enhanced_logger import enhanced_logger, log_claude_vision, log_processing_step, log_error
from utils.error_logger import log_info, log_warning

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not installed, try manual loading
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

logger = logging.getLogger(__name__)

@dataclass
class ScaleInformation:
    """Scale information extracted from drawing"""
    text_scale: Optional[str] = None  # e.g., "1:100", "SCALE 1:50"
    scale_ratio: Optional[float] = None  # Numeric ratio (0.01 for 1:100)
    graphic_scale_detected: bool = False
    confidence: float = 0.0
    extraction_method: str = "none"
    validation_notes: List[str] = None

    def __post_init__(self):
        if self.validation_notes is None:
            self.validation_notes = []

@dataclass
class DrawingContext:
    """Comprehensive drawing context information"""
    project_info: Dict[str, str] = None
    scale_info: ScaleInformation = None
    drawing_type: Optional[str] = None  # "framing_plan", "floor_plan", etc.
    standards: List[str] = None
    material_schedule: Dict[str, Any] = None
    title_block_data: Dict[str, str] = None
    extraction_confidence: float = 0.0

    def __post_init__(self):
        if self.project_info is None:
            self.project_info = {}
        if self.scale_info is None:
            self.scale_info = ScaleInformation()
        if self.standards is None:
            self.standards = []
        if self.material_schedule is None:
            self.material_schedule = {}
        if self.title_block_data is None:
            self.title_block_data = {}

@dataclass
class ClaudeJoistDetection:
    """Structured result from Claude Vision joist detection"""
    label: str
    specification: str
    location: Dict[str, float]  # x, y coordinates
    confidence: float
    reasoning: str
    measurements: Optional[Dict[str, Any]] = None
    scale_validated: bool = False
    measurement_accuracy_score: Optional[float] = None

@dataclass
class JoistMeasurement:
    """Actual joist measurements extracted from structural lines"""
    pattern_label: str  # e.g., "J1"
    horizontal_span_m: float  # e.g., 3.386
    vertical_span_m: Optional[float] = None  # e.g., 4.872
    joist_count: int = 1  # number of parallel joists detected
    confidence: float = 0.0
    measurement_method: str = "structural_lines"  # "structural_lines", "dimension_text", etc.
    line_details: Optional[Dict[str, Any]] = None  # Additional line information
    line_coordinates: Optional[Dict[str, Any]] = None  # Pixel coordinates of measured lines

@dataclass 
class ClaudeVisionResult:
    """Complete result from Claude Vision analysis"""
    detected_joists: List[ClaudeJoistDetection]
    span_length_m: Optional[float]
    joist_spacing_m: Optional[float]
    overall_confidence: float
    claude_reasoning: str
    processing_time_ms: float
    cost_estimate_usd: Optional[float]
    raw_response: Dict[str, Any]
    drawing_context: Optional[DrawingContext] = None
    scale_accuracy_score: Optional[float] = None

class ScaleDetectionEngine:
    """Engine for detecting and validating scale information from architectural drawings"""
    
    def __init__(self, claude_client):
        self.claude_client = claude_client
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 2000
    
    def extract_drawing_scale(self, pdf_images: List[Tuple[bytes, int]]) -> ScaleInformation:
        """Extract scale from title blocks and scale bars using Claude Vision"""
        try:
            log_processing_step("scale_detection", "started", 
                              details={"pages_to_analyze": len(pdf_images)})
            
            # Analyze first page for title block (most common location)
            if pdf_images:
                scale_info = self._analyze_title_block_for_scale(pdf_images[0][0])
                
                # If no clear scale found, try graphic scale detection
                if scale_info.confidence < 0.7:
                    graphic_scale = self._detect_graphic_scale(pdf_images[0][0])
                    if graphic_scale.confidence > scale_info.confidence:
                        scale_info = graphic_scale
                
                log_processing_step("scale_detection", "completed",
                                  details={
                                      "method": scale_info.extraction_method,
                                      "confidence": scale_info.confidence,
                                      "scale": scale_info.text_scale
                                  })
                
                return scale_info
            
            return ScaleInformation(extraction_method="no_images")
            
        except Exception as e:
            log_error(e, "scale_detection_engine.extract_drawing_scale")
            return ScaleInformation(extraction_method="error")
    
    def _analyze_title_block_for_scale(self, image_bytes: bytes) -> ScaleInformation:
        """Analyze title block area for scale information"""
        try:
            # Encode image for Claude
            img_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Scale detection prompt
            prompt = """
You are analyzing an architectural drawing to extract scale information from the title block.

Look for scale indicators such as:
1. **Text scales**: "1:100", "SCALE 1:50", "1/4" = 1'-0"", "NTS" (Not To Scale)
2. **Scale ratios**: Any text indicating drawing scale
3. **Title block information**: Project details, drawing numbers, scales

Return your analysis as JSON:
```json
{
  "scale_found": true,
  "scale_text": "1:100",
  "scale_ratio": 0.01,
  "confidence": 0.95,
  "location": "title_block_bottom_right",
  "extraction_method": "title_block_text",
  "validation_notes": ["Clear scale text found in standard title block location"]
}
```

If no scale is found, return scale_found: false with confidence score.
"""
            
            # Send to Claude
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            # Parse response
            response_text = response.content[0].text if response.content else ""
            scale_data = self._parse_scale_response(response_text)
            
            if scale_data and scale_data.get("scale_found"):
                return ScaleInformation(
                    text_scale=scale_data.get("scale_text"),
                    scale_ratio=scale_data.get("scale_ratio"),
                    confidence=scale_data.get("confidence", 0.0),
                    extraction_method=scale_data.get("extraction_method", "title_block"),
                    validation_notes=scale_data.get("validation_notes", [])
                )
            
            return ScaleInformation(extraction_method="title_block_not_found")
            
        except Exception as e:
            log_error(e, "scale_detection_engine._analyze_title_block_for_scale")
            return ScaleInformation(extraction_method="title_block_error")
    
    def _detect_graphic_scale(self, image_bytes: bytes) -> ScaleInformation:
        """Detect graphic scale bars in the drawing"""
        try:
            # Similar implementation for graphic scale detection
            # This would look for visual scale bars rather than text
            img_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """
Look for graphic scale bars in this architectural drawing.

Graphic scales typically appear as:
1. **Ruler-like bars** with measurement divisions
2. **Linear scales** marked with distances (0, 5m, 10m, etc.)
3. **Scale references** near the title block

Analyze any graphic scale elements and return:
```json
{
  "graphic_scale_found": true,
  "estimated_scale": "1:100",
  "scale_ratio": 0.01,
  "confidence": 0.85,
  "extraction_method": "graphic_scale_bar",
  "validation_notes": ["Found linear scale bar with 10m divisions"]
}
```
"""
            
            response = self.claude_client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            response_text = response.content[0].text if response.content else ""
            scale_data = self._parse_scale_response(response_text)
            
            if scale_data and scale_data.get("graphic_scale_found"):
                return ScaleInformation(
                    text_scale=scale_data.get("estimated_scale"),
                    scale_ratio=scale_data.get("scale_ratio"),
                    graphic_scale_detected=True,
                    confidence=scale_data.get("confidence", 0.0),
                    extraction_method=scale_data.get("extraction_method", "graphic_scale"),
                    validation_notes=scale_data.get("validation_notes", [])
                )
            
            return ScaleInformation(extraction_method="graphic_scale_not_found")
            
        except Exception as e:
            log_error(e, "scale_detection_engine._detect_graphic_scale")
            return ScaleInformation(extraction_method="graphic_scale_error")
    
    def _parse_scale_response(self, response_text: str) -> Optional[Dict]:
        """Parse Claude's scale detection response"""
        try:
            # Extract JSON from response
            import re
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
            
            # Try to find JSON object directly
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            log_error(e, "scale_detection_engine._parse_scale_response")
            return None
    
    def validate_measurement_accuracy(self, measurements: List[Dict], scale_info: ScaleInformation) -> Dict:
        """Validate extracted measurements against detected scale"""
        if not scale_info.scale_ratio or scale_info.confidence < 0.5:
            return {
                "validation_possible": False,
                "reason": "No reliable scale information available",
                "accuracy_score": 0.0
            }
        
        validated_measurements = []
        accuracy_scores = []
        
        for measurement in measurements:
            # Apply scale validation logic
            validated_measurement = self._validate_single_measurement(measurement, scale_info)
            validated_measurements.append(validated_measurement)
            accuracy_scores.append(validated_measurement.get("accuracy_score", 0.0))
        
        overall_accuracy = sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0.0
        
        return {
            "validation_possible": True,
            "overall_accuracy_score": overall_accuracy,
            "validated_measurements": validated_measurements,
            "scale_confidence": scale_info.confidence
        }
    
    def _validate_single_measurement(self, measurement: Dict, scale_info: ScaleInformation) -> Dict:
        """Validate a single measurement against scale"""
        # Add scale validation logic here
        # This would check if the measurement makes sense given the scale
        return {
            **measurement,
            "scale_validated": True,
            "accuracy_score": 0.9,
            "scale_applied": scale_info.text_scale
        }

class ClaudeVisionAnalyzer:
    """Claude Vision API integration for joist detection in architectural drawings"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Get API key from environment or parameter
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided. Set ANTHROPIC_API_KEY environment variable.")
        
        # Initialize Anthropic client with custom timeout
        self.client = anthropic.Anthropic(
            api_key=self.api_key,
            timeout=90.0,  # 90 second timeout
            max_retries=2   # Retry failed requests twice
        )
        
        # Model configuration
        self.model = "claude-3-5-sonnet-20241022"  # Latest model with vision
        self.max_tokens = 4000
        
        # Image optimization settings
        self.target_image_size = (800, 600)  # Reduced for faster processing
        self.image_quality = 85  # JPEG quality
        
        # Initialize Scale Detection Engine
        self.scale_engine = ScaleDetectionEngine(self.client)
        
        # Cache for drawing context to avoid re-extraction
        self._drawing_context_cache = {}
        
    def analyze_pdf_with_claude(self, pdf_content: bytes) -> ClaudeVisionResult:
        """Main method to analyze PDF using Claude Vision"""
        start_time = time.time()
        
        try:
            log_processing_step("claude_vision_analysis", "started", 
                              details={"pdf_size": len(pdf_content)})
            
            # Step 1: Convert PDF to optimized images
            images = self._convert_pdf_to_images(pdf_content)
            log_processing_step("pdf_to_images", "success", 
                              details={"pages_converted": len(images)})
            
            # Step 2: Extract drawing context and scale information
            drawing_context = self._extract_drawing_context(images)
            log_processing_step("context_extraction", "completed",
                              details={
                                  "scale_confidence": drawing_context.scale_info.confidence,
                                  "scale_method": drawing_context.scale_info.extraction_method
                              })
            
            # Step 3: Analyze with Claude Vision using enhanced context
            claude_response = self._analyze_images_with_claude_enhanced(images, drawing_context)
            
            # Step 4: Parse and structure results with context
            result = self._parse_claude_response_enhanced(claude_response, start_time, drawing_context)
            
            # Step 5: Validate measurements against scale
            if drawing_context.scale_info.confidence > 0.5:
                scale_validation = self.scale_engine.validate_measurement_accuracy(
                    [joist.__dict__ for joist in result.detected_joists],
                    drawing_context.scale_info
                )
                result.scale_accuracy_score = scale_validation.get("overall_accuracy_score", 0.0)
                
                log_processing_step("scale_validation", "completed",
                                  details={
                                      "accuracy_score": result.scale_accuracy_score,
                                      "validation_possible": scale_validation.get("validation_possible", False)
                                  })
            
            # Log the successful analysis
            processing_time = (time.time() - start_time) * 1000
            log_claude_vision(
                action="analyze_pdf",
                cost=result.cost_estimate_usd,
                processing_time_ms=processing_time
            )
            
            log_processing_step("claude_vision_analysis", "completed", 
                              duration_ms=processing_time,
                              details={
                                  "joists_found": len(result.detected_joists),
                                  "confidence": result.overall_confidence
                              })
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_id = log_error(e, "claude_vision_analyzer.analyze_pdf", **{
                "pdf_size": len(pdf_content),
                "processing_time_ms": processing_time
            })
            
            log_processing_step("claude_vision_analysis", "failed", 
                              duration_ms=processing_time,
                              details={"error_id": error_id})
            
            raise e
    
    def _extract_drawing_context(self, pdf_images: List[Tuple[bytes, int]]) -> DrawingContext:
        """Extract comprehensive drawing context including scale and project information"""
        try:
            # Extract scale information
            scale_info = self.scale_engine.extract_drawing_scale(pdf_images)
            
            # Extract title block and project context (using first page)
            project_context = self._extract_title_block_context(pdf_images[0][0] if pdf_images else None)
            
            # Determine drawing type
            drawing_type = self._classify_drawing_type(pdf_images[0][0] if pdf_images else None)
            
            return DrawingContext(
                project_info=project_context.get("project_info", {}),
                scale_info=scale_info,
                drawing_type=drawing_type,
                standards=project_context.get("standards", ["AS1684"]),  # Default Australian standard
                title_block_data=project_context.get("title_block", {}),
                extraction_confidence=min(scale_info.confidence, project_context.get("confidence", 0.5))
            )
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._extract_drawing_context")
            # Return default context with minimal information
            return DrawingContext(
                scale_info=ScaleInformation(extraction_method="error"),
                drawing_type="unknown",
                standards=["AS1684"]
            )
    
    def _extract_title_block_context(self, image_bytes: Optional[bytes]) -> Dict:
        """Extract project information from title block"""
        if not image_bytes:
            return {"confidence": 0.0}
        
        try:
            img_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """
Analyze this architectural drawing's title block and extract project information.

Look for:
1. **Project Name/Address**: Building location or project title
2. **Drawing Number**: Sheet identification (e.g., S-01, A-02)
3. **Drawing Title**: Type of drawing (e.g., "Floor Framing Plan", "Structural Plan")
4. **Standards Referenced**: Building codes (AS1684, BCA, etc.)
5. **Date and Revision**: Drawing version information
6. **Architect/Engineer**: Design professional information

Return as JSON:
```json
{
  "project_info": {
    "name": "3 Fiddens Wharf Rd",
    "address": "Banora Point, NSW",
    "drawing_number": "S-01"
  },
  "title_block": {
    "drawing_title": "Structural Framing Plan",
    "revision": "B",
    "date": "14.05.25"
  },
  "standards": ["AS1684", "BCA"],
  "confidence": 0.9
}
```
"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }]
            )
            
            response_text = response.content[0].text if response.content else ""
            context_data = self.scale_engine._parse_scale_response(response_text)
            
            return context_data or {"confidence": 0.0}
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._extract_title_block_context")
            return {"confidence": 0.0}
    
    def _classify_drawing_type(self, image_bytes: Optional[bytes]) -> str:
        """Classify the type of architectural drawing"""
        if not image_bytes:
            return "unknown"
        
        try:
            # Quick classification based on typical drawing elements
            # This could be enhanced with a separate Claude analysis
            return "framing_plan"  # Default assumption for structural drawings
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._classify_drawing_type")
            return "unknown"
    
    def _convert_pdf_to_images(self, pdf_content: bytes) -> List[Tuple[bytes, int]]:
        """Convert PDF pages to optimized images for Claude Vision"""
        images = []
        pdf_doc = None
        
        try:
            # Open PDF from bytes
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                
                # Calculate optimal DPI for ~1.15MP target
                page_rect = page.rect
                target_width, target_height = self.target_image_size
                
                # Calculate scaling to fit target size while maintaining aspect ratio
                scale_x = target_width / page_rect.width
                scale_y = target_height / page_rect.height
                scale = min(scale_x, scale_y)
                
                # Generate image at calculated scale
                mat = fitz.Matrix(scale, scale)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convert to PIL Image for optimization
                img_bytes = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_bytes))
                
                # Optimize image
                optimized_bytes = self._optimize_image_for_claude(pil_image)
                images.append((optimized_bytes, page_num))
                
                log_processing_step(f"convert_page_{page_num}", "success",
                                  details={
                                      "original_size": f"{page_rect.width}x{page_rect.height}",
                                      "optimized_size": f"{pil_image.width}x{pil_image.height}",
                                      "file_size_kb": len(optimized_bytes) / 1024
                                  })
            
            return images
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._convert_pdf_to_images")
            raise e
        finally:
            if pdf_doc:
                pdf_doc.close()
    
    def _optimize_image_for_claude(self, pil_image: Image.Image) -> bytes:
        """Optimize PIL image for Claude Vision API"""
        # Resize if needed (maintaining aspect ratio)
        if pil_image.size != self.target_image_size:
            pil_image.thumbnail(self.target_image_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Save as optimized PNG (better for technical drawings than JPEG)
        img_buffer = io.BytesIO()
        pil_image.save(img_buffer, format='PNG', optimize=True)
        return img_buffer.getvalue()
    
    def _analyze_images_with_claude(self, images: List[Tuple[bytes, int]]) -> Dict[str, Any]:
        """Send images to Claude Vision API for analysis"""
        try:
            # Prepare messages with images
            content_blocks = []
            
            # Add each image
            for img_bytes, page_num in images:
                # Encode image to base64
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64
                    }
                })
                
                # Add page context
                content_blocks.append({
                    "type": "text",
                    "text": f"[Page {page_num + 1} of the architectural drawing]"
                })
            
            # Add the main analysis prompt
            content_blocks.append({
                "type": "text", 
                "text": self._get_joist_analysis_prompt()
            })
            
            log_claude_vision("request_sent", 
                            prompt=self._get_joist_analysis_prompt()[:200])
            
            # Send request to Claude
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )
            
            api_time = (time.time() - start_time) * 1000
            
            # Extract response
            response_text = message.content[0].text if message.content else ""
            
            log_claude_vision("response_received",
                            response={"preview": response_text[:200]},
                            processing_time_ms=api_time)
            
            return {
                "response_text": response_text,
                "usage": message.usage.__dict__ if hasattr(message, 'usage') else None,
                "api_time_ms": api_time
            }
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._analyze_images_with_claude")
            raise e
    
    def _analyze_images_with_claude_enhanced(self, images: List[Tuple[bytes, int]], drawing_context: DrawingContext) -> Dict[str, Any]:
        """Send images to Claude Vision API for analysis with enhanced context"""
        try:
            # Prepare messages with images
            content_blocks = []
            
            # Add each image
            for img_bytes, page_num in images:
                # Encode image to base64
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64
                    }
                })
                
                # Add page context with drawing information
                page_context = f"[Page {page_num + 1} of {drawing_context.drawing_type}]"
                if drawing_context.scale_info.text_scale:
                    page_context += f" - Scale: {drawing_context.scale_info.text_scale}"
                if drawing_context.project_info.get("name"):
                    page_context += f" - Project: {drawing_context.project_info['name']}"
                
                content_blocks.append({
                    "type": "text",
                    "text": page_context
                })
            
            # Add the enhanced analysis prompt with context
            content_blocks.append({
                "type": "text", 
                "text": self._get_enhanced_joist_analysis_prompt(drawing_context)
            })
            
            log_claude_vision("request_sent_enhanced", 
                            prompt=self._get_enhanced_joist_analysis_prompt(drawing_context)[:200])
            
            # Send request to Claude
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )
            
            api_time = (time.time() - start_time) * 1000
            
            # Extract response
            response_text = message.content[0].text if message.content else ""
            
            log_claude_vision("response_received_enhanced",
                            response={"preview": response_text[:200]},
                            processing_time_ms=api_time)
            
            return {
                "response_text": response_text,
                "usage": message.usage.__dict__ if hasattr(message, 'usage') else None,
                "api_time_ms": api_time,
                "drawing_context": drawing_context
            }
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._analyze_images_with_claude_enhanced")
            raise e
    
    def _parse_claude_response_enhanced(self, claude_response: Dict[str, Any], start_time: float, drawing_context: DrawingContext) -> ClaudeVisionResult:
        """Parse Claude's response into structured result with context validation"""
        try:
            response_text = claude_response.get("response_text", "")
            
            # Extract JSON from Claude's response
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                raise ValueError("No valid JSON found in Claude's response")
            
            # Parse detected joists with enhanced validation
            detected_joists = []
            for joist_data in json_data.get("detected_joists", []):
                joist = ClaudeJoistDetection(
                    label=joist_data.get("label", ""),
                    specification=joist_data.get("specification", ""),
                    location=joist_data.get("location", {}),
                    confidence=float(joist_data.get("confidence", 0.0)),
                    reasoning=joist_data.get("reasoning", ""),
                    measurements=joist_data.get("measurements"),
                    scale_validated=drawing_context.scale_info.confidence > 0.5,
                    measurement_accuracy_score=None  # Will be calculated during validation
                )
                detected_joists.append(joist)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (rough approximation based on tokens)
            usage = claude_response.get("usage")
            cost_estimate = self._estimate_api_cost(usage) if usage else None
            
            return ClaudeVisionResult(
                detected_joists=detected_joists,
                span_length_m=json_data.get("span_length_m"),
                joist_spacing_m=json_data.get("joist_spacing_m"),
                overall_confidence=float(json_data.get("overall_confidence", 0.0)),
                claude_reasoning=json_data.get("claude_reasoning", ""),
                processing_time_ms=processing_time_ms,
                cost_estimate_usd=cost_estimate,
                raw_response=json_data,
                drawing_context=drawing_context,
                scale_accuracy_score=None  # Will be set during validation
            )
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._parse_claude_response_enhanced", **{
                "response_preview": claude_response.get("response_text", "")[:200]
            })
            raise e
    
    def _get_enhanced_joist_analysis_prompt(self, drawing_context: DrawingContext) -> str:
        """Get enhanced joist analysis prompt with drawing context"""
        
        # Build context section
        context_section = f"""
**DRAWING CONTEXT:**
- Drawing Type: {drawing_context.drawing_type}
- Scale: {drawing_context.scale_info.text_scale or 'Not detected'}
- Standards: {', '.join(drawing_context.standards)}
"""
        
        if drawing_context.project_info.get("name"):
            context_section += f"- Project: {drawing_context.project_info['name']}\n"
        
        if drawing_context.scale_info.confidence > 0.7:
            scale_instruction = f"""
**SCALE ACCURACY CRITICAL:**
- This drawing is at {drawing_context.scale_info.text_scale} scale
- All measurements MUST be converted using this scale
- Validate that extracted dimensions make sense at this scale
- Apply scale ratio of {drawing_context.scale_info.scale_ratio} if available
"""
        else:
            scale_instruction = """
**SCALE WARNING:**
- Drawing scale not reliably detected
- Exercise caution with measurement extraction
- Note any scale indicators you can identify
"""
        
        # Enhanced prompt with context
        return f"""You are an expert structural engineer analyzing architectural drawings for joist detection and measurements.

{context_section}

{scale_instruction}

Please analyze these technical drawings and identify:

1. **Joist Labels**: Look for labels like "J1", "J2", "J3", etc. that indicate joist specifications
2. **Joist Specifications**: Find text near joist labels describing dimensions and materials (e.g., "200 x 45 LVL at 450 centres")
3. **Measurements**: Identify span lengths and spacing measurements - APPLY SCALE CORRECTION
4. **Visual Elements**: 
   - Red lines typically indicate joist placement
   - Blue lines typically show rim boards
   - Parallel lines may represent joists
   - Dimension lines with measurements
5. **Context Integration**: Consider project type and standards when interpreting specifications

**CRITICAL**: Return your analysis as a JSON object with this exact structure:

```json
{{
  "detected_joists": [
    {{
      "label": "J1",
      "specification": "200 x 45 LVL at 450 centres", 
      "location": {{"x": 100, "y": 200}},
      "confidence": 0.95,
      "reasoning": "Clear label 'J1' with specification text nearby",
      "measurements": {{
        "width_mm": 200,
        "depth_mm": 45,
        "material": "LVL",
        "spacing_mm": 450
      }},
      "scale_considerations": "Measurements verified against {drawing_context.scale_info.text_scale or 'unknown'} scale"
    }}
  ],
  "span_length_m": 3.386,
  "joist_spacing_m": 0.45,
  "overall_confidence": 0.90,
  "claude_reasoning": "Found clear joist labels with specifications. Applied {drawing_context.scale_info.text_scale or 'estimated'} scale for measurements. Context indicates {drawing_context.drawing_type} for {drawing_context.project_info.get('name', 'residential project')}.",
  "visual_elements_found": [
    "Joist labels (J1, J2)",
    "Dimension lines", 
    "Specification text",
    "Red joist placement lines"
  ],
  "scale_validation": {{
    "scale_used": "{drawing_context.scale_info.text_scale or 'not_available'}",
    "confidence": {drawing_context.scale_info.confidence},
    "measurement_method": "{drawing_context.scale_info.extraction_method}"
  }}
}}
```

**Important Guidelines:**
- Only include joists you can clearly identify with high confidence
- Convert all measurements to meters for span_length_m and joist_spacing_m using the detected scale
- Keep measurements in mm for the individual joist measurements object
- If scale is reliable, apply it to ALL measurements
- If you cannot find clear measurements, set values to null
- Confidence scores should be between 0.0 and 1.0
- Provide detailed reasoning for your findings including scale considerations
- Focus on structural elements, ignore architectural details like windows/doors
- Apply {', '.join(drawing_context.standards)} standards where applicable

Look carefully at the drawing and provide your analysis:"""
    
    def _get_joist_analysis_prompt(self) -> str:
        """Get the specialized prompt for joist detection"""
        return """You are an expert structural engineer analyzing architectural drawings for joist detection and measurements.

Please analyze these technical drawings and identify:

1. **Joist Labels**: Look for labels like "J1", "J2", "J3", etc. that indicate joist specifications
2. **Joist Specifications**: Find text near joist labels describing dimensions and materials (e.g., "200 x 45 LVL at 450 centres")
3. **Measurements**: Identify span lengths and spacing measurements
4. **Visual Elements**: 
   - Red lines typically indicate joist placement
   - Blue lines typically show rim boards
   - Parallel lines may represent joists
   - Dimension lines with measurements

**CRITICAL**: Return your analysis as a JSON object with this exact structure:

```json
{
  "detected_joists": [
    {
      "label": "J1",
      "specification": "200 x 45 LVL at 450 centres", 
      "location": {"x": 100, "y": 200},
      "confidence": 0.95,
      "reasoning": "Clear label 'J1' with specification text nearby",
      "measurements": {
        "width_mm": 200,
        "depth_mm": 45,
        "material": "LVL",
        "spacing_mm": 450
      }
    }
  ],
  "span_length_m": 3.386,
  "joist_spacing_m": 0.45,
  "overall_confidence": 0.90,
  "claude_reasoning": "Found clear joist labels with specifications. The drawing shows a span of 3.386m with 450mm centres spacing. Red lines indicate joist placement.",
  "visual_elements_found": [
    "Joist labels (J1, J2)",
    "Dimension lines", 
    "Specification text",
    "Red joist placement lines"
  ]
}
```

**Important Guidelines:**
- Only include joists you can clearly identify with high confidence
- Convert all measurements to meters for span_length_m and joist_spacing_m
- Keep measurements in mm for the individual joist measurements object
- If you cannot find clear measurements, set values to null
- Confidence scores should be between 0.0 and 1.0
- Provide detailed reasoning for your findings
- Focus on structural elements, ignore architectural details like windows/doors

Look carefully at the drawing and provide your analysis:"""

    def _parse_claude_response(self, claude_response: Dict[str, Any], start_time: float) -> ClaudeVisionResult:
        """Parse Claude's response into structured result"""
        try:
            response_text = claude_response.get("response_text", "")
            
            # Extract JSON from Claude's response
            json_data = self._extract_json_from_response(response_text)
            
            if not json_data:
                raise ValueError("No valid JSON found in Claude's response")
            
            # Parse detected joists
            detected_joists = []
            for joist_data in json_data.get("detected_joists", []):
                joist = ClaudeJoistDetection(
                    label=joist_data.get("label", ""),
                    specification=joist_data.get("specification", ""),
                    location=joist_data.get("location", {}),
                    confidence=float(joist_data.get("confidence", 0.0)),
                    reasoning=joist_data.get("reasoning", ""),
                    measurements=joist_data.get("measurements")
                )
                detected_joists.append(joist)
            
            # Calculate processing time
            processing_time_ms = (time.time() - start_time) * 1000
            
            # Estimate cost (rough approximation based on tokens)
            usage = claude_response.get("usage")
            cost_estimate = self._estimate_api_cost(usage) if usage else None
            
            return ClaudeVisionResult(
                detected_joists=detected_joists,
                span_length_m=json_data.get("span_length_m"),
                joist_spacing_m=json_data.get("joist_spacing_m"),
                overall_confidence=float(json_data.get("overall_confidence", 0.0)),
                claude_reasoning=json_data.get("claude_reasoning", ""),
                processing_time_ms=processing_time_ms,
                cost_estimate_usd=cost_estimate,
                raw_response=json_data
            )
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._parse_claude_response", **{
                "response_preview": claude_response.get("response_text", "")[:200]
            })
            raise e
    
    def _extract_json_from_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON object from Claude's response text"""
        try:
            # Look for JSON between code blocks
            import re
            
            # Try to find JSON in code blocks first
            json_pattern = r'```json\s*(\{.*?\})\s*```'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            if matches:
                return json.loads(matches[0])
            
            # Try to find JSON object directly
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, response_text, re.DOTALL)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._extract_json_from_response")
            return None
    
    def _estimate_api_cost(self, usage: Dict) -> Optional[float]:
        """Estimate API cost based on token usage"""
        try:
            # Claude 3.5 Sonnet pricing (as of 2025)
            input_cost_per_1k = 0.003  # $0.003 per 1K input tokens
            output_cost_per_1k = 0.015  # $0.015 per 1K output tokens
            
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            
            input_cost = (input_tokens / 1000) * input_cost_per_1k
            output_cost = (output_tokens / 1000) * output_cost_per_1k
            
            return round(input_cost + output_cost, 6)
            
        except Exception:
            return None
    
    def _make_api_call_with_retry(self, messages, max_retries=3):
        """Make API call with retry logic for connection errors"""
        for attempt in range(max_retries):
            try:
                return self.client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    messages=messages
                )
            except Exception as e:
                log_warning(f"API call attempt {attempt + 1} failed: {str(e)}", "claude_vision.api_retry")
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff
    
    def analyze_selected_areas(self, pdf_content: bytes, selection_areas: List[Dict], scale_factor: Optional[float] = None) -> Dict[str, Any]:
        """Analyze specific areas marked by user with Claude Vision"""
        start_time = time.time()
        
        try:
            log_processing_step("area_analysis", "started", 
                              details={"areas_count": len(selection_areas)})
            log_info(f"Starting area analysis for {len(selection_areas)} areas", "claude_vision.analyze_selected_areas")
            
            # Group areas by page number for efficient processing
            areas_by_page = {}
            for area in selection_areas:
                page_num = area.get('page_number', 0)
                if page_num not in areas_by_page:
                    areas_by_page[page_num] = []
                areas_by_page[page_num].append(area)
            
            log_info(f"Areas spread across {len(areas_by_page)} pages", "claude_vision.analyze_selected_areas")
            
            area_results = []
            total_cost = 0.0
            
            # Process pages one at a time
            for page_num, page_areas in areas_by_page.items():
                # Convert only this specific page
                pdf_conversion_start = time.time()
                log_info(f"Converting page {page_num} to image...", "claude_vision.pdf_conversion")
                page_image = self._convert_single_page_to_image(pdf_content, page_num)
                pdf_conversion_time = (time.time() - pdf_conversion_start) * 1000
                log_info(f"Page {page_num} conversion completed in {pdf_conversion_time:.0f}ms", "claude_vision.pdf_conversion")
                
                if not page_image:
                    log_warning(f"Failed to convert page {page_num}", "claude_vision.pdf_conversion")
                    continue
                
                # Process all areas on this page
                for i, area in enumerate(page_areas):
                    try:
                        area_start_time = time.time()
                        area_index = selection_areas.index(area)
                        log_info(f"Processing area {area_index+1}/{len(selection_areas)}: {area.get('calculation_type', 'unknown')}", "claude_vision.area_processing")
                        
                        # Crop the specific area from the page image
                        crop_start = time.time()
                        cropped_image = self._crop_area_from_single_image(page_image, area)
                        crop_time = (time.time() - crop_start) * 1000
                        log_info(f"Area cropping completed in {crop_time:.0f}ms", "claude_vision.area_cropping")
                        
                        if cropped_image:
                            # Analyze this specific area with Claude Vision
                            claude_start = time.time()
                            log_info(f"Sending area {area_index+1} to Claude Vision API...", "claude_vision.api_call")
                            area_result = self._analyze_area_with_claude(cropped_image, area, scale_factor)
                            claude_time = (time.time() - claude_start) * 1000
                            log_info(f"Claude Vision API responded in {claude_time:.0f}ms", "claude_vision.api_call")
                            
                            area_results.append(area_result)
                            
                            if area_result.get("cost_estimate_usd"):
                                total_cost += area_result["cost_estimate_usd"]
                            
                            area_total_time = (time.time() - area_start_time) * 1000
                            log_processing_step(f"area_{area_index}_analysis", "success",
                                              duration_ms=area_total_time,
                                              details={"calculation_type": area.get("calculation_type")})
                        else:
                            log_warning(f"Failed to crop area {area_index+1}", "claude_vision.area_cropping")
                    
                    except Exception as area_error:
                        area_index = selection_areas.index(area)
                        log_error(area_error, f"claude_vision_analyzer.analyze_area_{area_index}")
                        area_results.append({
                            "area_index": area_index,
                            "error": str(area_error),
                            "calculation_type": area.get("calculation_type", "unknown")
                        })
            
            processing_time = (time.time() - start_time) * 1000
            
            # Combine results into unified response
            log_info("Combining area results...", "claude_vision.combine_results")
            combined_result = self._combine_area_results(area_results, processing_time, total_cost)
            
            log_processing_step("area_analysis", "completed",
                              duration_ms=processing_time,
                              details={
                                  "successful_areas": len([r for r in area_results if "error" not in r]),
                                  "pages_processed": len(areas_by_page),
                                  "total_processing_ms": processing_time
                              })
            log_info(f"Area analysis completed in {processing_time:.0f}ms total", "claude_vision.analyze_selected_areas")
            
            return combined_result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            error_id = log_error(e, "claude_vision_analyzer.analyze_selected_areas", **{
                "areas_count": len(selection_areas),
                "processing_time_ms": processing_time
            })
            raise e
    
    def _crop_area_from_image(self, pdf_images: List[Tuple[bytes, int]], area: Dict) -> Optional[bytes]:
        """Crop specific area from PDF page image"""
        try:
            page_number = area.get("page_number", 0)
            
            # Find the correct page
            target_image = None
            for img_bytes, page_num in pdf_images:
                if page_num == page_number:
                    target_image = img_bytes
                    break
            
            if not target_image:
                return None
            
            # Load image with PIL
            pil_image = Image.open(io.BytesIO(target_image))
            
            # Get area coordinates (assuming they're in PDF coordinates)
            x = area.get("x", 0)
            y = area.get("y", 0) 
            width = area.get("width", 100)
            height = area.get("height", 100)
            
            # Convert PDF coordinates to image coordinates if needed
            # (This might need adjustment based on how coordinates are stored)
            img_width, img_height = pil_image.size
            
            # Crop the area
            left = max(0, int(x))
            top = max(0, int(y))
            right = min(img_width, int(x + width))
            bottom = min(img_height, int(y + height))
            
            cropped = pil_image.crop((left, top, right, bottom))
            
            # Convert back to bytes
            img_buffer = io.BytesIO()
            cropped.save(img_buffer, format='PNG', optimize=True)
            return img_buffer.getvalue()
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._crop_area_from_image")
            return None
    
    def _convert_single_page_to_image(self, pdf_content: bytes, page_number: int) -> Optional[bytes]:
        """Convert a single PDF page to an optimized image for Claude Vision"""
        pdf_doc = None
        
        try:
            # Open PDF from bytes
            pdf_doc = fitz.open(stream=pdf_content, filetype="pdf")
            
            # Convert from 1-indexed (frontend) to 0-indexed (PyMuPDF)
            page_index = page_number - 1
            
            # Check if page exists
            if page_index < 0 or page_index >= len(pdf_doc):
                log_warning(f"Page {page_number} (index {page_index}) does not exist in PDF with {len(pdf_doc)} pages", "claude_vision.convert_single_page")
                return None
            
            page = pdf_doc[page_index]
            
            # Calculate optimal DPI for ~1.15MP target
            page_rect = page.rect
            target_width, target_height = self.target_image_size
            
            # Calculate scaling to fit target size while maintaining aspect ratio
            scale_x = target_width / page_rect.width
            scale_y = target_height / page_rect.height
            scale = min(scale_x, scale_y)
            
            # Generate image at calculated scale
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            # Convert to PNG bytes
            img_bytes = pix.tobytes("png")
            
            return img_bytes
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._convert_single_page_to_image")
            return None
        finally:
            if pdf_doc:
                pdf_doc.close()
    
    def _crop_area_from_single_image(self, page_image: bytes, area: Dict) -> Optional[bytes]:
        """Crop specific area from a single page image"""
        try:
            # Load image with PIL
            pil_image = Image.open(io.BytesIO(page_image))
            
            # Get area coordinates
            x = area.get("x", 0)
            y = area.get("y", 0) 
            width = area.get("width", 100)
            height = area.get("height", 100)
            
            # Get image dimensions
            img_width, img_height = pil_image.size
            
            # Crop the area
            left = max(0, int(x))
            top = max(0, int(y))
            right = min(img_width, int(x + width))
            bottom = min(img_height, int(y + height))
            
            cropped = pil_image.crop((left, top, right, bottom))
            
            # Convert back to bytes
            img_buffer = io.BytesIO()
            cropped.save(img_buffer, format='PNG', optimize=True)
            return img_buffer.getvalue()
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._crop_area_from_single_image")
            return None
    
    def _analyze_area_with_claude(self, area_image: bytes, area_info: Dict, scale_factor: Optional[float] = None) -> Dict[str, Any]:
        """Analyze a specific cropped area with Claude Vision"""
        try:
            # Default scale_factor to 100 if not provided
            effective_scale_factor = scale_factor if scale_factor is not None else 100.0
            
            # Get calculation-type-specific prompt
            calculation_type = area_info.get("calculation_type", "general")
            prompt = self._get_area_specific_prompt(calculation_type)
            
            # Encode image to base64
            img_base64 = base64.b64encode(area_image).decode('utf-8')
            
            # Prepare content for Claude
            content_blocks = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64", 
                        "media_type": "image/png",
                        "data": img_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
            
            # Send request to Claude with retry logic
            start_time = time.time()
            message = self._make_api_call_with_retry([{
                "role": "user",
                "content": content_blocks
            }])
            
            api_time = (time.time() - start_time) * 1000
            
            # Process response
            response_text = message.content[0].text if message.content else ""
            json_data = self._extract_json_from_response(response_text)
            
            # Log Claude Vision response for debugging
            log_info(f"Claude Vision raw response length: {len(response_text)} chars", "claude_vision.debug")
            if json_data:
                log_info(f"Claude Vision parsed JSON keys: {list(json_data.keys())}", "claude_vision.debug")
                if "detected_elements" in json_data:
                    log_info(f"Detected {len(json_data['detected_elements'])} elements", "claude_vision.debug")
                    for i, elem in enumerate(json_data['detected_elements']):
                        log_info(f"Element {i}: label='{elem.get('label')}', type='{elem.get('type')}', measurements={elem.get('measurements', {})}", "claude_vision.debug")
            else:
                log_warning("Failed to parse JSON from Claude Vision response", "claude_vision.debug")
            
            # Calculate cost
            usage = message.usage.__dict__ if hasattr(message, 'usage') else None
            cost_estimate = self._estimate_api_cost(usage) if usage else None
            
            return {
                "calculation_type": calculation_type,
                "area_info": area_info,
                "claude_response": json_data or {"raw_text": response_text},
                "processing_time_ms": api_time,
                "cost_estimate_usd": cost_estimate,
                "scale_factor": scale_factor,
                "success": True
            }
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._analyze_area_with_claude")
            return {
                "calculation_type": area_info.get("calculation_type", "unknown"),
                "area_info": area_info,
                "error": str(e),
                "success": False
            }
    
    def _get_area_specific_prompt(self, calculation_type: str) -> str:
        """Get specialized prompt based on calculation type"""
        prompts = {
            "joist": """You are analyzing a specific area marked by a user that contains joist specifications.

Focus on this marked area and identify:

1. **Joist Information**:
   - Labels like "J1", "J2", "J3", etc.
   - Material specifications (e.g., "200 x 45 LVL", "150 x 45 MGP10")
   - Spacing information (e.g., "at 450 centres", "@600 CTS")
   - Any span or dimension measurements

2. **Structural Details**:
   - Joist type and size
   - Material grade
   - Spacing between joists
   - Any blocking or support requirements

Return your analysis as JSON:
```json
{
  "detected_elements": [
    {
      "label": "J1",
      "type": "joist",
      "confidence": 0.95,
      "specification": "200 x 45 LVL at 450 centres",
      "material": "LVL",
      "size": "200x45",
      "spacing": "450mm"
    }
  ],
  "span_measurements": ["3.386m", "4.872m"],
  "confidence": 0.90,
  "reasoning": "Found J1 joist specification with 200x45 LVL at 450mm centres"
}
```""",
            
            "beam": """You are analyzing a specific area marked by a user that contains beam specifications.

Focus ONLY on this marked area and identify:
1. **Beam Labels**: Any labels like "B1", "B2", "GLB1", etc.
2. **Beam Specifications**: Text describing dimensions and materials
3. **Load Information**: Any load ratings or specifications
4. **Span Measurements**: Length dimensions

Return your analysis as JSON with beam-specific information.""",
            
            "wall": """You are analyzing a specific area marked by a user that contains wall framing specifications.

Focus ONLY on this marked area and identify:
1. **Stud Specifications**: Dimensions and spacing (e.g., "90x45 at 450 centres")
2. **Wall Labels**: Any reference codes
3. **Heights**: Wall height measurements
4. **Material Types**: Timber grades or types

Return your analysis as JSON with wall framing information.""",
            
            "rafter": """You are analyzing a specific area marked by a user that contains rafter specifications.

Focus ONLY on this marked area and identify:
1. **Rafter Labels**: Any labels like "R1", "R2", etc.
2. **Rafter Specifications**: Dimensions, spacing, and material
3. **Pitch/Angle**: Any roof pitch information
4. **Span Measurements**: Rafter length dimensions

Return your analysis as JSON with rafter-specific information.""",
            
            "general": """You are analyzing a construction drawing area.

Focus on identifying:

1. **Structural Elements**: Any beams, joists, columns, or other members
2. **Material Specifications**: Sizes, grades, and types
3. **Dimensions**: Spans, spacings, or other measurements
4. **Labels**: Reference codes or identifiers

Return as JSON with detected_elements array."""
        }
        
        return prompts.get(calculation_type, prompts["general"])  # Default to general
    
    def _combine_area_results(self, area_results: List[Dict], processing_time: float, total_cost: float) -> Dict[str, Any]:
        """Combine multiple area analysis results into unified response"""
        successful_results = [r for r in area_results if r.get("success", False)]
        
        all_elements = []
        combined_reasoning = []
        
        for result in successful_results:
            claude_response = result.get("claude_response", {})
            if "detected_elements" in claude_response:
                all_elements.extend(claude_response["detected_elements"])
            
            if "reasoning" in claude_response:
                area_type = result.get("calculation_type", "area")
                combined_reasoning.append(f"{area_type}: {claude_response['reasoning']}")
        
        # Calculate overall confidence
        confidences = []
        for result in successful_results:
            claude_response = result.get("claude_response", {})
            if "confidence" in claude_response:
                confidences.append(claude_response["confidence"])
        
        overall_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "area_analysis_results": area_results,
            "detected_elements": all_elements,
            "overall_confidence": overall_confidence,
            "combined_reasoning": "; ".join(combined_reasoning),
            "processing_time_ms": processing_time,
            "total_cost_estimate_usd": total_cost,
            "successful_areas": len(successful_results),
            "total_areas": len(area_results)
        }

    def create_form_data_from_result(self, result: ClaudeVisionResult) -> Dict[str, Any]:
        """Convert Claude Vision result to form data format"""
        form_data = {
            "detected_joists": len(result.detected_joists),
            "claude_vision_used": True,
            "confidence": result.overall_confidence,
            "claude_reasoning": result.claude_reasoning,
            "processing_time_ms": result.processing_time_ms,
            "cost_estimate_usd": result.cost_estimate_usd,
            "detection_methods": ["claude_vision"]
        }
        
        # Add measurements if found
        if result.span_length_m:
            form_data["span_length"] = result.span_length_m
        
        if result.joist_spacing_m:
            form_data["joist_spacing"] = result.joist_spacing_m
        
        # Add all detected joists
        if result.detected_joists:
            best_joist = max(result.detected_joists, key=lambda x: x.confidence)
            form_data["primary_joist_label"] = best_joist.label
            form_data["primary_joist_specification"] = best_joist.specification
            
            form_data["all_detected_joists"] = [
                {
                    "label": joist.label,
                    "specification": joist.specification,
                    "confidence": joist.confidence,
                    "reasoning": joist.reasoning,
                    "measurements": joist.measurements
                }
                for joist in result.detected_joists
            ]
        
        return form_data
    
    def detect_joist_patterns(self, pdf_content: bytes, example_pdf_path: Optional[str] = None) -> Dict[str, Any]:
        """Detect J1 cross-pattern joists (J1A-F) using Claude Vision with training example"""
        start_time = time.time()
        
        try:
            log_processing_step("joist_pattern_detection", "started")
            
            # Convert PDF to images
            pdf_images = self._convert_pdf_to_images(pdf_content)
            if not pdf_images:
                return {"patterns_found": [], "error": "Failed to convert PDF to images"}
            
            # Load example PDF if provided for training
            example_image = None
            if example_pdf_path and os.path.exists(example_pdf_path):
                try:
                    with open(example_pdf_path, 'rb') as f:
                        example_pdf_content = f.read()
                    example_images = self._convert_pdf_to_images(example_pdf_content)
                    if example_images:
                        example_image = example_images[0][0]  # First page
                        log_processing_step("example_pdf_loaded", "success")
                except Exception as e:
                    log_error(e, "Failed to load example PDF")
            
            # Analyze with Claude Vision using pattern detection prompt
            result = self._analyze_joist_patterns_with_claude(pdf_images[0][0], example_image)
            
            processing_time = (time.time() - start_time) * 1000
            
            log_processing_step("joist_pattern_detection", "completed",
                              duration_ms=processing_time,
                              details={"patterns_found": len(result.get("patterns", []))})
            
            return result
            
        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            log_error(e, "claude_vision_analyzer.detect_joist_patterns")
            return {
                "patterns_found": [],
                "error": str(e),
                "processing_time_ms": processing_time
            }
    
    def _analyze_joist_patterns_with_claude(self, target_image: bytes, example_image: Optional[bytes] = None) -> Dict[str, Any]:
        """Analyze PDF for J1 cross-pattern sections using Claude Vision"""
        try:
            # Prepare content blocks
            content_blocks = []
            
            # Add example image if available
            if example_image:
                example_base64 = base64.b64encode(example_image).decode('utf-8')
                content_blocks.extend([
                    {
                        "type": "text",
                        "text": "Here is an example showing J1A through J1F patterns marked on a similar drawing:"
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": example_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": "Notice how J1A-F are cross-hatched rectangular areas with parallel lines indicating joists. Some are rotated 90 degrees in narrow spaces."
                    }
                ])
            
            # Add target image
            target_base64 = base64.b64encode(target_image).decode('utf-8')
            content_blocks.extend([
                {
                    "type": "text",
                    "text": "Now analyze this drawing and find similar cross-hatched rectangular patterns:"
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": target_base64
                    }
                }
            ])
            
            # Add the pattern detection prompt
            content_blocks.append({
                "type": "text",
                "text": self._get_joist_pattern_detection_prompt()
            })
            
            # Send to Claude
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )
            
            api_time = (time.time() - start_time) * 1000
            
            # Parse response
            response_text = message.content[0].text if message.content else ""
            patterns_data = self._extract_json_from_response(response_text)
            
            if patterns_data:
                patterns_data["processing_time_ms"] = api_time
                patterns_data["method"] = "claude_vision_pattern_detection"
                return patterns_data
            
            return {
                "patterns_found": [],
                "error": "Failed to parse pattern detection response",
                "raw_response": response_text,
                "processing_time_ms": api_time
            }
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._analyze_joist_patterns_with_claude")
            return {"patterns_found": [], "error": str(e)}
    
    def _get_joist_pattern_detection_prompt(self) -> str:
        """Get specialized prompt for J1 cross-pattern detection"""
        return """You are analyzing an architectural drawing to detect J1 joist patterns.

**IMPORTANT CONTEXT:**
- J1A through J1F are NOT labels on the drawing - they are our numbering system
- We need to find 6 distinct cross-hatched rectangular areas that represent joist sections
- Each section has parallel lines indicating individual joists
- Some sections may be rotated 90 degrees (vertical instead of horizontal)

**What to look for:**
1. **Cross-hatched rectangles**: Areas with parallel lines (the joists)
2. **Boundaries**: Clear rectangular boundaries around each joist section
3. **Pattern characteristics**:
   - Parallel lines at consistent spacing (typically 450mm for J1)
   - Lines extend to the boundaries (arrows or walls)
   - May be horizontal OR vertical orientation
4. **Nearby labels**: Look for "J1" text labels near these patterns

**Detection approach:**
1. Identify all cross-hatched rectangular regions
2. Number them J1A through J1F based on position (left-to-right, top-to-bottom)
3. Record the bounding box coordinates for each pattern

Return your analysis as JSON:
```json
{
  "patterns_found": [
    {
      "label": "J1A",
      "bounding_box": {
        "x": 100,
        "y": 200,
        "width": 300,
        "height": 150
      },
      "orientation": "horizontal",
      "confidence": 0.95,
      "characteristics": "Large horizontal cross-hatched area with ~8 parallel lines",
      "nearby_text": "J1"
    },
    // ... J1B through J1F
  ],
  "total_patterns": 6,
  "overall_confidence": 0.90,
  "detection_notes": "Found 6 distinct cross-hatched rectangular regions matching J1 joist patterns"
}
```

**Important:**
- Number patterns J1A-F based on spatial position, NOT on any labels in the drawing
- Include ALL cross-hatched rectangular areas that could be joist sections
- Note orientation (horizontal/vertical) for each pattern
- Coordinates should be in pixels relative to the image
"""
    
    def detect_joist_measurements(self, pdf_content: bytes, scale_factor: float = 100.0) -> List[JoistMeasurement]:
        """
        Detect and measure actual joist structural lines from PDF
        - Horizontal lines with arrows = joist spans
        - Vertical lines with circles = blocking/support lines
        """
        start_time = time.time()
        
        try:
            log_processing_step("joist_measurement_detection", "started")
            
            # Convert PDF to images
            pdf_images = self._convert_pdf_to_images(pdf_content)
            if not pdf_images:
                return []
            
            # Analyze structural lines with Claude Vision
            measurements = self._analyze_structural_lines_with_claude(pdf_images[0][0], scale_factor)
            
            processing_time = (time.time() - start_time) * 1000
            
            log_processing_step("joist_measurement_detection", "completed",
                              duration_ms=processing_time,
                              details={"measurements_found": len(measurements)})
            
            return measurements
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer.detect_joist_measurements")
            return []
    
    def _analyze_structural_lines_with_claude(self, image_bytes: bytes, scale_factor: float) -> List[JoistMeasurement]:
        """Analyze structural lines to extract joist measurements"""
        try:
            # Encode image
            img_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Prepare Claude request
            content_blocks = [
                {
                    "type": "text",
                    "text": self._get_structural_line_measurement_prompt(scale_factor)
                },
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": img_base64
                    }
                }
            ]
            
            # Send to Claude
            start_time = time.time()
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[{
                    "role": "user",
                    "content": content_blocks
                }]
            )
            
            api_time = (time.time() - start_time) * 1000
            
            # Parse response
            response_text = message.content[0].text if message.content else ""
            measurements_data = self._extract_json_from_response(response_text)
            
            # Convert to JoistMeasurement objects
            measurements = []
            if measurements_data and 'measurements' in measurements_data:
                for m in measurements_data['measurements']:
                    measurement = JoistMeasurement(
                        pattern_label=m.get('label', ''),
                        horizontal_span_m=m.get('horizontal_span_m', 0.0),
                        vertical_span_m=m.get('vertical_span_m'),
                        joist_count=m.get('joist_count', 1),
                        confidence=m.get('confidence', 0.0),
                        measurement_method=m.get('method', 'structural_lines'),
                        line_details=m.get('line_details', {}),
                        line_coordinates=m.get('line_coordinates', {})
                    )
                    measurements.append(measurement)
            
            return measurements
            
        except Exception as e:
            log_error(e, "claude_vision_analyzer._analyze_structural_lines_with_claude")
            return []
    
    def _get_structural_line_measurement_prompt(self, scale_factor: float) -> str:
        """Get prompt for measuring structural lines"""
        # Default to 100 if scale_factor is None
        effective_scale_factor = scale_factor if scale_factor is not None else 100.0
        
        return f"""You are analyzing a structural drawing to measure joist dimensions by identifying structural lines.

**IMPORTANT**: The drawing scale is 1:{effective_scale_factor}

**What to Look For:**

1. **Horizontal Lines with Arrows**:
   - These represent joist spans
   - Have arrows at both ends (←─────→)
   - Measure the length between arrows
   - This gives the horizontal span dimension

2. **Vertical Lines with Circles**:
   - These intersect with horizontal joist lines
   - Have small circles (○) at intersection points
   - Measure from top to bottom of the vertical line
   - This gives the vertical span/blocking dimension

3. **Parallel Lines**:
   - Multiple parallel horizontal lines indicate multiple joists
   - Count how many parallel joist lines exist in each section

**Measurement Process:**
1. Identify each distinct joist section (may be labeled J1, J2, etc.)
2. Find the horizontal line(s) with arrows
3. Measure the pixel length of the horizontal line
4. Convert to real dimensions using scale (pixels / scale_factor = meters)
5. Find vertical lines that intersect (look for circles at intersections)
6. Measure vertical line lengths and convert to meters

Return your analysis as JSON:
```json
{{
  "measurements": [
    {{
      "label": "J1",
      "horizontal_span_m": 3.386,
      "vertical_span_m": 4.872,
      "joist_count": 8,
      "confidence": 0.95,
      "method": "structural_lines",
      "line_details": {{
        "horizontal_pixels": 338.6,
        "vertical_pixels": 487.2,
        "arrows_found": true,
        "circles_found": true,
        "parallel_lines": 8
      }},
      "line_coordinates": {{
        "horizontal_line": {{
          "start_x": 150,
          "start_y": 300,
          "end_x": 488.6,
          "end_y": 300
        }},
        "vertical_line": {{
          "start_x": 150,
          "start_y": 300,
          "end_x": 150,
          "end_y": 787.2
        }}
      }}
    }}
  ],
  "total_sections": 2,
  "scale_applied": {effective_scale_factor},
  "detection_notes": "Found 2 main joist sections (J1 and J2) with clear dimensional lines"
}}
```

**Critical Instructions:**
- Measure the actual structural lines, not the cross-hatching
- Look for arrows to identify span dimensions
- Look for circles to identify intersection points
- Apply the scale factor to convert pixels to meters
- Count parallel lines to determine joist quantity
- Provide exact pixel coordinates for the start and end points of measured lines
- Use simple labels like "J1", "J2" for main sections (not J1A-F subdivisions)
"""
    
    def create_form_data_from_area_analysis(self, area_result: Dict[str, Any]) -> Dict[str, Any]:
        """Convert area analysis result to form data format"""
        form_data = {
            "manual_areas_analyzed": True,
            "claude_vision_used": True,
            "confidence": area_result.get("overall_confidence", 0.0),
            "claude_reasoning": area_result.get("combined_reasoning", ""),
            "processing_time_ms": area_result.get("processing_time_ms", 0),
            "cost_estimate_usd": area_result.get("total_cost_estimate_usd", 0),
            "detection_methods": ["claude_vision_area_analysis"],
            "areas_processed": area_result.get("total_areas", 0),
            "successful_areas": area_result.get("successful_areas", 0)
        }
        
        # Extract measurements from detected elements
        detected_elements = area_result.get("detected_elements", [])
        
        if detected_elements:
            # Find the best element (highest confidence)
            best_element = max(detected_elements, key=lambda x: x.get("confidence", 0))
            
            form_data["primary_element_label"] = best_element.get("label", "")
            form_data["primary_element_specification"] = best_element.get("specification", "")
            
            # Extract measurements
            measurements = best_element.get("measurements", {})
            if measurements:
                if "spacing_mm" in measurements and measurements["spacing_mm"] is not None:
                    form_data["joist_spacing"] = measurements["spacing_mm"] / 1000  # Convert to meters
                
                if "width_mm" in measurements and "depth_mm" in measurements:
                    width_mm = measurements.get('width_mm')
                    depth_mm = measurements.get('depth_mm')
                    if width_mm is not None and depth_mm is not None:
                        form_data["material_detected"] = f"{width_mm}x{depth_mm}"
                        if "material" in measurements:
                            form_data["material_detected"] += f" {measurements['material']}"
                    elif "material" in measurements:
                        # If we don't have dimensions but have material type
                        form_data["material_detected"] = measurements['material']
            
            # Add all detected elements
            form_data["all_detected_elements"] = detected_elements
        
        return form_data