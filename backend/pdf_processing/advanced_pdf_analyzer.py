# Computer vision libraries - optional imports to prevent process death
try:
    import cv2
    import numpy as np
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    from sklearn.cluster import DBSCAN
    from scipy.spatial.distance import euclidean
    CV_AVAILABLE = True
except ImportError as e:
    # These libraries are not needed for current workflow (no Claude Vision)
    # They were causing memory pressure and process death
    CV_AVAILABLE = False
    # Create dummy objects to prevent errors
    np = None

import fitz  # PyMuPDF
import tempfile
import os
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ExtractedText:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    confidence: float
    method: str  # 'native', 'tesseract', 'easyocr', 'visual'
    page_number: int

@dataclass
class DetectedLine:
    start_point: Tuple[float, float]
    end_point: Tuple[float, float]
    angle: float
    length: float
    thickness: float
    confidence: float
    page_number: int

@dataclass
class StructuralElement:
    element_type: str  # 'joist', 'beam', 'dimension_line', 'label'
    bbox: Tuple[float, float, float, float]
    properties: Dict
    confidence: float
    page_number: int

class ImagePreprocessor:
    """Advanced image preprocessing for architectural drawings"""
    
    @staticmethod
    def enhance_image(image: np.ndarray) -> np.ndarray:
        """Apply various enhancements to improve OCR accuracy"""
        # Convert to PIL for easier manipulation
        if len(image.shape) == 3:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        else:
            pil_image = Image.fromarray(image)
        
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.5)
        
        # Enhance sharpness
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Convert back to numpy
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def deskew_image(image: np.ndarray) -> np.ndarray:
        """Correct rotation in scanned documents"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Use Hough Line Transform to detect lines
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is not None:
            angles = []
            for rho, theta in lines[:20]:  # Use first 20 lines
                angle = np.degrees(theta) - 90
                angles.append(angle)
            
            if angles:
                # Find the most common angle
                median_angle = np.median(angles)
                
                # Only correct if angle is significant
                if abs(median_angle) > 1:
                    height, width = gray.shape
                    center = (width // 2, height // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    return cv2.warpAffine(image, rotation_matrix, (width, height), 
                                        flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return image
    
    @staticmethod
    def remove_noise(image: np.ndarray) -> np.ndarray:
        """Remove noise while preserving text and lines"""
        # Apply bilateral filter to reduce noise while keeping edges sharp
        denoised = cv2.bilateralFilter(image, 9, 75, 75)
        return denoised

class ComputerVisionAnalyzer:
    """Computer vision methods for detecting structural elements"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
    
    def detect_lines(self, image: np.ndarray, page_num: int) -> List[DetectedLine]:
        """Detect lines that might represent joists or structural elements"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Edge detection
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Hough Line Transform
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=100, 
                               minLineLength=50, maxLineGap=10)
        
        detected_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line properties
                length = np.sqrt((x2-x1)**2 + (y2-y1)**2)
                angle = np.degrees(np.arctan2(y2-y1, x2-x1))
                
                # Estimate thickness by checking nearby pixels
                thickness = self._estimate_line_thickness(gray, x1, y1, x2, y2)
                
                # Calculate confidence based on length and clarity
                confidence = min(1.0, length / 200.0)  # Longer lines = higher confidence
                
                detected_lines.append(DetectedLine(
                    start_point=(x1, y1),
                    end_point=(x2, y2),
                    angle=angle,
                    length=length,
                    thickness=thickness,
                    confidence=confidence,
                    page_number=page_num
                ))
        
        return detected_lines
    
    def _estimate_line_thickness(self, gray_image: np.ndarray, x1: int, y1: int, x2: int, y2: int) -> float:
        """Estimate the thickness of a detected line"""
        # Simple approach: sample perpendicular to the line
        try:
            mid_x, mid_y = (x1 + x2) // 2, (y1 + y2) // 2
            
            # Get perpendicular direction
            dx, dy = x2 - x1, y2 - y1
            length = np.sqrt(dx**2 + dy**2)
            if length == 0:
                return 1.0
            
            perp_dx, perp_dy = -dy/length, dx/length
            
            # Sample along perpendicular
            thickness = 1.0
            for i in range(1, 10):
                px1 = int(mid_x + i * perp_dx)
                py1 = int(mid_y + i * perp_dy)
                px2 = int(mid_x - i * perp_dx)
                py2 = int(mid_y - i * perp_dy)
                
                if (0 <= px1 < gray_image.shape[1] and 0 <= py1 < gray_image.shape[0] and
                    0 <= px2 < gray_image.shape[1] and 0 <= py2 < gray_image.shape[0]):
                    
                    if gray_image[py1, px1] < 128 or gray_image[py2, px2] < 128:
                        thickness = i
                    else:
                        break
            
            return float(thickness)
        except:
            return 1.0
    
    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect regions likely to contain text"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Use morphological operations to find text-like regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        # Apply closing to connect nearby text
        closed = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        text_regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter by size (likely text dimensions)
            if 10 < w < 200 and 5 < h < 50:
                text_regions.append((x, y, x+w, y+h))
        
        return text_regions

class AdvancedPDFAnalyzer:
    """Advanced PDF analyzer with OCR, computer vision, and multi-method extraction"""
    
    def __init__(self):
        self.preprocessor = ImagePreprocessor()
        self.cv_analyzer = ComputerVisionAnalyzer()
        self.easyocr_reader = None
        self._initialize_ocr()
    
    def _initialize_ocr(self):
        """Initialize OCR engines"""
        # Lazy load EasyOCR - will be initialized on first use
        self.easyocr_reader = None
        logger.info("OCR initialization deferred for faster startup")
    
    def analyze_pdf_advanced(self, pdf_content: bytes) -> Dict:
        """Comprehensive PDF analysis using multiple methods"""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            pdf_doc = fitz.open(temp_file_path)
            
            analysis_result = {
                "page_count": pdf_doc.page_count,
                "extracted_text": [],
                "detected_lines": [],
                "structural_elements": [],
                "extraction_methods": [],
                "overall_confidence": 0.0,
                "processing_log": []
            }
            
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                
                # Method 1: Native text extraction
                native_text = self._extract_native_text(page, page_num)
                analysis_result["extracted_text"].extend(native_text)
                
                # Method 2: Convert to image for OCR and CV analysis
                page_image = self._pdf_page_to_image(page)
                
                if page_image is not None:
                    # Preprocess image
                    enhanced_image = self.preprocessor.enhance_image(page_image)
                    deskewed_image = self.preprocessor.deskew_image(enhanced_image)
                    clean_image = self.preprocessor.remove_noise(deskewed_image)
                    
                    # Method 3: Tesseract OCR
                    tesseract_text = self._extract_tesseract_text(clean_image, page_num)
                    analysis_result["extracted_text"].extend(tesseract_text)
                    
                    # Method 4: EasyOCR
                    if self.easyocr_reader:
                        easyocr_text = self._extract_easyocr_text(clean_image, page_num)
                        analysis_result["extracted_text"].extend(easyocr_text)
                    
                    # Method 5: Computer vision line detection
                    detected_lines = self.cv_analyzer.detect_lines(clean_image, page_num)
                    analysis_result["detected_lines"].extend(detected_lines)
                    
                    analysis_result["processing_log"].append(f"Page {page_num + 1}: Processed with all methods")
                else:
                    analysis_result["processing_log"].append(f"Page {page_num + 1}: Image conversion failed")
            
            # Calculate overall confidence
            if analysis_result["extracted_text"]:
                avg_confidence = np.mean([text.confidence for text in analysis_result["extracted_text"]])
                analysis_result["overall_confidence"] = avg_confidence
            
            # Record which methods were used
            analysis_result["extraction_methods"] = ["native", "tesseract", "easyocr", "computer_vision"]
            
            pdf_doc.close()
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in advanced PDF analysis: {e}")
            return {
                "error": str(e),
                "page_count": 0,
                "extracted_text": [],
                "detected_lines": [],
                "structural_elements": [],
                "extraction_methods": [],
                "overall_confidence": 0.0,
                "processing_log": [f"Critical error: {e}"]
            }
        finally:
            os.unlink(temp_file_path)
    
    def _extract_native_text(self, page: fitz.Page, page_num: int) -> List[ExtractedText]:
        """Extract text using PyMuPDF's native method"""
        extracted_text = []
        
        try:
            text_dict = page.get_text("dict")
            
            for block in text_dict["blocks"]:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                extracted_text.append(ExtractedText(
                                    text=text,
                                    bbox=span["bbox"],
                                    confidence=1.0,  # Native extraction is reliable
                                    method="native",
                                    page_number=page_num
                                ))
        except Exception as e:
            logger.warning(f"Native text extraction failed for page {page_num}: {e}")
        
        return extracted_text
    
    def _pdf_page_to_image(self, page: fitz.Page, dpi: int = 300) -> Optional[np.ndarray]:
        """Convert PDF page to image for OCR processing"""
        try:
            # Render page as image
            mat = fitz.Matrix(dpi/72, dpi/72)  # Scale factor for DPI
            pix = page.get_pixmap(matrix=mat)
            
            # Convert to numpy array
            img_data = pix.tobytes("ppm")
            nparr = np.frombuffer(img_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            return image
        except Exception as e:
            logger.warning(f"Failed to convert page to image: {e}")
            return None
    
    def _extract_tesseract_text(self, image: np.ndarray, page_num: int) -> List[ExtractedText]:
        """Extract text using Tesseract OCR"""
        extracted_text = []
        
        try:
            # Convert to grayscale for OCR
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(gray, output_type=pytesseract.Output.DICT)
            
            n_boxes = len(ocr_data['level'])
            for i in range(n_boxes):
                confidence = float(ocr_data['conf'][i])
                text = str(ocr_data['text'][i]).strip()
                
                if confidence > 30 and text:  # Filter low confidence results
                    x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i], 
                                 ocr_data['width'][i], ocr_data['height'][i])
                    
                    extracted_text.append(ExtractedText(
                        text=text,
                        bbox=(x, y, x+w, y+h),
                        confidence=confidence / 100.0,  # Normalize to 0-1
                        method="tesseract",
                        page_number=page_num
                    ))
                    
        except Exception as e:
            logger.warning(f"Tesseract OCR failed for page {page_num}: {e}")
        
        return extracted_text
    
    def _extract_easyocr_text(self, image: np.ndarray, page_num: int) -> List[ExtractedText]:
        """Extract text using EasyOCR"""
        extracted_text = []
        
        try:
            # Lazy load EasyOCR on first use
            if self.easyocr_reader is None:
                try:
                    logger.info("Lazy loading EasyOCR (this may take a moment on first use)...")
                    import easyocr
                    self.easyocr_reader = easyocr.Reader(['en'])
                    logger.info("EasyOCR loaded successfully")
                except Exception as e:
                    logger.warning(f"Failed to initialize EasyOCR: {e}")
                    return extracted_text
            
            # EasyOCR expects RGB format
            if len(image.shape) == 3:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            
            results = self.easyocr_reader.readtext(rgb_image)
            
            for result in results:
                bbox_points, text, confidence = result
                
                if confidence > 0.3 and text.strip():  # Filter low confidence
                    # Convert bbox points to x0, y0, x1, y1 format
                    xs = [point[0] for point in bbox_points]
                    ys = [point[1] for point in bbox_points]
                    bbox = (min(xs), min(ys), max(xs), max(ys))
                    
                    extracted_text.append(ExtractedText(
                        text=text.strip(),
                        bbox=bbox,
                        confidence=confidence,
                        method="easyocr",
                        page_number=page_num
                    ))
                    
        except Exception as e:
            logger.warning(f"EasyOCR failed for page {page_num}: {e}")
        
        return extracted_text
    
    def find_joist_elements(self, analysis_result: Dict) -> List[StructuralElement]:
        """Find joist-related elements using advanced pattern recognition"""
        joist_elements = []
        
        # Combine all extracted text
        all_text = analysis_result.get("extracted_text", [])
        detected_lines = analysis_result.get("detected_lines", [])
        
        # Pattern matching for joist labels with fuzzy matching
        joist_patterns = [
            r'\b(J\d+)\b',
            r'\b(JOIST\s*\d+)\b',
            r'\b(j\d+)\b',
            r'\b([Jj]oist\s*\d+)\b'
        ]
        
        for text_item in all_text:
            for pattern in joist_patterns:
                matches = re.findall(pattern, text_item.text, re.IGNORECASE)
                for match in matches:
                    # Create structural element for joist label
                    joist_elements.append(StructuralElement(
                        element_type="joist_label",
                        bbox=text_item.bbox,
                        properties={
                            "label": match,
                            "text": text_item.text,
                            "extraction_method": text_item.method
                        },
                        confidence=text_item.confidence,
                        page_number=text_item.page_number
                    ))
        
        # Analyze detected lines for potential joists
        horizontal_lines = [line for line in detected_lines 
                          if abs(line.angle) < 15 or abs(abs(line.angle) - 180) < 15]
        
        if horizontal_lines:
            # Cluster parallel lines (potential joists)
            line_positions = [(line.start_point[1] + line.end_point[1])/2 for line in horizontal_lines]
            
            if len(line_positions) > 1:
                # Simple clustering by y-position
                clusters = self._cluster_parallel_lines(horizontal_lines)
                
                for cluster in clusters:
                    if len(cluster) > 2:  # Multiple parallel lines suggest joists
                        avg_confidence = np.mean([line.confidence for line in cluster])
                        
                        # Calculate bounding box for the cluster
                        all_x = []
                        all_y = []
                        for line in cluster:
                            all_x.extend([line.start_point[0], line.end_point[0]])
                            all_y.extend([line.start_point[1], line.end_point[1]])
                        
                        bbox = (min(all_x), min(all_y), max(all_x), max(all_y))
                        
                        joist_elements.append(StructuralElement(
                            element_type="joist_lines",
                            bbox=bbox,
                            properties={
                                "line_count": len(cluster),
                                "avg_spacing": self._calculate_line_spacing(cluster),
                                "avg_angle": np.mean([line.angle for line in cluster])
                            },
                            confidence=avg_confidence,
                            page_number=cluster[0].page_number
                        ))
        
        return joist_elements
    
    def _cluster_parallel_lines(self, lines: List[DetectedLine], max_distance: float = 50.0) -> List[List[DetectedLine]]:
        """Cluster parallel lines that might represent joists"""
        if len(lines) < 2:
            return [lines] if lines else []
        
        # Use y-coordinates of line centers for clustering
        positions = np.array([[(line.start_point[1] + line.end_point[1])/2] for line in lines])
        
        # DBSCAN clustering
        clustering = DBSCAN(eps=max_distance, min_samples=2).fit(positions)
        
        clusters = []
        for cluster_id in set(clustering.labels_):
            if cluster_id != -1:  # Ignore noise points
                cluster_lines = [lines[i] for i, label in enumerate(clustering.labels_) if label == cluster_id]
                clusters.append(cluster_lines)
        
        return clusters
    
    def _calculate_line_spacing(self, lines: List[DetectedLine]) -> float:
        """Calculate average spacing between parallel lines"""
        if len(lines) < 2:
            return 0.0
        
        y_positions = sorted([(line.start_point[1] + line.end_point[1])/2 for line in lines])
        spacings = [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
        
        return np.mean(spacings) if spacings else 0.0