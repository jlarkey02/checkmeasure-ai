"""
PDF Scale Calculator - Mathematical approach to PDF measurements
Replaces AI-based auto-calibration with deterministic scale calculations
"""

import re
from typing import Tuple, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

# Standard paper sizes in mm (width x height)
PAPER_SIZES = {
    "A0": (841, 1189),
    "A1": (594, 841),
    "A2": (420, 594),
    "A3": (297, 420),
    "A4": (210, 297),
    "A5": (148, 210),
}

# Common architectural scales
COMMON_SCALES = [
    "1:20 at A3",
    "1:50 at A3",
    "1:100 at A3",
    "1:200 at A3",
    "1:500 at A3",
    "1:100 at A2",
    "1:100 at A1",
    "1:50 at A1",
]

@dataclass
class ScaleNotation:
    """Parsed scale notation"""
    scale_ratio: int  # e.g., 100 for 1:100
    paper_size: str   # e.g., "A3"
    raw_notation: str # e.g., "1:100 at A3"


class PDFScaleCalculator:
    """
    Calculate real-world measurements from PDF coordinates using scale notation.
    
    This replaces the AI-based auto-calibration with a mathematical approach
    that accounts for:
    - Drawing scale (1:50, 1:100, etc.)
    - Intended paper size (A3, A2, etc.)
    - Actual PDF dimensions
    """
    
    def __init__(self, scale_notation: str = "1:100 at A3"):
        """
        Initialize calculator with scale notation.
        
        Args:
            scale_notation: Scale and paper size, e.g., "1:100 at A3"
        """
        self.scale_notation = self._parse_scale_notation(scale_notation)
        logger.info(f"Initialized PDFScaleCalculator with {scale_notation}")
    
    def _parse_scale_notation(self, notation: str) -> ScaleNotation:
        """
        Parse scale notation string into components.
        
        Examples:
            "1:100 at A3" -> scale_ratio=100, paper_size="A3"
            "1:50 at A2" -> scale_ratio=50, paper_size="A2"
        """
        # Pattern: "1:100 at A3" or "1:100 @ A3"
        pattern = r"1:(\d+)\s*(?:at|@)\s*([A-Za-z]\d)"
        match = re.match(pattern, notation.strip())
        
        if not match:
            raise ValueError(f"Invalid scale notation: {notation}")
        
        scale_ratio = int(match.group(1))
        paper_size = match.group(2).upper()
        
        if paper_size not in PAPER_SIZES:
            raise ValueError(f"Unknown paper size: {paper_size}")
        
        return ScaleNotation(
            scale_ratio=scale_ratio,
            paper_size=paper_size,
            raw_notation=notation
        )
    
    def calculate_scale_correction(self, pdf_width_mm: float, pdf_height_mm: float) -> float:
        """
        Calculate correction factor based on PDF size vs intended paper size.
        
        Args:
            pdf_width_mm: Actual PDF page width in mm
            pdf_height_mm: Actual PDF page height in mm
            
        Returns:
            Scale correction factor
        """
        intended_width, intended_height = PAPER_SIZES[self.scale_notation.paper_size]
        
        # Determine orientation
        pdf_is_landscape = pdf_width_mm > pdf_height_mm
        intended_is_landscape = intended_width > intended_height
        
        # Flip intended dimensions if orientations don't match
        if pdf_is_landscape != intended_is_landscape:
            intended_width, intended_height = intended_height, intended_width
        
        # Calculate scale correction based on width
        # (Width is more reliable as height can vary with content)
        scale_correction = pdf_width_mm / intended_width
        
        logger.debug(f"PDF size: {pdf_width_mm:.1f}x{pdf_height_mm:.1f}mm")
        logger.debug(f"Intended size: {intended_width}x{intended_height}mm")
        logger.debug(f"Scale correction: {scale_correction:.3f}")
        
        return scale_correction
    
    def pdf_points_to_real_mm(
        self,
        distance_points: float,
        pdf_width_mm: float,
        pdf_height_mm: float
    ) -> float:
        """
        Convert distance in PDF points to real-world millimeters.
        
        Args:
            distance_points: Distance in PDF points
            pdf_width_mm: PDF page width in mm
            pdf_height_mm: PDF page height in mm
            
        Returns:
            Real-world distance in millimeters
        """
        # Convert points to mm (1 point = 0.3528 mm)
        distance_mm = distance_points * 0.3528
        
        # Get scale correction
        scale_correction = self.calculate_scale_correction(pdf_width_mm, pdf_height_mm)
        
        # Apply drawing scale and correction
        real_distance_mm = distance_mm * self.scale_notation.scale_ratio * scale_correction
        
        return real_distance_mm
    
    def measure_area(
        self,
        x1: float, y1: float,
        x2: float, y2: float,
        pdf_width_mm: float,
        pdf_height_mm: float
    ) -> Dict[str, float]:
        """
        Measure a rectangular area in PDF coordinates.
        
        Args:
            x1, y1: Top-left corner in PDF points
            x2, y2: Bottom-right corner in PDF points
            pdf_width_mm: PDF page width in mm
            pdf_height_mm: PDF page height in mm
            
        Returns:
            Dictionary with measurements in mm and m
        """
        # Calculate dimensions in PDF points
        width_points = abs(x2 - x1)
        height_points = abs(y2 - y1)
        
        # Convert to real-world measurements
        width_mm = self.pdf_points_to_real_mm(width_points, pdf_width_mm, pdf_height_mm)
        height_mm = self.pdf_points_to_real_mm(height_points, pdf_width_mm, pdf_height_mm)
        
        # Calculate area
        area_m2 = (width_mm * height_mm) / 1_000_000
        
        result = {
            "width_mm": round(width_mm),
            "height_mm": round(height_mm),
            "width_m": round(width_mm / 1000, 3),
            "height_m": round(height_mm / 1000, 3),
            "area_m2": round(area_m2, 2),
            "scale_used": self.scale_notation.raw_notation,
            "scale_ratio": self.scale_notation.scale_ratio,
        }
        
        logger.info(f"Measured area: {result['width_mm']}mm x {result['height_mm']}mm")
        
        return result
    
    @staticmethod
    def get_common_scales() -> list:
        """Get list of common scale notations for UI."""
        return COMMON_SCALES
    
    @staticmethod
    def format_scale_notation(scale_ratio: int, paper_size: str) -> str:
        """Format scale notation from components."""
        return f"1:{scale_ratio} at {paper_size}"


# Convenience function for quick measurements
def measure_pdf_area(
    coordinates: Tuple[float, float, float, float],
    pdf_dimensions: Tuple[float, float],
    scale_notation: str = "1:100 at A3"
) -> Dict[str, float]:
    """
    Quick measurement function.
    
    Args:
        coordinates: (x1, y1, x2, y2) in PDF points
        pdf_dimensions: (width_mm, height_mm) of PDF page
        scale_notation: Scale and paper size notation
        
    Returns:
        Measurement results
    """
    calculator = PDFScaleCalculator(scale_notation)
    return calculator.measure_area(
        coordinates[0], coordinates[1],
        coordinates[2], coordinates[3],
        pdf_dimensions[0], pdf_dimensions[1]
    )