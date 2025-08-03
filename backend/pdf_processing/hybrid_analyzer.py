"""
Hybrid PDF Analyzer - Combines text extraction, pattern matching, and vision AI
for robust scale detection and joist identification.
"""
import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import pdfplumber
from pathlib import Path
import os

logger = logging.getLogger(__name__)

@dataclass
class ScaleDetectionResult:
    """Result of scale detection from PDF"""
    scale_ratio: str  # e.g., "1:100"
    scale_factor: float  # e.g., 100.0
    confidence: float  # 0-100
    method: str  # 'text', 'ocr', 'vision', 'manual'
    source_text: Optional[str] = None  # The text where scale was found
    page_number: Optional[int] = None

@dataclass
class JoistDetection:
    """Detected joist information"""
    label: str  # e.g., "J1A"
    joist_type: str  # e.g., "J1"
    sublabel: Optional[str] = None  # e.g., "A"
    dimensions: Optional[Dict[str, float]] = None
    material: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    confidence: float = 0.0

@dataclass
class JoistPattern:
    """Detected joist pattern (cross-hatched rectangular area)"""
    label: str  # e.g., "J1A"
    bounding_box: Dict[str, float]  # x, y, width, height
    orientation: str  # 'horizontal' or 'vertical'
    confidence: float
    characteristics: str
    nearby_text: Optional[str] = None

@dataclass
class AnalysisAssumption:
    """Assumption made during analysis"""
    id: str
    category: str  # 'scale', 'joist', 'measurement', 'material'
    description: str
    value: str
    confidence: float
    source: str  # 'text', 'vision', 'default', 'manual'
    editable: bool = True


