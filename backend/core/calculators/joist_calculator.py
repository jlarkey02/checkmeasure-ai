import math
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from core.materials.material_system import MaterialSystem

# Import enhanced calculator functionality
try:
    from .enhanced_joist_calculator import EnhancedJoistCalculator, JOIST_TYPES
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False

@dataclass
class JoistCalculationResult:
    joist_count: int
    joist_length: float
    blocking_count: int
    blocking_length: float
    total_joist_length: float
    total_blocking_length: float
    material_specification: str
    reference_code: str
    cutting_list: List[Dict]
    calculation_notes: List[str]
    assumptions: List[str]

class JoistCalculator:
    def __init__(self, use_enhanced: bool = True):
        self.material_system = MaterialSystem()
        self.standard_lengths = self.material_system.get_standard_lengths()
        
        # Use enhanced calculator if available and requested
        if use_enhanced and ENHANCED_AVAILABLE:
            self._enhanced = EnhancedJoistCalculator()
        else:
            self._enhanced = None
    
    def calculate_joists(
        self,
        span_length: float,
        joist_spacing: float,
        building_level: str,
        room_type: Optional[str] = None,
        load_type: str = "residential"
    ) -> Dict:
        """
        Calculate joist requirements based on client examples
        
        Formula from examples:
        Span Length ÷ Joist Spacing = Number of Joists (rounded up)
        Example: 3.386m ÷ 0.45m = 7.524 → 8 joists
        
        Blocking: Number of Rows × Span Length = Total Blocking Length
        Example: 5 rows × 3.386m = 16.93m → 3 lengths @ 6.0m
        """
        
        calculation_notes = []
        assumptions = []
        
        # Validate inputs
        if span_length is None or span_length <= 0:
            raise ValueError("Span length must be a positive number")
        
        if joist_spacing is None or joist_spacing <= 0:
            raise ValueError("Joist spacing must be a positive number")
        
        if joist_spacing not in self.material_system.get_standard_spacings():
            assumptions.append(f"Non-standard joist spacing: {joist_spacing}m")
        
        # Calculate number of joists
        joist_count_raw = span_length / joist_spacing
        joist_count = math.ceil(joist_count_raw)
        
        calculation_notes.append(f"Joist calculation: {span_length}m ÷ {joist_spacing}m = {joist_count_raw:.3f} → {joist_count} joists")
        
        # Determine joist length (typically span length + bearing allowance)
        bearing_allowance = 0.1  # 100mm bearing each end
        joist_length = span_length + (2 * bearing_allowance)
        
        calculation_notes.append(f"Joist length: {span_length}m + {2 * bearing_allowance}m bearing = {joist_length}m")
        
        # Calculate blocking requirements
        blocking_rows = self._calculate_blocking_rows(span_length)
        blocking_length_per_row = span_length
        total_blocking_length = blocking_rows * blocking_length_per_row
        
        calculation_notes.append(f"Blocking: {blocking_rows} rows × {blocking_length_per_row}m = {total_blocking_length}m")
        
        # Get material specification
        material_info = self.material_system.get_joist_material(span_length, load_type)
        assumptions.extend(material_info["assumptions"])
        
        # Generate reference code
        reference_code = self._generate_reference_code(building_level, "J", 1)
        
        # Calculate total material requirements
        total_joist_length = joist_count * joist_length
        
        # Generate cutting list
        cutting_list = self._generate_cutting_list(
            joist_count=joist_count,
            joist_length=joist_length,
            blocking_length=total_blocking_length,
            material_spec=material_info["specification"],
            reference_code=reference_code
        )
        
        return {
            "joist_count": joist_count,
            "joist_length": joist_length,
            "blocking_count": blocking_rows,
            "blocking_length": total_blocking_length,
            "total_joist_length": total_joist_length,
            "material_specification": material_info["specification"],
            "reference_code": reference_code,
            "cutting_list": cutting_list,
            "calculation_notes": calculation_notes,
            "assumptions": assumptions
        }
    
    def _calculate_blocking_rows(self, span_length: float) -> int:
        """
        Calculate number of blocking rows required
        Based on AS1684 - typically 1 row per 2.4m of span
        """
        if span_length <= 2.4:
            return 1
        elif span_length <= 4.8:
            return 2
        elif span_length <= 7.2:
            return 3
        else:
            return 4
    
    def _generate_reference_code(self, building_level: str, component_type: str, sequence: int) -> str:
        """
        Generate reference code following client examples
        Format: {Level}{Component}{Sequence}
        Example: L1-J1, GF-J2, RF-J1
        """
        return f"{building_level}-{component_type}{sequence}"
    
    def _generate_cutting_list(
        self,
        joist_count: int,
        joist_length: float,
        blocking_length: float,
        material_spec: str,
        reference_code: str
    ) -> List[Dict]:
        """
        Generate cutting list with optimization for standard lengths
        """
        cutting_list = []
        
        # Optimize joist cutting
        joist_cutting = self._optimize_cutting(
            required_length=joist_length,
            quantity=joist_count,
            material_spec=material_spec,
            reference_code=reference_code,
            application="Joists"
        )
        cutting_list.extend(joist_cutting)
        
        # Optimize blocking cutting
        if blocking_length > 0:
            blocking_cutting = self._optimize_cutting(
                required_length=blocking_length,
                quantity=1,
                material_spec=material_spec,
                reference_code=reference_code.replace("J", "B"),  # B for blocking
                application="Blocking"
            )
            cutting_list.extend(blocking_cutting)
        
        return cutting_list
    
    def _optimize_cutting(
        self,
        required_length: float,
        quantity: int,
        material_spec: str,
        reference_code: str,
        application: str
    ) -> List[Dict]:
        """
        Optimize cutting pattern to minimize waste
        """
        cutting_list = []
        
        if application == "Joists":
            # For joists, each piece is the required length
            optimized_length = self._find_optimal_length(required_length)
            
            cutting_list.append({
                "profile_size": material_spec,
                "quantity": quantity,
                "length": optimized_length,
                "cut_length": required_length,
                "reference": reference_code,
                "application": application,
                "waste": optimized_length - required_length
            })
        else:
            # For blocking, optimize total length across standard lengths
            total_length_needed = required_length * quantity
            optimized_pieces = self._optimize_total_length(total_length_needed)
            
            for i, piece in enumerate(optimized_pieces):
                cutting_list.append({
                    "profile_size": material_spec,
                    "quantity": piece["quantity"],
                    "length": piece["length"],
                    "cut_length": piece["cut_length"],
                    "reference": f"{reference_code}-{i+1}",
                    "application": application,
                    "waste": piece["waste"]
                })
        
        return cutting_list
    
    def _find_optimal_length(self, required_length: float) -> float:
        """Find the shortest standard length that fits the required length"""
        for standard_length in sorted(self.standard_lengths):
            if standard_length >= required_length:
                return standard_length
        
        # If no standard length is long enough, use the longest
        return max(self.standard_lengths)
    
    def _optimize_total_length(self, total_length: float) -> List[Dict]:
        """
        Optimize cutting pattern for total length requirement
        This is a simplified version - could be improved with dynamic programming
        """
        pieces = []
        remaining_length = total_length
        
        # Use largest standard lengths first to minimize waste
        for standard_length in sorted(self.standard_lengths, reverse=True):
            if remaining_length <= 0:
                break
            
            quantity_needed = int(remaining_length / standard_length)
            if quantity_needed > 0:
                cut_length = min(standard_length, remaining_length)
                pieces.append({
                    "quantity": quantity_needed,
                    "length": standard_length,
                    "cut_length": cut_length,
                    "waste": standard_length - cut_length
                })
                remaining_length -= quantity_needed * cut_length
        
        # Handle any remaining length
        if remaining_length > 0:
            optimal_length = self._find_optimal_length(remaining_length)
            pieces.append({
                "quantity": 1,
                "length": optimal_length,
                "cut_length": remaining_length,
                "waste": optimal_length - remaining_length
            })
        
        return pieces