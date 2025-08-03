"""
Base Calculator Framework for Construction Material Calculations
==============================================================

This module provides the abstract base class and shared utilities for all
construction material calculators, ensuring a consistent interface and
shared functionality across different calculator types.

ARCHITECTURAL PRINCIPLES:
------------------------
1. **Separation of Concerns**: Each material type is a self-contained module
2. **Common Interface Pattern**: All calculators implement a standard interface
3. **Pluggable Architecture**: New calculators can be added without modifying existing code
4. **Shared Utilities**: Common functionality is abstracted into reusable components
5. **Configuration-Driven**: Material specifications are defined in configuration
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import math


class ConstructionCalculator(ABC):
    """
    Abstract base class defining the interface all material calculators must implement.
    
    This ensures consistency across all calculator types and enables the factory pattern
    for dynamic calculator creation.
    """
    
    @abstractmethod
    def calculate(self, dimensions: Dict[str, float], options: Dict[str, Any] = None) -> Dict:
        """
        Calculate material requirements based on dimensions and options.
        
        Args:
            dimensions: Dictionary containing dimensional data (e.g., width, length, height)
            options: Optional dictionary containing calculation options
                    (e.g., area_suffix, material_grade, spacing)
        
        Returns:
            Dictionary containing calculation results, material specifications,
            and any relevant notes or warnings
        """
        pass
    
    @abstractmethod
    def format_output(self, result: Dict) -> str:
        """
        Format calculation results for display.
        
        Args:
            result: Dictionary returned from calculate() method
        
        Returns:
            Formatted string ready for display to user
        """
        pass
    
    @abstractmethod
    def get_material_specs(self) -> Dict:
        """
        Return available material specifications for this calculator type.
        
        Returns:
            Dictionary mapping material codes to descriptions
        """
        pass
    
    def validate_dimensions(self, dimensions: Dict[str, float]) -> None:
        """
        Validate input dimensions. Can be overridden by subclasses for specific validation.
        
        Args:
            dimensions: Dictionary of dimensions to validate
        
        Raises:
            ValueError: If dimensions are invalid
        """
        for key, value in dimensions.items():
            if value is None or value <= 0:
                raise ValueError(f"{key} must be a positive number")


class StandardLengthsRegistry:
    """
    Central registry for standard material lengths used across all calculators.
    Based on Australian standard timber and steel lengths.
    """
    
    # Standard timber lengths in meters
    TIMBER_LENGTHS = [3.0, 3.6, 4.2, 4.8, 5.4, 6.0, 6.6, 7.2, 7.8, 8.4]
    
    # Common blocking/nogging lengths
    BLOCKING_LENGTHS = [4.8, 5.4, 6.0]
    
    # Standard steel lengths
    STEEL_LENGTHS = [6.0, 8.0, 9.0, 10.0, 12.0]
    
    # Sheet material sizes (width, height)
    SHEET_SIZES = [(2.4, 1.2), (2.7, 1.2), (3.0, 1.2)]
    
    @classmethod
    def get_optimal_length(cls, required_length: float, material_type: str = 'timber') -> float:
        """
        Find the optimal standard length for a given requirement.
        
        Args:
            required_length: The minimum length needed
            material_type: Type of material ('timber', 'steel', etc.)
        
        Returns:
            The shortest standard length that meets the requirement
        """
        if material_type == 'timber':
            lengths = cls.TIMBER_LENGTHS
        elif material_type == 'steel':
            lengths = cls.STEEL_LENGTHS
        else:
            lengths = cls.TIMBER_LENGTHS  # Default to timber
        
        for standard_length in sorted(lengths):
            if standard_length >= required_length:
                return standard_length
        
        # If no standard length is long enough, round up to nearest 0.6m
        return math.ceil(required_length / 0.6) * 0.6


class OptimizationUtilities:
    """
    Shared optimization algorithms for material cutting and waste reduction.
    """
    
    @staticmethod
    def optimize_short_lengths(
        num_pieces: int, 
        piece_length: float, 
        standard_lengths: List[float],
        max_waste_percent: float = 30.0
    ) -> Optional[Dict]:
        """
        Optimize multiple short pieces into fewer standard lengths.
        
        Args:
            num_pieces: Number of pieces needed
            piece_length: Length of each piece
            standard_lengths: Available standard lengths
            max_waste_percent: Maximum acceptable waste percentage
        
        Returns:
            Optimization details if beneficial, None otherwise
        """
        if piece_length >= min(standard_lengths):
            return None
        
        total_length_needed = num_pieces * piece_length
        best_option = None
        min_waste_percent = float('inf')
        
        for std_length in standard_lengths:
            pieces_per_standard = int(std_length / piece_length)
            if pieces_per_standard >= 2:
                standards_needed = math.ceil(num_pieces / pieces_per_standard)
                total_length_ordered = standards_needed * std_length
                waste = total_length_ordered - total_length_needed
                waste_percent = (waste / total_length_ordered) * 100
                
                if waste_percent < min_waste_percent and waste_percent < max_waste_percent:
                    min_waste_percent = waste_percent
                    best_option = {
                        'optimized': True,
                        'pieces_needed': standards_needed,
                        'standard_length': std_length,
                        'pieces_per_length': pieces_per_standard,
                        'waste_percent': waste_percent,
                        'calculation': (
                            f"{piece_length}m x {num_pieces} = {total_length_needed:.2f}m / "
                            f"{standards_needed} Lengths = {total_length_needed/standards_needed:.3f}m "
                            f"=> {std_length}m (cut up)"
                        )
                    }
        
        return best_option
    
    @staticmethod
    def optimize_total_length(
        total_length: float,
        available_lengths: List[float]
    ) -> List[Dict[str, float]]:
        """
        Optimize cutting pattern for total length requirement using a greedy algorithm.
        
        Args:
            total_length: Total length needed
            available_lengths: Available standard lengths
        
        Returns:
            List of pieces with quantities and lengths
        """
        pieces = []
        remaining_length = total_length
        
        # Use largest standard lengths first to minimize waste
        for standard_length in sorted(available_lengths, reverse=True):
            if remaining_length <= 0:
                break
            
            quantity_needed = int(remaining_length / standard_length)
            if quantity_needed > 0:
                pieces.append({
                    'quantity': quantity_needed,
                    'length': standard_length,
                    'total_length': quantity_needed * standard_length
                })
                remaining_length -= quantity_needed * standard_length
        
        # Handle any remaining length
        if remaining_length > 0:
            optimal_length = StandardLengthsRegistry.get_optimal_length(remaining_length)
            pieces.append({
                'quantity': 1,
                'length': optimal_length,
                'total_length': optimal_length
            })
        
        return pieces


class CalculationFormatter:
    """
    Utilities for formatting calculation outputs consistently.
    """
    
    @staticmethod
    def format_calculation_line(
        description: str,
        formula: str,
        result: str,
        indent: int = 0
    ) -> str:
        """
        Format a calculation line with consistent structure.
        
        Args:
            description: What is being calculated
            formula: The calculation formula
            result: The calculation result
            indent: Number of spaces to indent
        
        Returns:
            Formatted calculation line
        """
        indent_str = " " * indent
        return f"{indent_str}{description}: {formula} => {result}"
    
    @staticmethod
    def format_cutting_list_section(
        material_spec: str,
        items: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Format a section of the cutting list.
        
        Args:
            material_spec: Material specification string
            items: List of cutting list items
        
        Returns:
            List of formatted lines
        """
        lines = [material_spec + ":"]
        
        # Group by length
        length_groups = {}
        for item in items:
            length = item['length']
            if length not in length_groups:
                length_groups[length] = 0
            length_groups[length] += item['quantity']
        
        # Format each length group
        for length in sorted(length_groups.keys()):
            quantity = length_groups[length]
            lines.append(f"  {quantity} Lengths @ {length:.1f}m")
        
        return lines