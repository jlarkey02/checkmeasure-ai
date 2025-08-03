"""
Enhanced Joist Calculator with Dropdown Types and Consolidation
==============================================================

This module implements the complete joist calculation system with:
- Multiple joist types (J1, J2, RX) with dropdown selection
- Area-by-area calculations with consolidation
- Short length optimization
- Advanced blocking calculations
- Professional cutting list generation

Based on Australian Standard AS1684 and real-world construction practices.
"""

import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .base_calculator import (
    ConstructionCalculator,
    StandardLengthsRegistry,
    OptimizationUtilities,
    CalculationFormatter
)
from ..materials.material_system import MaterialSystem


@dataclass
class JoistSpec:
    """Data class to store joist specifications"""
    name: str
    depth: int  # mm
    width: int  # mm
    material: str  # LVL, LCL, etc.
    centres: float  # meters
    description: str
    grade: str = "E13"  # Default grade


# Preloaded joist types based on common Australian specifications
JOIST_TYPES = {
    'J1': JoistSpec(
        name='J1',
        depth=200,
        width=45,
        material='LVL',
        centres=0.45,
        description='200x45 LVL AT 450 CTS',
        grade='E13'
    ),
    'J2': JoistSpec(
        name='J2',
        depth=150,
        width=45,
        material='LVL',
        centres=0.30,
        description='150x45 LVL AT 300 CTS',
        grade='E13'
    ),
    'RX': JoistSpec(
        name='RX',
        depth=130,
        width=45,
        material='LCL',
        centres=0.45,
        description='130x45 LCL AT 450 CTS',
        grade='E13'
    )
}


