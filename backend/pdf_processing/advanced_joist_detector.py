import re
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .advanced_pdf_analyzer import AdvancedPDFAnalyzer, ExtractedText, DetectedLine, StructuralElement
import logging

logger = logging.getLogger(__name__)

@dataclass
class AdvancedJoistLabel:
    label: str
    specification: str
    dimensions: Dict[str, float]
    bbox: Tuple[float, float, float, float]
    page_number: int
    confidence: float
    detection_methods: List[str]  # Which methods found this joist
    spatial_elements: Dict  # Related lines, measurements, etc.

@dataclass
class JoistSpecification:
    width_mm: Optional[float] = None
    depth_mm: Optional[float] = None
    material_type: Optional[str] = None
    spacing_mm: Optional[float] = None
    material_description: Optional[str] = None

class AdvancedJoistDetector:
    """Advanced joist detection using multiple analysis methods"""
    
    def __init__(self):
        self.pdf_analyzer = AdvancedPDFAnalyzer()
        
        # Enhanced joist label patterns
        self.joist_label_patterns = [
            r'\b(J\d+)\b',  # J1, J2, J3
            r'\b(j\d+)\b',  # j1, j2, j3
            r'\b(JOIST\s*\d+)\b',  # JOIST 1, JOIST 2
            r'\b(joist\s*\d+)\b',  # joist 1, joist 2
            r'\b(Joist\s*\d+)\b',  # Joist 1, Joist 2
            r'\b(J-\d+)\b',  # J-1, J-2
            r'\b(j-\d+)\b',  # j-1, j-2
            r'\b(J\s+\d+)\b',  # J 1, J 2
        ]
        
        # Enhanced specification patterns
        self.specification_patterns = [
            # Full specifications with dimensions, material, and spacing
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*|PINE|pine|Pine)\s*(?:timber\s*)?(?:beams?\s*)?(?:at|@|AT|spacing|SPACING|centres?|centers?|CENTRES?)\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?|CRS|crs)',
            
            # Specifications with "at" or "@"
            r'(\d+)\s*[x×*/]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*|PINE|pine|Pine)\s*(?:timber\s*)?(?:beams?\s*)?(?:at|@|AT)\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?|CRS|crs)',
            
            # Specifications without "at" (implied spacing)
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*|PINE|pine|Pine)\s*(?:timber\s*)?(?:beams?\s*)?\s*(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?|CRS|crs)',
            
            # Just dimensions and material
            r'(\d+)\s*[x×*]\s*(\d+)\s*(?:mm)?\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*|PINE|pine|Pine)',
            
            # Just spacing information
            r'(\d+)\s*(?:mm)?\s*(?:centres?|centers?|c|C|CENTRES?|CRS|crs|spacing|SPACING)',
            
            # Alternative formats
            r'(\d+)\s*mm\s*[x×*]\s*(\d+)\s*mm\s*(LVL|MGP\d*|F\d*|lvl|mgp\d*|f\d*)',
            
            # Spacing with "o.c." (on center)
            r'(\d+)\s*(?:mm)?\s*(?:o\.c\.|OC|o/c|O/C)',
        ]
        
        # Material mappings
        self.material_mappings = {
            'LVL': 'Laminated Veneer Lumber',
            'lvl': 'Laminated Veneer Lumber',
            'MGP10': 'Machine Graded Pine 10',
            'mgp10': 'Machine Graded Pine 10',
            'MGP12': 'Machine Graded Pine 12',
            'mgp12': 'Machine Graded Pine 12',
            'F5': 'Seasoned Hardwood F5',
            'f5': 'Seasoned Hardwood F5',
            'F7': 'Seasoned Hardwood F7',
            'f7': 'Seasoned Hardwood F7',
            'F8': 'Seasoned Hardwood F8',
            'f8': 'Seasoned Hardwood F8',
            'PINE': 'Pine Timber',
            'pine': 'Pine Timber',
            'Pine': 'Pine Timber',
        }
    
    def detect_joists_advanced(self, pdf_content: bytes) -> List[AdvancedJoistLabel]:
        """Advanced joist detection using multiple methods"""
        # Perform advanced PDF analysis
        analysis_result = self.pdf_analyzer.analyze_pdf_advanced(pdf_content)
        
        if "error" in analysis_result:
            logger.error(f"PDF analysis failed: {analysis_result['error']}")
            return []
        
        # Find structural elements
        structural_elements = self.pdf_analyzer.find_joist_elements(analysis_result)
        
        # Extract joist labels and specifications
        joist_labels = self._extract_joist_information(
            analysis_result["extracted_text"], 
            analysis_result["detected_lines"],
            structural_elements
        )
        
        # Enhance with spatial analysis
        enhanced_joists = self._enhance_with_spatial_analysis(joist_labels, analysis_result)
        
        return enhanced_joists
    
    def _extract_joist_information(self, extracted_text: List[ExtractedText], 
                                 detected_lines: List[DetectedLine],
                                 structural_elements: List[StructuralElement]) -> List[AdvancedJoistLabel]:
        """Extract joist information from multiple data sources"""
        joist_labels = []
        
        # Method 1: Text-based detection
        text_based_joists = self._detect_joists_from_text(extracted_text)
        
        # Method 2: Structural element analysis
        element_based_joists = self._detect_joists_from_elements(structural_elements)
        
        # Method 3: Line pattern analysis
        line_based_joists = self._detect_joists_from_lines(detected_lines, extracted_text)
        
        # Combine and deduplicate
        all_joists = text_based_joists + element_based_joists + line_based_joists
        deduplicated_joists = self._deduplicate_joists(all_joists)
        
        return deduplicated_joists
    
    def _detect_joists_from_text(self, extracted_text: List[ExtractedText]) -> List[AdvancedJoistLabel]:
        """Detect joists from text using pattern matching"""
        joists = []
        
        for text_item in extracted_text:
            # Look for joist labels
            for pattern in self.joist_label_patterns:
                matches = re.findall(pattern, text_item.text, re.IGNORECASE)
                
                for match in matches:
                    # Look for specifications nearby
                    spec_text, spec_confidence = self._find_nearby_specification(
                        text_item.text, extracted_text, text_item
                    )
                    
                    if spec_text:
                        parsed_spec = self._parse_specification_advanced(spec_text)
                        
                        joists.append(AdvancedJoistLabel(
                            label=match.upper(),
                            specification=spec_text,
                            dimensions=parsed_spec,
                            bbox=text_item.bbox,
                            page_number=text_item.page_number,
                            confidence=min(text_item.confidence, spec_confidence),
                            detection_methods=["text_pattern"],
                            spatial_elements={}
                        ))
        
        return joists
    
    def _detect_joists_from_elements(self, structural_elements: List[StructuralElement]) -> List[AdvancedJoistLabel]:
        """Detect joists from structural elements identified by computer vision"""
        joists = []
        
        for element in structural_elements:
            if element.element_type == "joist_label":
                # Convert structural element to joist label
                joists.append(AdvancedJoistLabel(
                    label=element.properties.get("label", "UNKNOWN"),
                    specification=element.properties.get("text", ""),
                    dimensions={},  # Will be filled by specification parsing
                    bbox=element.bbox,
                    page_number=element.page_number,
                    confidence=element.confidence,
                    detection_methods=["computer_vision"],
                    spatial_elements={"element": element}
                ))
            
            elif element.element_type == "joist_lines":
                # Create joist from line patterns
                spacing = element.properties.get("avg_spacing", 0)
                line_count = element.properties.get("line_count", 0)
                
                joists.append(AdvancedJoistLabel(
                    label=f"LINES_{line_count}",
                    specification=f"Detected {line_count} parallel lines with {spacing:.1f}px spacing",
                    dimensions={"spacing_px": spacing, "line_count": line_count},
                    bbox=element.bbox,
                    page_number=element.page_number,
                    confidence=element.confidence,
                    detection_methods=["line_detection"],
                    spatial_elements={"lines": element}
                ))
        
        return joists
    
    def _detect_joists_from_lines(self, detected_lines: List[DetectedLine], 
                                extracted_text: List[ExtractedText]) -> List[AdvancedJoistLabel]:
        """Detect joists by analyzing line patterns and nearby text"""
        joists = []
        
        # Find clusters of parallel horizontal lines
        horizontal_lines = [line for line in detected_lines 
                          if abs(line.angle) < 15 or abs(abs(line.angle) - 180) < 15]
        
        if len(horizontal_lines) >= 3:  # Need at least 3 lines to suggest joists
            # Group lines by proximity and parallelism
            line_clusters = self._cluster_lines_by_proximity(horizontal_lines)
            
            for cluster in line_clusters:
                if len(cluster) >= 3:
                    # Calculate average spacing
                    spacings = self._calculate_line_spacings(cluster)
                    avg_spacing = np.mean(spacings) if spacings else 0
                    
                    # Look for nearby text that might describe these joists
                    cluster_bbox = self._get_cluster_bbox(cluster)
                    nearby_text = self._find_text_near_bbox(cluster_bbox, extracted_text, radius=100)
                    
                    # Try to find joist specifications in nearby text
                    best_spec = ""
                    best_confidence = 0.5
                    
                    for text_item in nearby_text:
                        for pattern in self.specification_patterns:
                            if re.search(pattern, text_item.text, re.IGNORECASE):
                                if text_item.confidence > best_confidence:
                                    best_spec = text_item.text
                                    best_confidence = text_item.confidence
                    
                    parsed_spec = self._parse_specification_advanced(best_spec) if best_spec else {}
                    
                    joists.append(AdvancedJoistLabel(
                        label=f"CV_JOISTS_{len(cluster)}",
                        specification=best_spec or f"Visual detection: {len(cluster)} parallel lines",
                        dimensions=parsed_spec,
                        bbox=cluster_bbox,
                        page_number=cluster[0].page_number,
                        confidence=best_confidence,
                        detection_methods=["computer_vision", "spatial_analysis"],
                        spatial_elements={"line_cluster": cluster, "avg_spacing_px": avg_spacing}
                    ))
        
        return joists
    
    def _find_nearby_specification(self, current_text: str, all_text: List[ExtractedText], 
                                 current_item: ExtractedText, radius: float = 150) -> Tuple[str, float]:
        """Find joist specification text near a joist label"""
        best_spec = ""
        best_confidence = 0.0
        
        # First, check if specification is in the same text block
        for pattern in self.specification_patterns:
            match = re.search(pattern, current_text, re.IGNORECASE)
            if match:
                return current_text, current_item.confidence
        
        # Look in nearby text blocks
        current_center = self._get_bbox_center(current_item.bbox)
        
        for text_item in all_text:
            if text_item == current_item or text_item.page_number != current_item.page_number:
                continue
            
            distance = self._calculate_distance(current_center, self._get_bbox_center(text_item.bbox))
            
            if distance <= radius:
                for pattern in self.specification_patterns:
                    if re.search(pattern, text_item.text, re.IGNORECASE):
                        # Calculate confidence based on distance and text confidence
                        spatial_confidence = max(0.1, 1.0 - (distance / radius))
                        combined_confidence = text_item.confidence * spatial_confidence
                        
                        if combined_confidence > best_confidence:
                            best_spec = text_item.text
                            best_confidence = combined_confidence
        
        return best_spec, best_confidence
    
    def _parse_specification_advanced(self, spec_text: str) -> Dict[str, float]:
        """Advanced specification parsing with multiple pattern support"""
        if not spec_text:
            return {}
        
        result = {}
        
        for i, pattern in enumerate(self.specification_patterns):
            match = re.search(pattern, spec_text, re.IGNORECASE)
            
            if match:
                groups = match.groups()
                
                try:
                    if i <= 2:  # Full specification patterns
                        if len(groups) >= 4:
                            result['width_mm'] = float(groups[0])
                            result['depth_mm'] = float(groups[1])
                            result['material_type'] = groups[2].upper()
                            result['spacing_mm'] = float(groups[3])
                            result['material_description'] = self.material_mappings.get(
                                groups[2].upper(), groups[2]
                            )
                    
                    elif i == 3:  # Just dimensions and material
                        if len(groups) >= 3:
                            result['width_mm'] = float(groups[0])
                            result['depth_mm'] = float(groups[1])
                            result['material_type'] = groups[2].upper()
                            result['material_description'] = self.material_mappings.get(
                                groups[2].upper(), groups[2]
                            )
                    
                    elif i == 4:  # Just spacing
                        result['spacing_mm'] = float(groups[0])
                    
                    elif i == 5:  # Alternative mm format
                        if len(groups) >= 3:
                            result['width_mm'] = float(groups[0])
                            result['depth_mm'] = float(groups[1])
                            result['material_type'] = groups[2].upper()
                    
                    elif i == 6:  # On center spacing
                        result['spacing_mm'] = float(groups[0])
                    
                    break  # Use first matching pattern
                    
                except (ValueError, IndexError) as e:
                    logger.debug(f"Failed to parse specification group: {e}")
                    continue
        
        return result
    
    def _enhance_with_spatial_analysis(self, joist_labels: List[AdvancedJoistLabel], 
                                     analysis_result: Dict) -> List[AdvancedJoistLabel]:
        """Enhance joist detection with spatial relationship analysis"""
        enhanced_joists = []
        
        for joist in joist_labels:
            enhanced_joist = joist
            
            # Try to find related lines near this joist label
            nearby_lines = self._find_lines_near_joist(joist, analysis_result["detected_lines"])
            if nearby_lines:
                enhanced_joist.spatial_elements["nearby_lines"] = nearby_lines
                
                # Calculate potential spacing from lines
                if len(nearby_lines) >= 2:
                    line_spacing = self._calculate_line_spacings(nearby_lines)
                    if line_spacing:
                        avg_spacing_px = np.mean(line_spacing)
                        enhanced_joist.spatial_elements["visual_spacing_px"] = avg_spacing_px
            
            # Try to find related measurements
            nearby_measurements = self._find_measurements_near_joist(joist, analysis_result["extracted_text"])
            if nearby_measurements:
                enhanced_joist.spatial_elements["nearby_measurements"] = nearby_measurements
            
            enhanced_joists.append(enhanced_joist)
        
        return enhanced_joists
    
    def _deduplicate_joists(self, joists: List[AdvancedJoistLabel]) -> List[AdvancedJoistLabel]:
        """Remove duplicate joist detections"""
        if not joists:
            return []
        
        # Group joists by proximity and label similarity
        unique_joists = []
        
        for joist in joists:
            is_duplicate = False
            
            for existing in unique_joists:
                # Check if they're the same joist (similar location and label)
                if (existing.page_number == joist.page_number and
                    self._calculate_distance(
                        self._get_bbox_center(existing.bbox),
                        self._get_bbox_center(joist.bbox)
                    ) < 50 and
                    self._similar_labels(existing.label, joist.label)):
                    
                    # Merge the better detection
                    if joist.confidence > existing.confidence:
                        # Replace with better detection
                        unique_joists.remove(existing)
                        unique_joists.append(joist)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_joists.append(joist)
        
        return unique_joists
    
    # Utility methods
    def _get_bbox_center(self, bbox: Tuple[float, float, float, float]) -> Tuple[float, float]:
        """Calculate center point of bounding box"""
        return ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
    
    def _calculate_distance(self, point1: Tuple[float, float], point2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two points"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
    
    def _cluster_lines_by_proximity(self, lines: List[DetectedLine], max_distance: float = 50.0) -> List[List[DetectedLine]]:
        """Cluster lines by proximity"""
        if len(lines) < 2:
            return [lines] if lines else []
        
        clusters = []
        used_lines = set()
        
        for i, line in enumerate(lines):
            if i in used_lines:
                continue
            
            cluster = [line]
            used_lines.add(i)
            
            line_y = (line.start_point[1] + line.end_point[1]) / 2
            
            for j, other_line in enumerate(lines):
                if j in used_lines or i == j:
                    continue
                
                other_y = (other_line.start_point[1] + other_line.end_point[1]) / 2
                
                if abs(line_y - other_y) <= max_distance:
                    cluster.append(other_line)
                    used_lines.add(j)
            
            if len(cluster) >= 2:
                clusters.append(cluster)
        
        return clusters
    
    def _calculate_line_spacings(self, lines: List[DetectedLine]) -> List[float]:
        """Calculate spacings between consecutive lines"""
        if len(lines) < 2:
            return []
        
        y_positions = sorted([(line.start_point[1] + line.end_point[1])/2 for line in lines])
        return [y_positions[i+1] - y_positions[i] for i in range(len(y_positions)-1)]
    
    def _get_cluster_bbox(self, lines: List[DetectedLine]) -> Tuple[float, float, float, float]:
        """Calculate bounding box for a cluster of lines"""
        all_x = []
        all_y = []
        
        for line in lines:
            all_x.extend([line.start_point[0], line.end_point[0]])
            all_y.extend([line.start_point[1], line.end_point[1]])
        
        return (min(all_x), min(all_y), max(all_x), max(all_y))
    
    def _find_text_near_bbox(self, bbox: Tuple[float, float, float, float], 
                           text_items: List[ExtractedText], radius: float = 100) -> List[ExtractedText]:
        """Find text items near a bounding box"""
        bbox_center = self._get_bbox_center(bbox)
        nearby_text = []
        
        for text_item in text_items:
            text_center = self._get_bbox_center(text_item.bbox)
            distance = self._calculate_distance(bbox_center, text_center)
            
            if distance <= radius:
                nearby_text.append(text_item)
        
        return nearby_text
    
    def _find_lines_near_joist(self, joist: AdvancedJoistLabel, 
                             detected_lines: List[DetectedLine], radius: float = 200) -> List[DetectedLine]:
        """Find lines near a joist label"""
        joist_center = self._get_bbox_center(joist.bbox)
        nearby_lines = []
        
        for line in detected_lines:
            if line.page_number != joist.page_number:
                continue
            
            line_center = ((line.start_point[0] + line.end_point[0])/2, 
                          (line.start_point[1] + line.end_point[1])/2)
            distance = self._calculate_distance(joist_center, line_center)
            
            if distance <= radius:
                nearby_lines.append(line)
        
        return nearby_lines
    
    def _find_measurements_near_joist(self, joist: AdvancedJoistLabel, 
                                    extracted_text: List[ExtractedText], radius: float = 150) -> List[ExtractedText]:
        """Find measurement text near a joist"""
        joist_center = self._get_bbox_center(joist.bbox)
        measurement_patterns = [
            r'\d+\.?\d*\s*m\b',
            r'\d+\.?\d*\s*mm\b',
            r'\d+\.?\d*\s*cm\b',
            r'\d+\.?\d*\s*ft\b'
        ]
        
        nearby_measurements = []
        
        for text_item in extracted_text:
            if text_item.page_number != joist.page_number:
                continue
            
            text_center = self._get_bbox_center(text_item.bbox)
            distance = self._calculate_distance(joist_center, text_center)
            
            if distance <= radius:
                for pattern in measurement_patterns:
                    if re.search(pattern, text_item.text, re.IGNORECASE):
                        nearby_measurements.append(text_item)
                        break
        
        return nearby_measurements
    
    def _similar_labels(self, label1: str, label2: str) -> bool:
        """Check if two joist labels are similar"""
        # Extract numbers from labels
        num1 = re.findall(r'\d+', label1)
        num2 = re.findall(r'\d+', label2)
        
        if num1 and num2:
            return num1[0] == num2[0]
        
        return label1.upper() == label2.upper()