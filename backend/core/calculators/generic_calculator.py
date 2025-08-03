"""
Generic Calculator for Unknown Element Types
===========================================

This module provides a generic calculator that can handle any element type
using the element registry data. It provides basic material calculations
when a specific calculator implementation doesn't exist yet.
"""

import math
from typing import Dict, List, Any, Optional

from .base_calculator import (
    ConstructionCalculator,
    StandardLengthsRegistry,
    OptimizationUtilities,
    CalculationFormatter
)
from .element_types import ElementSpecification


class GenericCalculator(ConstructionCalculator):
    """
    Generic calculator that handles any element type using registry data.
    
    This calculator:
    - Uses element specification data for calculations
    - Provides basic quantity and length calculations
    - Can be enhanced with element-specific logic later
    - Serves as a fallback for unimplemented calculators
    """
    
    def __init__(self):
        """Initialize generic calculator."""
        self.element_spec: Optional[ElementSpecification] = None
        self.standard_lengths = StandardLengthsRegistry.TIMBER_LENGTHS
        self.calculation_history = []
    
    def configure_for_element(self, element_spec: ElementSpecification) -> None:
        """
        Configure calculator for a specific element type.
        
        Args:
            element_spec: Element specification from registry
        """
        self.element_spec = element_spec
        
        # Adjust standard lengths based on material type
        if element_spec.specification.get('material') == 'Steel':
            self.standard_lengths = StandardLengthsRegistry.STEEL_LENGTHS
        else:
            self.standard_lengths = StandardLengthsRegistry.TIMBER_LENGTHS
    
    def get_material_specs(self) -> Dict:
        """Return material specifications for configured element."""
        if not self.element_spec:
            return {"generic": "Generic material calculation"}
        
        return {
            self.element_spec.code: self.element_spec.description
        }
    
    def calculate(self, dimensions: Dict[str, float], options: Dict[str, Any] = None) -> Dict:
        """
        Perform generic calculation based on element specification.
        
        Args:
            dimensions: Dictionary with dimensional data
            options: Additional calculation options
        
        Returns:
            Calculation results
        """
        # Validate dimensions
        self.validate_dimensions(dimensions)
        
        if not self.element_spec:
            raise ValueError("Calculator not configured with element specification")
        
        # Extract common dimensions
        width = dimensions.get('width', 0)
        length = dimensions.get('length', 0)
        height = dimensions.get('height', 0)
        
        # Process options
        options = options or {}
        area_suffix = options.get('area_suffix', 'A')
        building_level = options.get('building_level', 'L1')
        
        # Initialize result
        result = {
            'element_code': self.element_spec.code,
            'element_description': self.element_spec.description,
            'dimensions': dimensions,
            'calculation_notes': [],
            'warnings': []
        }
        
        # Perform calculations based on element specification
        spec = self.element_spec.specification
        
        # Handle different calculation patterns
        if 'centres' in spec:
            # Spacing-based calculation (like joists/studs)
            result.update(self._calculate_spacing_based(width, length, spec))
        elif 'configuration' in spec and spec['configuration'] == 'double':
            # Double member calculation (like bearers)
            result.update(self._calculate_double_member(width, length, spec))
        else:
            # Simple length-based calculation
            result.update(self._calculate_length_based(width, length, spec))
        
        # Add material specification
        result['material_specification'] = self._build_material_spec(spec)
        
        # Add reference code
        result['reference_code'] = f"{building_level}-{self.element_spec.code}{area_suffix}"
        
        # Store in history
        self.calculation_history.append(result)
        
        return result
    
    def _calculate_spacing_based(self, width: float, length: float, spec: Dict) -> Dict:
        """
        Calculate quantities for spacing-based elements (joists, studs).
        
        Args:
            width: Width dimension
            length: Length dimension
            spec: Element specification
        
        Returns:
            Calculation results
        """
        centres = spec.get('centres', 0.45)  # Default 450mm centres
        
        # Calculate number of members
        calculated = width / centres
        count = math.ceil(calculated)
        
        # Determine standard length
        standard_length = StandardLengthsRegistry.get_optimal_length(length)
        
        # Check for optimization
        optimization = None
        if length < 3.0:
            optimization = OptimizationUtilities.optimize_short_lengths(
                count, length, self.standard_lengths
            )
        
        return {
            'member_count': count,
            'member_length': length,
            'standard_length': standard_length,
            'centres': centres,
            'calculation': f"{width:.3f}m / {centres}m = {calculated:.3f} => {count} pieces",
            'optimization': optimization,
            'total_length': count * length,
            'waste_percentage': ((standard_length - length) / standard_length) * 100
        }
    
    def _calculate_double_member(self, width: float, length: float, spec: Dict) -> Dict:
        """
        Calculate for double member configurations (bearers).
        
        Args:
            width: Width dimension
            length: Length dimension
            spec: Element specification
        
        Returns:
            Calculation results
        """
        pieces_per_member = spec.get('pieces', 2)
        
        # For bearers, typically use the longer dimension
        member_length = max(width, length)
        standard_length = StandardLengthsRegistry.get_optimal_length(member_length)
        
        return {
            'member_count': pieces_per_member,
            'member_length': member_length,
            'standard_length': standard_length,
            'configuration': f"{pieces_per_member} pieces laminated",
            'total_length': pieces_per_member * member_length,
            'calculation': f"{pieces_per_member} × {member_length:.3f}m = {pieces_per_member * member_length:.3f}m total"
        }
    
    def _calculate_length_based(self, width: float, length: float, spec: Dict) -> Dict:
        """
        Simple length-based calculation for basic elements.
        
        Args:
            width: Width dimension
            length: Length dimension
            spec: Element specification
        
        Returns:
            Calculation results
        """
        # Use the longer dimension as the member length
        member_length = max(width, length)
        standard_length = StandardLengthsRegistry.get_optimal_length(member_length)
        
        return {
            'member_count': 1,
            'member_length': member_length,
            'standard_length': standard_length,
            'total_length': member_length,
            'calculation': f"1 piece @ {member_length:.3f}m"
        }
    
    def _build_material_spec(self, spec: Dict) -> str:
        """
        Build material specification string from element data.
        
        Args:
            spec: Element specification dictionary
        
        Returns:
            Material specification string
        """
        parts = []
        
        # Add dimensions if available
        if 'depth' in spec and 'width' in spec:
            parts.append(f"{spec['depth']} x {spec['width']}")
        elif 'profile' in spec:
            parts.append(spec['profile'])
        
        # Add grade/treatment
        if 'grade' in spec:
            parts.append(spec['grade'])
        if 'treatment' in spec:
            parts.append(spec['treatment'])
        
        # Add material type
        if 'material' in spec:
            parts.append(spec['material'])
        
        return " ".join(parts)
    
    def format_output(self, result: Dict) -> str:
        """
        Format calculation results for display.
        
        Args:
            result: Calculation result dictionary
        
        Returns:
            Formatted output string
        """
        lines = []
        
        # Header
        lines.append(f"{result['element_code']}:")
        lines.append(f"Type: {result['element_description']}")
        lines.append("")
        
        # Dimensions
        dims = result['dimensions']
        dim_parts = []
        for key, value in dims.items():
            if value > 0:
                dim_parts.append(f"{key}: {value:.3f}m")
        lines.append("Dimensions: " + ", ".join(dim_parts))
        lines.append("")
        
        # Calculation details
        lines.append("Calculation:")
        if 'calculation' in result:
            lines.append(f"  {result['calculation']}")
        
        if 'optimization' in result and result['optimization']:
            opt = result['optimization']
            lines.append(f"  Optimization: {opt['calculation']}")
        
        lines.append("")
        
        # Material requirements
        lines.append("Material Requirements:")
        lines.append(f"  Specification: {result['material_specification']}")
        
        if 'member_count' in result:
            lines.append(f"  Quantity: {result['member_count']} pieces")
            lines.append(f"  Length each: {result.get('standard_length', 0):.1f}m")
        
        if 'total_length' in result:
            lines.append(f"  Total length: {result['total_length']:.2f}m")
        
        if 'waste_percentage' in result and result['waste_percentage'] > 0:
            lines.append(f"  Waste: {result['waste_percentage']:.1f}%")
        
        # Warnings
        if result.get('warnings'):
            lines.append("")
            lines.append("Warnings:")
            for warning in result['warnings']:
                lines.append(f"  ⚠️  {warning}")
        
        # Notes
        if result.get('calculation_notes'):
            lines.append("")
            lines.append("Notes:")
            for note in result['calculation_notes']:
                lines.append(f"  • {note}")
        
        return "\n".join(lines)
    
    def generate_cutting_list(self) -> List[Dict]:
        """
        Generate cutting list from calculation history.
        
        Returns:
            List of cutting list items
        """
        if not self.calculation_history:
            return []
        
        cutting_list = []
        
        for calc in self.calculation_history:
            if 'member_count' in calc and 'standard_length' in calc:
                cutting_list.append({
                    'reference': calc['reference_code'],
                    'specification': calc['material_specification'],
                    'quantity': calc['member_count'],
                    'length': calc['standard_length'],
                    'actual_length': calc.get('member_length', 0),
                    'application': calc['element_description']
                })
        
        return cutting_list
    
    def clear_history(self) -> None:
        """Clear calculation history."""
        self.calculation_history = []