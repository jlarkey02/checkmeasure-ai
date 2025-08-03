from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

class MaterialType(Enum):
    LVL = "LVL"
    TREATED_PINE = "TREATED_PINE"
    STEEL = "STEEL"
    SHEET_MATERIAL = "SHEET_MATERIAL"

class MaterialGrade(Enum):
    E10 = "E10"
    E13 = "E13"
    H2 = "H2"
    MGP10 = "MGP10"
    MGP12 = "MGP12"

@dataclass
class MaterialSpecification:
    profile: str  # e.g., "200x45", "90x45"
    grade: MaterialGrade
    type: MaterialType
    specification_code: str  # e.g., "200x45 E13 LVL", "90x45 H2 MGP10"
    standard_lengths: List[float]  # Available lengths in meters
    application: str  # Primary use case
    load_capacity: Optional[float] = None
    cost_per_meter: Optional[float] = None

class MaterialSystem:
    def __init__(self):
        self.standard_lengths = [3.0, 3.6, 4.2, 4.8, 5.4, 6.0, 6.6, 7.2, 7.8]
        self.standard_spacings = [0.3, 0.45, 0.6]  # 300mm, 450mm, 600mm centers
        self.materials = self._initialize_materials()
    
    def _initialize_materials(self) -> Dict[str, MaterialSpecification]:
        """Initialize material database based on client examples"""
        materials = {}
        
        # LVL Materials (from client examples)
        lvl_materials = [
            MaterialSpecification(
                profile="200x45",
                grade=MaterialGrade.E13,
                type=MaterialType.LVL,
                specification_code="200x45 E13 LVL",
                standard_lengths=self.standard_lengths,
                application="Primary structural joists and beams",
                load_capacity=8.5  # kN/m (example)
            ),
            MaterialSpecification(
                profile="150x45",
                grade=MaterialGrade.E13,
                type=MaterialType.LVL,
                specification_code="150x45 E13 LVL",
                standard_lengths=self.standard_lengths,
                application="Secondary joists and rafters",
                load_capacity=6.8
            ),
            MaterialSpecification(
                profile="240x45",
                grade=MaterialGrade.E13,
                type=MaterialType.LVL,
                specification_code="240x45 E13 LVL",
                standard_lengths=self.standard_lengths,
                application="Heavy-duty beams",
                load_capacity=10.2
            ),
            MaterialSpecification(
                profile="200x63",
                grade=MaterialGrade.E13,
                type=MaterialType.LVL,
                specification_code="200x63 E13 LVL",
                standard_lengths=self.standard_lengths,
                application="Bearers and headers",
                load_capacity=12.0
            ),
        ]
        
        # Treated Pine Materials
        treated_pine_materials = [
            MaterialSpecification(
                profile="90x45",
                grade=MaterialGrade.H2,
                type=MaterialType.TREATED_PINE,
                specification_code="90x45 H2 MGP10",
                standard_lengths=self.standard_lengths,
                application="Wall framing (studs, plates, noggins)",
                load_capacity=4.2
            ),
            MaterialSpecification(
                profile="70x35",
                grade=MaterialGrade.E10,
                type=MaterialType.TREATED_PINE,
                specification_code="70x35 E10 H2",
                standard_lengths=self.standard_lengths,
                application="Flooring battens",
                load_capacity=2.8
            ),
        ]
        
        # Add all materials to dictionary
        for material in lvl_materials + treated_pine_materials:
            materials[material.specification_code] = material
        
        return materials
    
    def get_joist_material(self, span_length: float, load_type: str = "residential") -> Dict:
        """
        Determine appropriate joist material based on span length and load requirements
        Following Australian residential construction standards
        """
        assumptions = []
        
        # Material selection logic based on span length
        if span_length <= 3.0:
            selected_material = self.materials["150x45 E13 LVL"]
            assumptions.append(f"Selected 150x45 E13 LVL for span ≤3.0m (actual: {span_length}m)")
        elif span_length <= 4.2:
            selected_material = self.materials["200x45 E13 LVL"]
            assumptions.append(f"Selected 200x45 E13 LVL for span ≤4.2m (actual: {span_length}m)")
        elif span_length <= 6.0:
            selected_material = self.materials["240x45 E13 LVL"]
            assumptions.append(f"Selected 240x45 E13 LVL for span ≤6.0m (actual: {span_length}m)")
        else:
            selected_material = self.materials["200x63 E13 LVL"]
            assumptions.append(f"Selected 200x63 E13 LVL for span >6.0m (actual: {span_length}m)")
        
        # Additional assumptions based on load type
        if load_type == "residential":
            assumptions.append("Assumed residential loading (1.5 kPa live load)")
        
        return {
            "specification": selected_material.specification_code,
            "material": selected_material,
            "assumptions": assumptions
        }
    
    def get_wall_framing_material(self, wall_type: str = "internal") -> Dict:
        """Get appropriate wall framing material"""
        selected_material = self.materials["90x45 H2 MGP10"]
        assumptions = [
            f"Selected 90x45 H2 MGP10 for {wall_type} wall framing",
            "Assumed standard residential wall loading"
        ]
        
        return {
            "specification": selected_material.specification_code,
            "material": selected_material,
            "assumptions": assumptions
        }
    
    def get_standard_lengths(self) -> List[float]:
        """Get standard material lengths"""
        return self.standard_lengths
    
    def get_standard_spacings(self) -> List[float]:
        """Get standard spacing options"""
        return self.standard_spacings
    
    def get_all_materials(self) -> Dict:
        """Get all available materials"""
        return {
            "lvl": self.get_lvl_materials(),
            "treated_pine": self.get_treated_pine_materials(),
            "standard_lengths": self.standard_lengths,
            "standard_spacings": self.standard_spacings
        }
    
    def get_lvl_materials(self) -> List[Dict]:
        """Get LVL materials"""
        return [
            {
                "specification": spec.specification_code,
                "profile": spec.profile,
                "grade": spec.grade.value,
                "application": spec.application,
                "load_capacity": spec.load_capacity
            }
            for spec in self.materials.values()
            if spec.type == MaterialType.LVL
        ]
    
    def get_treated_pine_materials(self) -> List[Dict]:
        """Get treated pine materials"""
        return [
            {
                "specification": spec.specification_code,
                "profile": spec.profile,
                "grade": spec.grade.value,
                "application": spec.application,
                "load_capacity": spec.load_capacity
            }
            for spec in self.materials.values()
            if spec.type == MaterialType.TREATED_PINE
        ]
    
    def get_steel_materials(self) -> List[Dict]:
        """Get steel materials - to be implemented"""
        return []
    
    def get_joist_materials(self) -> List[Dict]:
        """Get materials suitable for joists"""
        return [
            {
                "specification": spec.specification_code,
                "profile": spec.profile,
                "grade": spec.grade.value,
                "application": spec.application,
                "load_capacity": spec.load_capacity,
                "max_span": self._calculate_max_span(spec)
            }
            for spec in self.materials.values()
            if spec.type == MaterialType.LVL and "joist" in spec.application.lower()
        ]
    
    def _calculate_max_span(self, material: MaterialSpecification) -> float:
        """Calculate maximum span for a material (simplified)"""
        # This is a simplified calculation - would need proper engineering formulas
        span_factors = {
            "150x45": 3.0,
            "200x45": 4.2,
            "240x45": 6.0,
            "200x63": 7.2
        }
        return span_factors.get(material.profile, 3.0)