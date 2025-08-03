"""
Calculator Factory Pattern Implementation
========================================

This module implements the factory pattern for creating calculator instances
based on element types. It provides a centralized way to instantiate the
appropriate calculator for any given element type.
"""

from typing import Dict, Type, Optional, Any
from enum import Enum
import importlib

from .base_calculator import ConstructionCalculator
from .element_types import (
    CalculatorType,
    ElementSpecification,
    element_registry
)


class CalculatorFactory:
    """
    Factory for creating calculator instances based on element types.
    
    This factory:
    - Maps calculator types to their implementations
    - Creates appropriate calculator instances
    - Handles fallback to generic calculator for unknown types
    - Maintains calculator state where needed (e.g., JoistCalculator)
    - Uses lazy loading to prevent heavy imports at startup
    """
    
    # Registry of available calculator classes
    _calculator_classes: Dict[CalculatorType, Type[ConstructionCalculator]] = {}
    
    # Registry of calculator module paths for lazy loading
    _calculator_modules: Dict[CalculatorType, str] = {
        CalculatorType.JOIST: "core.calculators.enhanced_joist_calculator.EnhancedJoistCalculator",
        CalculatorType.GENERIC: "core.calculators.generic_calculator.GenericCalculator",
        CalculatorType.WALL_FRAME: "core.calculators.generic_calculator.GenericCalculator",
        CalculatorType.BEARER: "core.calculators.generic_calculator.GenericCalculator",
        CalculatorType.RAFTER: "core.calculators.generic_calculator.GenericCalculator",
        CalculatorType.COLUMN: "core.calculators.generic_calculator.GenericCalculator",
    }
    
    # Singleton instances for stateful calculators
    _singleton_instances: Dict[CalculatorType, ConstructionCalculator] = {}
    
    @classmethod
    def _load_calculator_class(cls, calculator_type: CalculatorType) -> Optional[Type[ConstructionCalculator]]:
        """
        Lazily load a calculator class for the given type.
        
        Args:
            calculator_type: The type of calculator to load
            
        Returns:
            The calculator class or None if not found
        """
        # Check if already loaded
        if calculator_type in cls._calculator_classes:
            return cls._calculator_classes[calculator_type]
        
        # Check if we have a module path for this type
        if calculator_type not in cls._calculator_modules:
            return None
        
        try:
            module_path = cls._calculator_modules[calculator_type]
            module_name, class_name = module_path.rsplit('.', 1)
            
            # Import the module
            module = importlib.import_module(module_name)
            
            # Get the class from the module
            calculator_class = getattr(module, class_name)
            
            # Cache it for future use
            cls._calculator_classes[calculator_type] = calculator_class
            
            return calculator_class
            
        except (ImportError, AttributeError) as e:
            print(f"Failed to load calculator for {calculator_type}: {e}")
            return None
    
    @classmethod
    def register_calculator(
        cls,
        calculator_type: CalculatorType,
        calculator_class: Type[ConstructionCalculator],
        use_singleton: bool = False
    ) -> None:
        """
        Register a calculator class for a specific type.
        
        Args:
            calculator_type: The type of calculator
            calculator_class: The calculator class to register
            use_singleton: If True, only one instance will be created and reused
        """
        cls._calculator_classes[calculator_type] = calculator_class
        
        # Remove singleton if switching away from singleton mode
        if not use_singleton and calculator_type in cls._singleton_instances:
            del cls._singleton_instances[calculator_type]
    
    @classmethod
    def create_from_element_code(cls, element_code: str) -> Optional[ConstructionCalculator]:
        """
        Create a calculator instance for a specific element code.
        
        Args:
            element_code: Element code (e.g., 'J1', 'S1')
        
        Returns:
            Calculator instance or None if element not found
        """
        # Get element specification from registry
        element_spec = element_registry.get(element_code)
        if not element_spec or not element_spec.active:
            return None
        
        return cls.create_from_type(element_spec.calculator_type, element_spec)
    
    @classmethod
    def create_from_type(
        cls,
        calculator_type: CalculatorType,
        element_spec: Optional[ElementSpecification] = None
    ) -> Optional[ConstructionCalculator]:
        """
        Create a calculator instance for a specific calculator type.
        
        Args:
            calculator_type: Type of calculator to create
            element_spec: Optional element specification for configuration
        
        Returns:
            Calculator instance or None if type not registered
        """
        # Try to load the calculator class lazily
        calculator_class = cls._load_calculator_class(calculator_type)
        
        if not calculator_class:
            # Fallback to generic calculator if available
            calculator_class = cls._load_calculator_class(CalculatorType.GENERIC)
            if not calculator_class:
                return None
            calculator_type = CalculatorType.GENERIC
        
        # Check if we should use a singleton instance
        if calculator_type in cls._singleton_instances:
            calculator = cls._singleton_instances[calculator_type]
            
            # Configure for specific element if needed
            if element_spec and hasattr(calculator, 'configure_for_element'):
                calculator.configure_for_element(element_spec)
            
            return calculator
        
        # Create new instance
        if calculator_type == CalculatorType.JOIST and element_spec:
            # Special handling for joist calculator with element type
            calculator = calculator_class(joist_type=element_spec.code)
        else:
            # Standard instantiation
            calculator = calculator_class()
        
        # Configure with element spec if method exists
        if element_spec and hasattr(calculator, 'configure_for_element'):
            calculator.configure_for_element(element_spec)
        
        return calculator
    
    @classmethod
    def get_available_calculators(cls) -> Dict[str, str]:
        """
        Get all available calculator types and their descriptions.
        
        Returns:
            Dictionary mapping calculator type names to descriptions
        """
        available = {}
        for calc_type in cls._calculator_classes.keys():
            available[calc_type.value] = calc_type.value.replace('_', ' ').title()
        return available
    
    @classmethod
    def create_generic_calculator(cls) -> Optional[ConstructionCalculator]:
        """
        Create a generic calculator instance.
        
        Returns:
            Generic calculator instance or None if not available
        """
        return cls.create_from_type(CalculatorType.GENERIC)
    
    @classmethod
    def clear_singletons(cls) -> None:
        """Clear all singleton instances."""
        cls._singleton_instances.clear()


# Note: Calculator registration is now handled lazily through _calculator_modules
# This prevents heavy imports at startup and improves performance


def create_calculator(element_code: str) -> Optional[ConstructionCalculator]:
    """
    Convenience function to create a calculator for an element code.
    
    Args:
        element_code: Element code (e.g., 'J1', 'S1')
    
    Returns:
        Calculator instance or None if not available
    """
    return CalculatorFactory.create_from_element_code(element_code)