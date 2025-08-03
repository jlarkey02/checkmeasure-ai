#!/usr/bin/env python3
"""
Test Script for Calculator Framework
===================================

This script tests the new modular calculator framework to ensure:
1. Element type registry is working
2. Calculator factory creates appropriate calculators
3. Enhanced joist calculator works with multiple types
4. Generic calculator handles unknown types
5. API endpoints are functional
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.calculators import (
    element_registry,
    create_calculator,
    EnhancedJoistCalculator,
    JOIST_TYPES
)


def test_element_registry():
    """Test element type registry functionality."""
    print("\n=== Testing Element Type Registry ===")
    
    # Get all element types
    all_types = element_registry.get_all()
    print(f"Total element types registered: {len(all_types)}")
    
    # Display by category
    categories = element_registry.get_categories()
    print(f"\nCategories: {categories}")
    
    for category in categories:
        elements = element_registry.get_by_category(category)
        print(f"\n{category}:")
        for elem in elements:
            print(f"  - {elem.code}: {elem.description}")
    
    # Test specific element
    j1 = element_registry.get('J1')
    if j1:
        print(f"\nJ1 Details:")
        print(f"  Description: {j1.description}")
        print(f"  Calculator Type: {j1.calculator_type.value}")
        print(f"  Specification: {j1.specification}")


def test_joist_calculator():
    """Test enhanced joist calculator with different types."""
    print("\n\n=== Testing Enhanced Joist Calculator ===")
    
    # Test dimensions
    test_areas = [
        {'width': 3.386, 'length': 4.872, 'suffix': 'A'},
        {'width': 2.980, 'length': 6.040, 'suffix': 'B'},
        {'width': 4.200, 'length': 2.400, 'suffix': 'C'},  # Short length test
    ]
    
    # Test with J1
    print("\n--- Testing with J1 ---")
    calc_j1 = create_calculator('J1')
    
    for area in test_areas:
        result = calc_j1.calculate(
            dimensions={'width': area['width'], 'length': area['length']},
            options={'area_suffix': area['suffix']}
        )
        print(f"\nArea {area['suffix']}:")
        print(calc_j1.format_output(result))
    
    # Show consolidated list
    if hasattr(calc_j1, 'generate_consolidated_cutting_list'):
        print(calc_j1.generate_consolidated_cutting_list())
    
    # Test with J2
    print("\n\n--- Testing with J2 ---")
    calc_j2 = create_calculator('J2')
    
    result = calc_j2.calculate(
        dimensions={'width': 3.386, 'length': 4.872},
        options={'area_suffix': 'D'}
    )
    print(calc_j2.format_output(result))


def test_generic_calculator():
    """Test generic calculator with non-joist types."""
    print("\n\n=== Testing Generic Calculator ===")
    
    # Test wall framing (S1)
    print("\n--- Testing S1 (Wall Framing) ---")
    calc_s1 = create_calculator('S1')
    if calc_s1:
        result = calc_s1.calculate(
            dimensions={'width': 3.6, 'length': 2.4},
            options={'area_suffix': 'W1'}
        )
        print(calc_s1.format_output(result))
    
    # Test bearer (1B3)
    print("\n--- Testing 1B3 (Bearer) ---")
    calc_bearer = create_calculator('1B3')
    if calc_bearer:
        result = calc_bearer.calculate(
            dimensions={'width': 4.8, 'length': 0.6},
            options={'area_suffix': 'B1'}
        )
        print(calc_bearer.format_output(result))


def test_calculator_factory():
    """Test calculator factory functionality."""
    print("\n\n=== Testing Calculator Factory ===")
    
    # Test creating calculators for different types
    test_codes = ['J1', 'J2', 'RX', 'S1', '1B3', 'SC1']
    
    for code in test_codes:
        calc = create_calculator(code)
        if calc:
            print(f"✓ Created calculator for {code}")
            specs = calc.get_material_specs()
            print(f"  Material specs: {specs}")
        else:
            print(f"✗ Failed to create calculator for {code}")
    
    # Test invalid code
    invalid_calc = create_calculator('INVALID')
    if invalid_calc:
        print("✗ Unexpectedly created calculator for invalid code")
    else:
        print("✓ Correctly rejected invalid element code")


def test_api_simulation():
    """Simulate API usage patterns."""
    print("\n\n=== Simulating API Usage ===")
    
    # Simulate getting element types for frontend
    print("\nElement types for dropdown:")
    all_types = element_registry.get_all(active_only=True)
    for code, spec in all_types.items():
        print(f"  {code}: {spec.description}")
    
    # Simulate calculation request
    print("\nSimulating calculation request for J1:")
    calc = create_calculator('J1')
    if calc:
        result = calc.calculate(
            dimensions={'width': 3.386, 'length': 4.872},
            options={'area_suffix': 'A', 'building_level': 'L1'}
        )
        
        # Simulate API response
        response = {
            'element_code': 'J1',
            'element_description': element_registry.get('J1').description,
            'calculation_result': result,
            'formatted_output': calc.format_output(result),
            'warnings': result.get('warnings', [])
        }
        
        print(f"API Response preview:")
        print(f"  Element: {response['element_code']} - {response['element_description']}")
        print(f"  Joists: {result.get('number_of_joists', 0)}")
        print(f"  Material: {result.get('material_specification', 'N/A')}")


def main():
    """Run all tests."""
    print("CheckMeasureAI Calculator Framework Test Suite")
    print("=" * 50)
    
    try:
        test_element_registry()
        test_joist_calculator()
        test_generic_calculator()
        test_calculator_factory()
        test_api_simulation()
        
        print("\n\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()