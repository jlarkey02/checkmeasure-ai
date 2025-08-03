import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .pdf_analyzer import PDFAnalyzer, TextBlock
import fitz

@dataclass
class JoistLabel:
    label: str  # e.g., "J1", "J2"
    specification: str  # e.g., "200 x 45 LVL at 450 centres"
    dimensions: Dict[str, float]  # parsed dimensions
    bbox: Tuple[float, float, float, float]
    page_number: int
    confidence: float

@dataclass
class JoistSpecification:
    width: float  # mm
    depth: float  # mm
    material_type: str  # "LVL", "MGP10", etc.
    spacing: float  # mm
    grade: Optional[str] = None

class JoistDetector:
    def __init__(self):
        self.pdf_analyzer = PDFAnalyzer()
        
        # Patterns for joist labels (case insensitive, flexible spacing)
        self.joist_label_patterns = [
            r'\b(J\d+)\b',  # J1, J2, J3, etc. (word boundary)
            r'\b(j\d+)\b',  # j1, j2, j3, etc. (lowercase)
            r'\b(JOIST\s*\d+)\b',  # JOIST 1, JOIST 2, etc.
            r'\b(joist\s*\d+)\b',  # joist 1, joist 2, etc.
            r'\b(Joist\s*\d+)\b',  # Joist 1, Joist 2, etc.
            r'\b(J-\d+)\b',  # J-1, J-2, etc.
            r'\b(j-\d+)\b',  # j-1, j-2, etc.
            r'\b(J\s+\d+)\b',  # J 1, J 2, etc. (with space)
        ]
        
        # Patterns for joist specifications (case insensitive, flexible)
        self.specification_patterns = [
            # Pattern: "200 x 45 LVL at 450 centres" (flexible spacing/punctuation)
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*)\s*(?:timber\s*)?(?:beams?\s*)?(?:at|@|AT)\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?)',
            # Pattern: "200/45 LVL timber beams at 450 centres"
            r'(\d+)\s*[/]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*)\s*(?:timber\s*)?(?:beams?\s*)?(?:at|@|AT)\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?)',
            # Pattern: "200x45 LVL 450 centres" (missing "at")
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*)\s*(?:timber\s*)?(?:beams?\s*)?\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?)',
            # Pattern: Just dimensions and material (relaxed)
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*)',
            # Pattern: Spacing only near joist label
            r'(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?)',
        ]
        
        # Material type mappings
        self.material_mappings = {
            'LVL': 'Laminated Veneer Lumber',
            'MGP10': 'Machine Graded Pine 10',
            'MGP12': 'Machine Graded Pine 12',
            'F5': 'Seasoned Hardwood F5',
            'F7': 'Seasoned Hardwood F7',
            'F8': 'Seasoned Hardwood F8',
        }
    
    def detect_joist_labels(self, pdf_content: bytes) -> List[JoistLabel]:
        """
        Detect joist labels and their specifications in PDF content
        """
        # First, analyze the PDF to get text blocks
        analysis = self.pdf_analyzer.analyze_pdf(pdf_content)
        text_blocks = analysis['text_blocks']
        
        joist_labels = []
        
        # Group text blocks by proximity to find label-specification pairs
        for i, text_block in enumerate(text_blocks):
            # Check if this text block contains a joist label
            label_match = self._find_joist_label(text_block.text)
            
            if label_match:
                # Look for specification in nearby text blocks
                specification = self._find_nearby_specification(
                    text_blocks, i, text_block
                )
                
                if specification:
                    # Parse the specification
                    parsed_spec = self._parse_specification(specification['text'])
                    
                    if parsed_spec:
                        joist_labels.append(JoistLabel(
                            label=label_match,
                            specification=specification['text'],
                            dimensions=parsed_spec,
                            bbox=text_block.bbox,
                            page_number=text_block.page_number,
                            confidence=specification['confidence']
                        ))
        
        return joist_labels
    
    def _find_joist_label(self, text: str) -> Optional[str]:
        """Find joist label in text (e.g., J1, J2)"""
        for pattern in self.joist_label_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        return None
    
    def _find_nearby_specification(self, text_blocks: List[TextBlock], 
                                 current_index: int, 
                                 label_block: TextBlock) -> Optional[Dict]:
        """
        Find specification text near a joist label
        """
        search_radius = 150  # pixels
        best_match = None
        best_confidence = 0
        
        # Search in nearby text blocks
        for i in range(max(0, current_index - 5), 
                      min(len(text_blocks), current_index + 6)):
            if i == current_index:
                continue
                
            block = text_blocks[i]
            
            # Check if blocks are on the same page
            if block.page_number != label_block.page_number:
                continue
            
            # Calculate distance between blocks
            distance = self._calculate_distance(label_block.bbox, block.bbox)
            
            if distance <= search_radius:
                # Check if this block contains a specification
                spec_match = self._find_specification_in_text(block.text)
                
                if spec_match:
                    # Calculate confidence based on distance and text quality
                    confidence = max(0.1, 1.0 - (distance / search_radius))
                    
                    if confidence > best_confidence:
                        best_match = {
                            'text': spec_match,
                            'confidence': confidence,
                            'block': block
                        }
                        best_confidence = confidence
        
        return best_match
    
    def _find_specification_in_text(self, text: str) -> Optional[str]:
        """Find joist specification in text"""
        for pattern in self.specification_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0)
        return None
    
    def _parse_specification(self, spec_text: str) -> Optional[Dict[str, float]]:
        """
        Parse joist specification text into structured data
        """
        for i, pattern in enumerate(self.specification_patterns):
            match = re.search(pattern, spec_text, re.IGNORECASE)
            
            if match:
                try:
                    # Handle different pattern types
                    if i <= 2:  # Full specification patterns (width x depth material at spacing)
                        width = float(match.group(1))
                        depth = float(match.group(2))
                        material = match.group(3).upper()
                        spacing = float(match.group(4))
                        
                        return {
                            'width_mm': width,
                            'depth_mm': depth,
                            'material_type': material,
                            'spacing_mm': spacing,
                            'material_description': self.material_mappings.get(material, material)
                        }
                    elif i == 3:  # Just dimensions and material
                        width = float(match.group(1))
                        depth = float(match.group(2))
                        material = match.group(3).upper()
                        
                        return {
                            'width_mm': width,
                            'depth_mm': depth,
                            'material_type': material,
                            'spacing_mm': None,  # Will need to find elsewhere
                            'material_description': self.material_mappings.get(material, material)
                        }
                    elif i == 4:  # Just spacing
                        spacing = float(match.group(1))
                        
                        return {
                            'width_mm': None,
                            'depth_mm': None,
                            'material_type': None,
                            'spacing_mm': spacing,
                            'material_description': None
                        }
                        
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _calculate_distance(self, bbox1: Tuple[float, float, float, float], 
                          bbox2: Tuple[float, float, float, float]) -> float:
        """Calculate distance between two bounding boxes"""
        # Get center points
        center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
        center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)
        
        # Calculate Euclidean distance
        return ((center1[0] - center2[0]) ** 2 + (center1[1] - center2[1]) ** 2) ** 0.5
    
    def extract_joist_measurements(self, pdf_content: bytes, 
                                 joist_label: str) -> Optional[Dict]:
        """
        Extract span measurements for a specific joist label
        """
        # Detect all joist labels first
        joist_labels = self.detect_joist_labels(pdf_content)
        
        # Find the specific joist label
        target_joist = None
        for joist in joist_labels:
            if joist.label.upper() == joist_label.upper():
                target_joist = joist
                break
        
        if not target_joist:
            return None
        
        # Extract measurements around the joist label area
        analysis = self.pdf_analyzer.analyze_pdf(pdf_content)
        
        # Look for dimensions near the joist label
        nearby_dimensions = []
        search_radius = 200  # pixels
        
        for dimension in analysis['dimensions']:
            if dimension.page_number == target_joist.page_number:
                distance = self._calculate_distance(
                    target_joist.bbox, 
                    dimension.bbox
                )
                
                if distance <= search_radius:
                    nearby_dimensions.append({
                        'value': dimension.value,
                        'unit': dimension.unit,
                        'distance': distance,
                        'text': dimension.text
                    })
        
        # Sort by distance and return the closest dimensions
        nearby_dimensions.sort(key=lambda x: x['distance'])
        
        return {
            'joist_label': target_joist.label,
            'specification': target_joist.dimensions,
            'nearby_measurements': nearby_dimensions[:5],  # Top 5 closest
            'suggested_span': self._suggest_span_length(nearby_dimensions),
            'confidence': target_joist.confidence
        }
    
    def _suggest_span_length(self, dimensions: List[Dict]) -> Optional[Dict]:
        """
        Suggest the most likely span length from nearby dimensions
        """
        if not dimensions:
            return None
        
        # Look for dimensions that are likely to be span lengths
        # (typically between 1m and 10m for residential construction)
        span_candidates = []
        
        for dim in dimensions:
            value_in_meters = self.pdf_analyzer.convert_to_meters(
                dim['value'], dim['unit']
            )
            
            # Filter for reasonable span lengths
            if 1.0 <= value_in_meters <= 10.0:
                span_candidates.append({
                    'value_meters': value_in_meters,
                    'original_value': dim['value'],
                    'unit': dim['unit'],
                    'text': dim['text'],
                    'distance': dim['distance']
                })
        
        if span_candidates:
            # Return the closest reasonable span
            return span_candidates[0]
        
        return None
    
    def auto_populate_calculation_form(self, pdf_content: bytes) -> Dict:
        """
        Automatically populate calculation form based on detected joist labels
        """
        joist_labels = self.detect_joist_labels(pdf_content)
        
        if not joist_labels:
            return {'error': 'No joist labels detected in PDF'}
        
        # Take the first detected joist as primary
        primary_joist = joist_labels[0]
        
        # Extract measurements for this joist
        measurements = self.extract_joist_measurements(
            pdf_content, primary_joist.label
        )
        
        if not measurements:
            return {'error': 'Could not extract measurements for detected joist'}
        
        # Build form data
        form_data = {
            'detected_joists': len(joist_labels),
            'primary_joist_label': primary_joist.label,
            'auto_populated': True
        }
        
        # Add specification data
        spec = primary_joist.dimensions
        if spec:
            # Safe conversion to meters with null checks
            spacing_mm = spec.get('spacing_mm')
            if spacing_mm is not None:
                form_data['joist_spacing'] = spacing_mm / 1000
            
            width_mm = spec.get('width_mm')
            depth_mm = spec.get('depth_mm')
            material_type = spec.get('material_type')
            
            if width_mm and depth_mm and material_type:
                form_data['material_detected'] = f"{width_mm}x{depth_mm} {material_type}"
            
            material_desc = spec.get('material_description')
            if material_desc:
                form_data['material_specification'] = material_desc
        
        # Add span length if detected
        if measurements['suggested_span']:
            form_data['span_length'] = measurements['suggested_span']['value_meters']
        
        # Add confidence and detection details
        form_data.update({
            'confidence': primary_joist.confidence,
            'all_detected_joists': [
                {
                    'label': j.label,
                    'specification': j.specification,
                    'confidence': j.confidence
                } for j in joist_labels
            ]
        })
        
        return form_data