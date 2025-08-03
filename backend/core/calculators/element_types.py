"""
Element Type Registry System
===========================

This module provides a flexible, data-driven system for managing structural
element types. Element types can be easily added, modified, or removed without
changing calculator code.

The registry serves as the single source of truth for all element specifications
and their associated calculators.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json


class CalculatorType(Enum):
    """Available calculator types in the system."""
    JOIST = "joist"
    WALL_FRAME = "wall_frame"
    BEARER = "bearer"
    RAFTER = "rafter"
    COLUMN = "column"
    GENERIC = "generic"  # Fallback for unknown types


@dataclass
class ElementSpecification:
    """Complete specification for a structural element."""
    code: str  # e.g., 'J1', 'S1', '1B3'
    calculator_type: CalculatorType
    description: str
    specification: Dict[str, Any]  # Flexible spec based on element type
    category: str = ""  # e.g., 'Floor System', 'Wall Framing'
    active: bool = True  # Can disable without deleting
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'code': self.code,
            'calculator_type': self.calculator_type.value,
            'description': self.description,
            'specification': self.specification,
            'category': self.category,
            'active': self.active,
            'custom_fields': self.custom_fields
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ElementSpecification':
        """Create from dictionary."""
        data = data.copy()
        data['calculator_type'] = CalculatorType(data['calculator_type'])
        return cls(**data)


class ElementTypeRegistry:
    """
    Central registry for all element types.
    
    This registry can be backed by:
    - In-memory dictionary (current)
    - JSON file (future)
    - Database (future)
    """
    
    def __init__(self):
        self._types: Dict[str, ElementSpecification] = {}
        self._initialize_default_types()
    
    def _initialize_default_types(self):
        """Initialize with default element types."""
        
        # Joist types
        self.register(ElementSpecification(
            code='J1',
            calculator_type=CalculatorType.JOIST,
            description='200x45 LVL AT 450 CTS',
            specification={
                'depth': 200,
                'width': 45,
                'material': 'LVL',
                'grade': 'E13',
                'centres': 0.45,
                'standard_profile': '200x45'
            },
            category='Floor System'
        ))
        
        self.register(ElementSpecification(
            code='J2',
            calculator_type=CalculatorType.JOIST,
            description='150x45 LVL AT 300 CTS',
            specification={
                'depth': 150,
                'width': 45,
                'material': 'LVL',
                'grade': 'E13',
                'centres': 0.30,
                'standard_profile': '150x45'
            },
            category='Floor System'
        ))
        
        self.register(ElementSpecification(
            code='J3',
            calculator_type=CalculatorType.JOIST,
            description='240x45 LVL AT 600 CTS',
            specification={
                'depth': 240,
                'width': 45,
                'material': 'LVL',
                'grade': 'E13',
                'centres': 0.60,
                'standard_profile': '240x45'
            },
            category='Floor System'
        ))
        
        # Rafter types (using joist calculator)
        self.register(ElementSpecification(
            code='RX',
            calculator_type=CalculatorType.JOIST,  # Can use joist calculator
            description='130x45 LCL AT 450 CTS',
            specification={
                'depth': 130,
                'width': 45,
                'material': 'LCL',
                'grade': 'E13',
                'centres': 0.45,
                'standard_profile': '130x45'
            },
            category='Roof System'
        ))
        
        # Wall framing types (placeholder for future calculator)
        self.register(ElementSpecification(
            code='S1',
            calculator_type=CalculatorType.WALL_FRAME,
            description='90x45 H2 MGP10 (Studs)',
            specification={
                'depth': 90,
                'width': 45,
                'material': 'MGP10',
                'treatment': 'H2',
                'centres': 0.45,
                'standard_profile': '90x45'
            },
            category='Wall Framing'
        ))
        
        self.register(ElementSpecification(
            code='S2',
            calculator_type=CalculatorType.WALL_FRAME,
            description='90x35 H2 MGP10 (Studs)',
            specification={
                'depth': 90,
                'width': 35,
                'material': 'MGP10',
                'treatment': 'H2',
                'centres': 0.60,
                'standard_profile': '90x35'
            },
            category='Wall Framing'
        ))
        
        # Bearer types (placeholder for future calculator)
        self.register(ElementSpecification(
            code='1B3',
            calculator_type=CalculatorType.BEARER,
            description='2/200x45 E13 LVL (Bearer)',
            specification={
                'configuration': 'double',
                'depth': 200,
                'width': 45,
                'material': 'LVL',
                'grade': 'E13',
                'pieces': 2,
                'standard_profile': '200x45'
            },
            category='Subfloor System'
        ))
        
        # Column types (placeholder for future calculator)
        self.register(ElementSpecification(
            code='SC1',
            calculator_type=CalculatorType.COLUMN,
            description='100UC14.8 Steel Column',
            specification={
                'profile': '100UC14.8',
                'material': 'Steel',
                'weight_per_meter': 14.8,
                'depth': 100,
                'flange_width': 100
            },
            category='Steel Framing'
        ))
    
    def register(self, element: ElementSpecification) -> None:
        """
        Register or update an element type.
        
        Args:
            element: Element specification to register
        """
        self._types[element.code] = element
    
    def remove(self, code: str) -> bool:
        """
        Remove an element type.
        
        Args:
            code: Element code to remove
        
        Returns:
            True if removed, False if not found
        """
        if code in self._types:
            del self._types[code]
            return True
        return False
    
    def deactivate(self, code: str) -> bool:
        """
        Deactivate an element type without removing it.
        
        Args:
            code: Element code to deactivate
        
        Returns:
            True if deactivated, False if not found
        """
        if code in self._types:
            self._types[code].active = False
            return True
        return False
    
    def get(self, code: str) -> Optional[ElementSpecification]:
        """
        Get an element specification by code.
        
        Args:
            code: Element code
        
        Returns:
            Element specification or None if not found
        """
        return self._types.get(code)
    
    def get_all(self, active_only: bool = True) -> Dict[str, ElementSpecification]:
        """
        Get all registered element types.
        
        Args:
            active_only: If True, only return active elements
        
        Returns:
            Dictionary of element specifications
        """
        if active_only:
            return {
                code: spec for code, spec in self._types.items()
                if spec.active
            }
        return self._types.copy()
    
    def get_by_category(self, category: str, active_only: bool = True) -> List[ElementSpecification]:
        """
        Get all elements in a specific category.
        
        Args:
            category: Category name
            active_only: If True, only return active elements
        
        Returns:
            List of element specifications
        """
        elements = []
        for spec in self._types.values():
            if spec.category == category:
                if not active_only or spec.active:
                    elements.append(spec)
        return elements
    
    def get_by_calculator_type(
        self,
        calculator_type: CalculatorType,
        active_only: bool = True
    ) -> List[ElementSpecification]:
        """
        Get all elements that use a specific calculator type.
        
        Args:
            calculator_type: Calculator type to filter by
            active_only: If True, only return active elements
        
        Returns:
            List of element specifications
        """
        elements = []
        for spec in self._types.values():
            if spec.calculator_type == calculator_type:
                if not active_only or spec.active:
                    elements.append(spec)
        return elements
    
    def get_categories(self) -> List[str]:
        """Get all unique categories."""
        categories = set()
        for spec in self._types.values():
            if spec.category:
                categories.add(spec.category)
        return sorted(list(categories))
    
    def export_to_json(self) -> str:
        """
        Export all element types to JSON.
        
        Returns:
            JSON string representation
        """
        data = {
            code: spec.to_dict()
            for code, spec in self._types.items()
        }
        return json.dumps(data, indent=2)
    
    def import_from_json(self, json_str: str) -> None:
        """
        Import element types from JSON.
        
        Args:
            json_str: JSON string to import
        """
        data = json.loads(json_str)
        for code, spec_dict in data.items():
            spec = ElementSpecification.from_dict(spec_dict)
            self.register(spec)
    
    def validate_specification(self, code: str) -> List[str]:
        """
        Validate an element specification.
        
        Args:
            code: Element code to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        spec = self.get(code)
        
        if not spec:
            errors.append(f"Element code '{code}' not found")
            return errors
        
        # Basic validation
        if not spec.description:
            errors.append("Description is required")
        
        # Calculator-specific validation
        if spec.calculator_type == CalculatorType.JOIST:
            required_fields = ['depth', 'width', 'material', 'centres']
            for field in required_fields:
                if field not in spec.specification:
                    errors.append(f"Joist specification missing required field: {field}")
        
        return errors


# Global registry instance
element_registry = ElementTypeRegistry()


def get_element_type(code: str) -> Optional[ElementSpecification]:
    """
    Convenience function to get an element type.
    
    Args:
        code: Element code
    
    Returns:
        Element specification or None
    """
    return element_registry.get(code)


def get_all_element_types(active_only: bool = True) -> Dict[str, ElementSpecification]:
    """
    Convenience function to get all element types.
    
    Args:
        active_only: If True, only return active elements
    
    Returns:
        Dictionary of element specifications
    """
    return element_registry.get_all(active_only)