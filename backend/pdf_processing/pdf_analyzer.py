import fitz  # PyMuPDF
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import tempfile
import os

@dataclass
class TextBlock:
    text: str
    bbox: Tuple[float, float, float, float]  # x0, y0, x1, y1
    page_number: int
    font_size: float
    confidence: float = 1.0

@dataclass
class Dimension:
    value: float
    unit: str
    text: str
    bbox: Tuple[float, float, float, float]
    page_number: int

class PDFAnalyzer:
    def __init__(self):
        self.dimension_patterns = [
            r'(\d+\.?\d*)\s*m',  # meters
            r'(\d+\.?\d*)\s*mm',  # millimeters
            r'(\d+\.?\d*)\s*cm',  # centimeters
            r'(\d+)-(\d+)',  # room dimensions like 3-4
            r'(\d+\.?\d*)\s*x\s*(\d+\.?\d*)',  # dimensions like 3.5 x 4.2
        ]
        
        self.scale_patterns = [
            r'1:(\d+)',  # scale patterns like 1:100
            r'SCALE\s*1:(\d+)',
            r'(\d+)\s*mm\s*=\s*(\d+)\s*m',
        ]
    
    def analyze_pdf(self, pdf_content: bytes) -> Dict:
        """
        Analyze PDF content and extract text, dimensions, and scale information
        """
        # Save PDF content to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            # Open PDF with PyMuPDF
            pdf_doc = fitz.open(temp_file_path)
            
            analysis_result = {
                "page_count": pdf_doc.page_count,
                "scale": None,
                "dimensions": [],
                "text_blocks": [],
                "page_info": {}
            }
            
            # Process each page
            for page_num in range(pdf_doc.page_count):
                page = pdf_doc[page_num]
                
                # Extract text blocks
                text_blocks = self._extract_text_blocks(page, page_num)
                analysis_result["text_blocks"].extend(text_blocks)
                
                # Extract dimensions
                dimensions = self._extract_dimensions(text_blocks)
                analysis_result["dimensions"].extend(dimensions)
                
                # Extract scale information
                scale = self._extract_scale(text_blocks)
                if scale and not analysis_result["scale"]:
                    analysis_result["scale"] = scale
                
                # Store page information
                analysis_result["page_info"][page_num] = {
                    "width": page.rect.width,
                    "height": page.rect.height,
                    "rotation": page.rotation
                }
            
            pdf_doc.close()
            return analysis_result
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
    
    def _extract_text_blocks(self, page: fitz.Page, page_num: int) -> List[TextBlock]:
        """Extract text blocks from a PDF page"""
        text_blocks = []
        
        # Get text with formatting information
        text_dict = page.get_text("dict")
        
        for block in text_dict["blocks"]:
            if "lines" in block:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text:
                            text_blocks.append(TextBlock(
                                text=text,
                                bbox=span["bbox"],
                                page_number=page_num,
                                font_size=span["size"]
                            ))
        
        return text_blocks
    
    def _extract_dimensions(self, text_blocks: List[TextBlock]) -> List[Dimension]:
        """Extract dimension information from text blocks"""
        dimensions = []
        
        for text_block in text_blocks:
            text = text_block.text
            
            # Try each dimension pattern
            for pattern in self.dimension_patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    if pattern.count('(') == 1:  # Single dimension
                        value = float(match.group(1))
                        unit = self._extract_unit(text, match)
                        
                        dimensions.append(Dimension(
                            value=value,
                            unit=unit,
                            text=match.group(0),
                            bbox=text_block.bbox,
                            page_number=text_block.page_number
                        ))
                    
                    elif pattern.count('(') == 2:  # Two dimensions (e.g., 3.5 x 4.2)
                        value1 = float(match.group(1))
                        value2 = float(match.group(2))
                        unit = self._extract_unit(text, match)
                        
                        dimensions.extend([
                            Dimension(
                                value=value1,
                                unit=unit,
                                text=match.group(0),
                                bbox=text_block.bbox,
                                page_number=text_block.page_number
                            ),
                            Dimension(
                                value=value2,
                                unit=unit,
                                text=match.group(0),
                                bbox=text_block.bbox,
                                page_number=text_block.page_number
                            )
                        ])
        
        return dimensions
    
    def _extract_unit(self, text: str, match: re.Match) -> str:
        """Extract unit from dimension text"""
        if 'mm' in text:
            return 'mm'
        elif 'cm' in text:
            return 'cm'
        elif 'm' in text:
            return 'm'
        else:
            return 'm'  # Default to meters
    
    def _extract_scale(self, text_blocks: List[TextBlock]) -> Optional[str]:
        """Extract scale information from text blocks"""
        for text_block in text_blocks:
            text = text_block.text
            
            for pattern in self.scale_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    if pattern.startswith('1:'):
                        return f"1:{match.group(1)}"
                    elif 'SCALE' in pattern:
                        return f"1:{match.group(1)}"
                    elif 'mm' in pattern:
                        # Convert mm to m scale
                        mm_value = float(match.group(1))
                        m_value = float(match.group(2))
                        scale_factor = (m_value * 1000) / mm_value
                        return f"1:{int(scale_factor)}"
        
        return None
    
    def extract_from_area(self, pdf_content: bytes, selection_area: Dict) -> Dict:
        """
        Extract measurements from a specific area of the PDF
        """
        # Save PDF content to temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_file.write(pdf_content)
            temp_file_path = temp_file.name
        
        try:
            pdf_doc = fitz.open(temp_file_path)
            page = pdf_doc[selection_area["page_number"]]
            
            # Create rectangle for selection area
            rect = fitz.Rect(
                selection_area["x"],
                selection_area["y"],
                selection_area["x"] + selection_area["width"],
                selection_area["y"] + selection_area["height"]
            )
            
            # Extract text from the selected area
            text_in_area = page.get_text("text", clip=rect)
            
            # Extract dimensions from the selected text
            text_blocks = [TextBlock(
                text=text_in_area,
                bbox=(rect.x0, rect.y0, rect.x1, rect.y1),
                page_number=selection_area["page_number"],
                font_size=12.0  # Default font size
            )]
            
            dimensions = self._extract_dimensions(text_blocks)
            
            pdf_doc.close()
            
            return {
                "measurements": [
                    {
                        "value": dim.value,
                        "unit": dim.unit,
                        "text": dim.text,
                        "bbox": dim.bbox
                    } for dim in dimensions
                ],
                "extracted_text": text_in_area,
                "confidence": 0.8,  # Default confidence
                "calculation_type": selection_area.get("calculation_type", "unknown")
            }
            
        finally:
            os.unlink(temp_file_path)
    
    def convert_to_meters(self, value: float, unit: str) -> float:
        """Convert dimension value to meters"""
        conversion_factors = {
            'mm': 0.001,
            'cm': 0.01,
            'm': 1.0,
            'ft': 0.3048,
            'in': 0.0254
        }
        
        return value * conversion_factors.get(unit, 1.0)
    
    def apply_scale(self, drawing_dimension: float, scale: str) -> float:
        """
        Apply drawing scale to get real-world dimension
        scale format: "1:100" means 1 unit on drawing = 100 units in real world
        """
        if not scale or not scale.startswith('1:'):
            return drawing_dimension
        
        try:
            scale_factor = int(scale.split(':')[1])
            return drawing_dimension * scale_factor
        except (ValueError, IndexError):
            return drawing_dimension