class EnhancedJoistCalculator(ConstructionCalculator):
    """
    Complete implementation of joist calculator with all features including:
    - Dropdown joist type selection
    - Multi-area consolidation
    - Short length optimization
    - Professional cutting list generation
    """
    
    def __init__(self, joist_type: str = 'J1'):
        """
        Initialize calculator with a specific joist type.
        
        Args:
            joist_type: Initial joist type (J1, J2, RX)
        """
        self.set_joist_type(joist_type)
        self.all_areas = {}  # Store all calculations for consolidation
        self.standard_lengths = StandardLengthsRegistry.TIMBER_LENGTHS
        self.blocking_lengths = StandardLengthsRegistry.BLOCKING_LENGTHS
        self.material_system = MaterialSystem()
    
    def set_joist_type(self, joist_type: str) -> None:
        """
        Change the joist type - persists until changed.
        
        Args:
            joist_type: Joist type code (J1, J2, RX)
        
        Raises:
            ValueError: If joist type is not recognized
        """
        if joist_type not in JOIST_TYPES:
            raise ValueError(f"Invalid joist type. Choose from: {list(JOIST_TYPES.keys())}")
        self.joist_type = joist_type
        self.spec = JOIST_TYPES[joist_type]
    
    def get_material_specs(self) -> Dict:
        """Return available joist specifications."""
        return {k: v.description for k, v in JOIST_TYPES.items()}
    
    def calculate(self, dimensions: Dict[str, float], options: Dict[str, Any] = None) -> Dict:
        """
        Calculate joist requirements using the complete mathematics.
        
        Args:
            dimensions: {'width': horizontal_dim, 'length': vertical_dim} in meters
            options: {
                'area_suffix': 'A',  # For multi-area tracking
                'building_level': 'L1',  # GF, L1, RF
                'require_blocking': None  # Auto-determine if None
            }
        
        Returns:
            Complete calculation results including all details
        """
        # Validate dimensions
        self.validate_dimensions(dimensions)
        
        # Extract parameters
        width = dimensions['width']
        length = dimensions['length']
        
        # Process options
        options = options or {}
        area_suffix = options.get('area_suffix', 'A')
        building_level = options.get('building_level', 'L1')
        require_blocking = options.get('require_blocking')
        
        # Get centre spacing from current joist spec
        centre_spacing = self.spec.centres
        
        # Core calculations
        calculation_notes = []
        assumptions = []
        
        # Calculate number of joists
        joists_calculated = width / centre_spacing
        number_of_joists = math.ceil(joists_calculated)
        
        calculation_notes.append(
            f"Joist calculation: {width:.3f}m ÷ {centre_spacing} = "
            f"{joists_calculated:.3f} → {number_of_joists} joists"
        )
        
        # Determine standard length for joists
        joist_standard_length = self.round_to_standard_length(length)
        
        # Check if optimization is needed for short lengths
        optimization = None
        if length < 3.0:
            optimization = self.optimize_short_lengths(number_of_joists, length)
            if optimization:
                calculation_notes.append(f"Optimization: {optimization['calculation']}")
        
        # Calculate blocking
        blocking_info = self.calculate_blocking(width, length, require_blocking)
        
        # Calculate ledger/rim board
        ledger_standard = self.round_to_standard_length(width)
        ledger_pieces = 2  # Top and bottom
        
        # Generate reference code
        reference_code = f"{building_level}-{self.joist_type}{area_suffix}"
        
        # Build complete result
        result = {
            # Area identification
            'area_suffix': area_suffix,
            'building_level': building_level,
            'reference_code': reference_code,
            
            # Joist type information
            'joist_type': self.joist_type,
            'joist_spec': {
                'name': self.spec.name,
                'depth': self.spec.depth,
                'width': self.spec.width,
                'material': self.spec.material,
                'centres': self.spec.centres,
                'description': self.spec.description,
                'grade': self.spec.grade
            },
            
            # Dimensions
            'width': width,
            'length': length,
            'area_m2': width * length,
            
            # Joist calculations
            'centre_spacing': centre_spacing,
            'joists_calculated': joists_calculated,
            'number_of_joists': number_of_joists,
            'joist_standard_length': joist_standard_length,
            'joist_actual_length': length,
            
            # Optimization
            'optimization': optimization,
            
            # Blocking
            'blocking': blocking_info,
            
            # Ledger/Rim board
            'ledger_standard': ledger_standard,
            'ledger_pieces': ledger_pieces,
            'ledger_actual_length': width,
            
            # Material specification
            'material_specification': f"{self.spec.depth} x {self.spec.width} {self.spec.grade} {self.spec.material}",
            
            # Notes and assumptions
            'calculation_notes': calculation_notes,
            'assumptions': assumptions
        }
        
        # Store for consolidation
        area_key = f"{self.joist_type}{area_suffix}"
        self.all_areas[area_key] = result
        
        return result
    
    def round_to_standard_length(self, length: float) -> float:
        """
        Round up to next standard timber length.
        
        Args:
            length: Required length in meters
        
        Returns:
            Standard length that accommodates the requirement
        """
        if length <= 3.0:
            return 3.0
        
        for standard in self.standard_lengths:
            if standard >= length:
                return standard
        
        # If no standard length is long enough, round up to nearest 0.6m
        return math.ceil(length / 0.6) * 0.6
    
    def optimize_short_lengths(self, num_pieces: int, piece_length: float) -> Optional[Dict]:
        """
        Optimize multiple short pieces into fewer standard lengths.
        
        Example: 8 pieces × 2.5m each could be cut from 4 × 6m lengths
        instead of ordering 8 × 3m lengths.
        
        Args:
            num_pieces: Number of pieces needed
            piece_length: Length of each piece
        
        Returns:
            Optimization details if beneficial, None otherwise
        """
        if piece_length >= 3.0:
            return None
        
        optimization = OptimizationUtilities.optimize_short_lengths(
            num_pieces=num_pieces,
            piece_length=piece_length,
            standard_lengths=self.standard_lengths,
            max_waste_percent=30.0
        )
        
        return optimization
    
    def calculate_blocking(self, width: float, length: float, require_blocking: bool = None) -> Dict:
        """
        Calculate blocking requirements based on AS1684 standards.
        
        Args:
            width: Span width in meters
            length: Joist length in meters
            require_blocking: Force blocking on/off, auto-determine if None
        
        Returns:
            Dictionary with blocking details
        """
        # Auto-determine blocking requirement if not specified
        if require_blocking is None:
            require_blocking = length > 3.0
        
        if not require_blocking:
            return {'required': False}
        
        # Blocking spacing as per AS1684
        blocking_spacing = 1.2  # meters
        blocking_calculated = length / blocking_spacing
        rows_of_blocking = math.ceil(blocking_calculated)
        
        # Total blocking length needed
        total_blocking_length = rows_of_blocking * width
        
        # Optimize blocking lengths
        best_option = None
        min_waste = float('inf')
        
        for blength in self.blocking_lengths:
            pieces_needed = math.ceil(total_blocking_length / blength)
            total_ordered = pieces_needed * blength
            waste = total_ordered - total_blocking_length
            waste_percent = (waste / total_ordered) * 100
            
            if waste < min_waste:
                min_waste = waste
                best_option = {
                    'length': blength,
                    'pieces': pieces_needed,
                    'waste_percent': waste_percent
                }
        
        return {
            'required': True,
            'spacing': blocking_spacing,
            'rows_calculated': blocking_calculated,
            'rows': rows_of_blocking,
            'total_length': total_blocking_length,
            'pieces': best_option['pieces'],
            'standard_length': best_option['length'],
            'waste_percent': best_option['waste_percent'],
            'calculation': f"{length:.3f}m / {blocking_spacing}m = {blocking_calculated:.3f} => {rows_of_blocking} rows of Blocking",
            'row_calculation': f"{rows_of_blocking} Rows of Blocking x {width:.3f}m = {total_blocking_length:.2f}m = {best_option['pieces']} Lengths @ {best_option['length']}m"
        }
    
    def format_output(self, result: Dict) -> str:
        """
        Format calculation result for professional display.
        
        Args:
            result: Calculation result dictionary
        
        Returns:
            Formatted string for display
        """
        lines = []
        
        # Header
        area_key = f"{result['joist_type']}{result['area_suffix']}"
        lines.append(f"{area_key}:")
        lines.append("")
        
        # Joist calculations
        lines.append("Joist Lengths:")
        calc_line = (
            f"{result['width']:.3f}m / {result['centre_spacing']} (centres) = "
            f"{result['joists_calculated']:.3f} => {result['number_of_joists']} "
            f"Lengths @ {result['joist_standard_length']}m"
        )
        lines.append(calc_line)
        
        # Optimization note if applicable
        if result['optimization'] and result['optimization']['optimized']:
            lines.append(f"Optimization: {result['optimization']['calculation']}")
        
        lines.append("")
        
        # Blocking section
        lines.append("Joist Blocking:")
        if result['blocking']['required']:
            lines.append(result['blocking']['calculation'])
            lines.append("")
            lines.append(result['blocking']['row_calculation'])
        else:
            lines.append("No Blocking")
        
        lines.append("")
        
        # Ledger/Rim board
        lines.append("Ledger Board/Rim Board:")
        lines.append(
            f"2 x {result['width']:.3f}m = {result['ledger_pieces']} "
            f"Lengths @ {result['ledger_standard']:.1f}m"
        )
        
        lines.append("")
        
        # Cutting list
        lines.append("Cutting List:")
        lines.append(result['material_specification'])
        
        # Ledger pieces
        lines.append(f"{result['ledger_pieces']} Lengths @ {result['ledger_standard']:.1f}m")
        
        # Blocking pieces
        if result['blocking']['required']:
            lines.append(
                f"{result['blocking']['pieces']} Lengths @ "
                f"{result['blocking']['standard_length']:.1f}m"
            )
        
        # Joist pieces
        if result['optimization'] and result['optimization']['optimized']:
            lines.append(
                f"{result['optimization']['pieces_needed']} Lengths @ "
                f"{result['optimization']['standard_length']:.1f}m (cut up)"
            )
        else:
            lines.append(
                f"{result['number_of_joists']} Lengths @ "
                f"{result['joist_standard_length']:.1f}m"
            )
        
        return "\n".join(lines)
    
    def generate_consolidated_cutting_list(self) -> str:
        """
        Generate consolidated cutting list for all calculated areas.
        
        Returns:
            Formatted consolidated cutting list
        """
        if not self.all_areas:
            return "No areas calculated yet."
        
        lines = []
        lines.append("\n" + "="*60)
        lines.append("CONSOLIDATED CUTTING LIST - ALL AREAS")
        lines.append("="*60)
        
        # Consolidate materials by specification and length
        consolidated = {}
        
        for area_key, result in self.all_areas.items():
            material_spec = result['material_specification']
            
            # Add ledger/rim board
            key = (material_spec, result['ledger_standard'])
            consolidated[key] = consolidated.get(key, 0) + result['ledger_pieces']
            
            # Add blocking if required
            if result['blocking']['required']:
                key = (material_spec, result['blocking']['standard_length'])
                consolidated[key] = consolidated.get(key, 0) + result['blocking']['pieces']
            
            # Add joists
            if result['optimization'] and result['optimization']['optimized']:
                key = (material_spec, result['optimization']['standard_length'])
                consolidated[key] = consolidated.get(key, 0) + result['optimization']['pieces_needed']
            else:
                key = (material_spec, result['joist_standard_length'])
                consolidated[key] = consolidated.get(key, 0) + result['number_of_joists']
        
        # Group by material specification
        materials = {}
        for (material_spec, length), quantity in consolidated.items():
            if material_spec not in materials:
                materials[material_spec] = []
            materials[material_spec].append((length, quantity))
        
        # Format output
        for material_spec, lengths in materials.items():
            lines.append(f"\n{material_spec}:")
            for length, quantity in sorted(lengths):
                lines.append(f"  {quantity} Lengths @ {length:.1f}m")
        
        # Summary
        lines.append("\n" + "-"*60)
        lines.append(f"Total areas calculated: {len(self.all_areas)}")
        lines.append("Areas included: " + ", ".join(self.all_areas.keys()))
        
        # Total area
        total_area = sum(result['area_m2'] for result in self.all_areas.values())
        lines.append(f"Total floor area: {total_area:.1f} m²")
        
        return "\n".join(lines)
    
    def clear_areas(self) -> None:
        """Clear all stored area calculations."""
        self.all_areas = {}
    
    def get_area_summary(self) -> List[Dict]:
        """
        Get summary of all calculated areas.
        
        Returns:
            List of area summaries
        """
        summaries = []
        for area_key, result in self.all_areas.items():
            summaries.append({
                'area_key': area_key,
                'dimensions': f"{result['width']:.2f}m × {result['length']:.2f}m",
                'area_m2': result['area_m2'],
                'joist_type': result['joist_type'],
                'joist_count': result['number_of_joists'],
                'material': result['material_specification']
            })
        return summaries