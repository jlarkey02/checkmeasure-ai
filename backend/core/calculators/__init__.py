"""
Calculator Module Initialization
================================

This module provides all calculator implementations and supporting infrastructure
for the CheckMeasureAI system.
"""

# Base classes and utilities
from .base_calculator import (
    ConstructionCalculator,
    StandardLengthsRegistry,
    OptimizationUtilities,
    CalculationFormatter
)

# Element type system
from .element_types import (
    CalculatorType,
    ElementSpecification,
    ElementTypeRegistry,
    element_registry,
    get_element_type,
    get_all_element_types
)

# Calculator implementations
from .joist_calculator import JoistCalculator
from .enhanced_joist_calculator import EnhancedJoistCalculator, JOIST_TYPES
from .generic_calculator import GenericCalculator

# Factory pattern
from .calculator_factory import CalculatorFactory, create_calculator

__all__ = [
    # Base classes
    'ConstructionCalculator',
    'StandardLengthsRegistry',
    'OptimizationUtilities',
    'CalculationFormatter',
    
    # Element types
    'CalculatorType',
    'ElementSpecification',
    'ElementTypeRegistry',
    'element_registry',
    'get_element_type',
    'get_all_element_types',
    
    # Calculators
    'JoistCalculator',
    'EnhancedJoistCalculator',
    'JOIST_TYPES',
    'GenericCalculator',
    
    # Factory
    'CalculatorFactory',
    'create_calculator'
]