class HybridPDFAnalyzer:
    """
    Analyzes construction PDFs using a hybrid approach:
    1. Text extraction (fastest, most accurate for digital PDFs)
    2. Pattern matching (reliable for standards)
    3. Vision AI (fallback for complex cases)
    """
    
    # Scale detection patterns
    SCALE_PATTERNS = [
        (r'SCALE\s*1:(\d+)', 'standard'),
        (r'Scale\s*1:(\d+)', 'standard'),
        (r'SCALE\s*at\s*A\d\s*1:(\d+)', 'with_size'),
        (r'1:(\d+)\s*SCALE', 'reversed'),
        (r'Scale\s*@\s*1:(\d+)', 'at_symbol'),
        (r'SCALE:\s*1:(\d+)', 'colon'),
        (r'1:(\d+)', 'simple'),  # Just "1:100" without "SCALE"
    ]
    
    # Joist label patterns
    JOIST_PATTERNS = [
        r'(J\d+)([A-Z])?',  # J1, J1A, J2B, etc.
        r'(RJ\d+)([A-Z])?',  # RJ1, RJ1A (roof joists)
        r'(FJ\d+)([A-Z])?',  # FJ1, FJ1A (floor joists)
    ]
    
    # Common joist specifications
    JOIST_SPECS = {
        'LVL': [
            '150x45', '200x45', '240x45', '300x45',
            '150x63', '200x63', '240x63', '300x63'
        ],
        'MGP': ['70x35', '90x35', '90x45', '120x35', '120x45'],
        'materials': ['E13 LVL', 'E14 LVL', 'MGP10', 'MGP12']
    }
    
    def __init__(self, claude_vision_analyzer=None):
        self.assumptions = []
        self.current_scale = None
        self.claude_vision = claude_vision_analyzer
        
    def analyze_pdf(self, pdf_path: str) -> Dict:
        """
        Main entry point for PDF analysis
        """
        logger.info(f"Starting hybrid analysis of {pdf_path}")
        
        # Reset state
        self.assumptions = []
        
        # Step 1: Extract text with layout
        text_data = self._extract_text_with_layout(pdf_path)
        
        # Step 2: Detect scale
        scale_result = self._detect_scale_hierarchical(text_data, pdf_path)
        self.current_scale = scale_result
        
        # Step 3: Detect joists
        joists = self._detect_joists(text_data)
        
        # Step 4: Detect joist patterns (cross-hatched areas) if Claude Vision available
        joist_patterns = []
        if self.claude_vision and os.path.exists(pdf_path):
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                
                # Path to example PDF with marked patterns
                example_pdf_path = os.path.join(
                    os.path.dirname(pdf_path), 
                    'joist-page-example-measured.pdf'
                )
                
                pattern_result = self.claude_vision.detect_joist_patterns(
                    pdf_content, 
                    example_pdf_path if os.path.exists(example_pdf_path) else None
                )
                
                if pattern_result.get('patterns_found'):
                    for pattern_data in pattern_result['patterns_found']:
                        joist_patterns.append(JoistPattern(
                            label=pattern_data.get('label', ''),
                            bounding_box=pattern_data.get('bounding_box', {}),
                            orientation=pattern_data.get('orientation', 'horizontal'),
                            confidence=pattern_data.get('confidence', 0.0),
                            characteristics=pattern_data.get('characteristics', ''),
                            nearby_text=pattern_data.get('nearby_text')
                        ))
                    logger.info(f"Detected {len(joist_patterns)} joist patterns using Claude Vision")
            except Exception as e:
                logger.error(f"Failed to detect joist patterns: {e}")
        
        # Step 5: Detect joist measurements if Claude Vision available
        joist_measurements = []
        if self.claude_vision and os.path.exists(pdf_path):
            try:
                with open(pdf_path, 'rb') as f:
                    pdf_content = f.read()
                
                # Use the detected scale factor for measurement conversion
                scale_factor = scale_result.scale_factor if scale_result.scale_factor else 100.0
                
                measurements = self.claude_vision.detect_joist_measurements(pdf_content, scale_factor)
                joist_measurements = measurements
                logger.info(f"Detected {len(joist_measurements)} joist measurements using Claude Vision")
            except Exception as e:
                logger.error(f"Failed to detect joist measurements: {e}")
        
        # Step 6: Generate assumptions
        assumptions = self._generate_assumptions(scale_result, joists, joist_patterns)
        
        return {
            'scale': scale_result,
            'joists': joists,
            'joist_patterns': joist_patterns,
            'joist_measurements': joist_measurements,
            'assumptions': assumptions,
            'text_data': text_data  # For debugging
        }
    
    def _extract_text_with_layout(self, pdf_path: str) -> List[Dict]:
        """
        Extract text while preserving layout information
        """
        text_data = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # Extract text with bounding boxes
                    words = page.extract_words(
                        x_tolerance=3,
                        y_tolerance=3,
                        keep_blank_chars=False
                    )
                    
                    # Extract plain text
                    text = page.extract_text()
                    
                    # Extract tables if any
                    tables = page.extract_tables()
                    
                    text_data.append({
                        'page_number': page_num,
                        'text': text,
                        'words': words,
                        'tables': tables,
                        'width': page.width,
                        'height': page.height
                    })
                    
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            
        return text_data
    
    def _detect_scale_hierarchical(self, text_data: List[Dict], pdf_path: str) -> ScaleDetectionResult:
        """
        Detect scale using multiple methods in order of preference
        """
        # Method 1: Text extraction with regex
        if scale := self._detect_scale_from_text(text_data):
            logger.info(f"Scale detected from text: {scale.scale_ratio}")
            return scale
            
        # Method 2: Title block analysis (if text extraction failed)
        if scale := self._detect_scale_from_title_block(text_data):
            logger.info(f"Scale detected from title block: {scale.scale_ratio}")
            return scale
            
        # Method 3: Common scales fallback
        logger.warning("No scale detected, using default 1:100")
        return ScaleDetectionResult(
            scale_ratio="1:100",
            scale_factor=100.0,
            confidence=50.0,
            method='default',
            source_text="No scale found - using default"
        )
    
    def _detect_scale_from_text(self, text_data: List[Dict]) -> Optional[ScaleDetectionResult]:
        """
        Detect scale using regex patterns on extracted text
        """
        for page_data in text_data:
            text = page_data.get('text', '')
            if not text:
                continue
                
            for pattern, pattern_type in self.SCALE_PATTERNS:
                matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
                for match in matches:
                    scale_value = match.group(1)
                    full_match = match.group(0)
                    
                    try:
                        scale_factor = float(scale_value)
                        return ScaleDetectionResult(
                            scale_ratio=f"1:{scale_value}",
                            scale_factor=scale_factor,
                            confidence=95.0,  # High confidence for text match
                            method='text',
                            source_text=full_match,
                            page_number=page_data['page_number']
                        )
                    except ValueError:
                        continue
                        
        return None
    
    def _detect_scale_from_title_block(self, text_data: List[Dict]) -> Optional[ScaleDetectionResult]:
        """
        Look for scale specifically in title block area (usually bottom right)
        """
        for page_data in text_data:
            words = page_data.get('words', [])
            page_width = page_data.get('width', 0)
            page_height = page_data.get('height', 0)
            
            # Title block is typically in bottom right quadrant
            title_block_words = [
                w for w in words
                if w['x0'] > page_width * 0.6 and w['top'] > page_height * 0.7
            ]
            
            # Reconstruct text from title block area
            title_text = ' '.join(w['text'] for w in title_block_words)
            
            # Try patterns on title block text
            for pattern, _ in self.SCALE_PATTERNS:
                match = re.search(pattern, title_text, re.IGNORECASE)
                if match:
                    scale_value = match.group(1)
                    return ScaleDetectionResult(
                        scale_ratio=f"1:{scale_value}",
                        scale_factor=float(scale_value),
                        confidence=85.0,  # Slightly lower confidence
                        method='text',
                        source_text=f"Title block: {match.group(0)}",
                        page_number=page_data['page_number']
                    )
                    
        return None
    
    def _detect_joists(self, text_data: List[Dict]) -> List[JoistDetection]:
        """
        Detect joist labels and information from text
        """
        joists = []
        
        for page_data in text_data:
            text = page_data.get('text', '')
            words = page_data.get('words', [])
            
            # Find joist labels
            for pattern in self.JOIST_PATTERNS:
                matches = re.finditer(pattern, text, re.MULTILINE)
                for match in matches:
                    joist_type = match.group(1)
                    sublabel = match.group(2) if len(match.groups()) > 1 else None
                    
                    label = joist_type + (sublabel or '')
                    
                    # Try to find associated dimensions/materials near the label
                    joist_info = self._extract_joist_details(label, words)
                    
                    joists.append(JoistDetection(
                        label=label,
                        joist_type=joist_type,
                        sublabel=sublabel,
                        dimensions=joist_info.get('dimensions'),
                        material=joist_info.get('material'),
                        location=joist_info.get('location'),
                        confidence=90.0 if joist_info else 75.0
                    ))
        
        # Remove duplicates
        unique_joists = []
        seen_labels = set()
        for joist in joists:
            if joist.label not in seen_labels:
                seen_labels.add(joist.label)
                unique_joists.append(joist)
                
        return unique_joists
    
    def _extract_joist_details(self, joist_label: str, words: List[Dict]) -> Dict:
        """
        Extract dimensions and material info near a joist label
        """
        details = {}
        
        # Find the joist label in words
        label_words = [w for w in words if joist_label in w['text']]
        if not label_words:
            return details
            
        label_word = label_words[0]
        label_x = label_word['x0']
        label_y = label_word['top']
        
        # Look for nearby text (within reasonable distance)
        nearby_words = [
            w for w in words
            if abs(w['x0'] - label_x) < 200 and abs(w['top'] - label_y) < 100
        ]
        
        nearby_text = ' '.join(w['text'] for w in nearby_words)
        
        # Look for dimensions (e.g., "200x45")
        dim_match = re.search(r'(\d+)x(\d+)', nearby_text)
        if dim_match:
            details['dimensions'] = {
                'width': float(dim_match.group(1)),
                'height': float(dim_match.group(2))
            }
            
        # Look for materials
        for material in self.JOIST_SPECS['materials']:
            if material in nearby_text:
                details['material'] = material
                break
                
        # Store location
        details['location'] = {
            'x': label_x,
            'y': label_y
        }
        
        return details
    
    def _generate_assumptions(self, scale: ScaleDetectionResult, joists: List[JoistDetection], joist_patterns: List[JoistPattern]) -> List[AnalysisAssumption]:
        """
        Generate assumptions for user validation
        """
        assumptions = []
        
        # Scale assumption
        assumptions.append(AnalysisAssumption(
            id='scale-1',
            category='scale',
            description='Drawing Scale',
            value=scale.scale_ratio,
            confidence=scale.confidence,
            source=scale.method,
            editable=True
        ))
        
        # Default material assumption if not detected
        if joists and not any(j.material for j in joists):
            assumptions.append(AnalysisAssumption(
                id='material-1',
                category='material',
                description='Default Joist Material',
                value='200x45 E13 LVL',
                confidence=70.0,
                source='default',
                editable=True
            ))
            
        # Joist spacing assumption
        assumptions.append(AnalysisAssumption(
            id='spacing-1',
            category='measurement',
            description='Default Joist Spacing',
            value='450mm',
            confidence=80.0,
            source='default',
            editable=True
        ))
        
        # Pattern detection assumption
        if joists:
            assumptions.append(AnalysisAssumption(
                id='pattern-1',
                category='joist',
                description='Joist Detection Method',
                value=f'Text labels found: {len(joists)} joists',
                confidence=85.0,
                source='text',
                editable=False
            ))
        
        # Joist pattern detection assumption
        if joist_patterns:
            assumptions.append(AnalysisAssumption(
                id='pattern-2',
                category='joist',
                description='Joist Pattern Detection',
                value=f'Cross-patterns found: {len(joist_patterns)} patterns (J1A-{chr(ord("A") + len(joist_patterns) - 1)})',
                confidence=min(p.confidence for p in joist_patterns) if joist_patterns else 0,
                source='vision',
                editable=False
            ))
            
        return assumptions


# Utility functions
def analyze_pdf_with_assumptions(pdf_path: str) -> Dict:
    """
    Convenience function to analyze a PDF and return results with assumptions
    """
    analyzer = HybridPDFAnalyzer()
    return analyzer.analyze_pdf(pdf_path)