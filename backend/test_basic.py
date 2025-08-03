#!/usr/bin/env python3
"""
Basic test script to verify the core calculation functionality
"""

from core.materials.material_system import MaterialSystem
from core.calculators.joist_calculator import JoistCalculator
from output_formats.cutting_list_generator import CuttingListGenerator, ProjectInfo, CuttingListItem

def test_material_system():
    print("=== Testing Material System ===")
    
    material_system = MaterialSystem()
    
    # Test joist material selection
    test_spans = [2.5, 3.5, 4.5, 6.5]
    
    for span in test_spans:
        material_info = material_system.get_joist_material(span)
        print(f"Span {span}m: {material_info['specification']}")
        for assumption in material_info['assumptions']:
            print(f"  - {assumption}")
    
    print("\nAvailable LVL materials:")
    for material in material_system.get_lvl_materials():
        print(f"  {material['specification']} - {material['application']}")
    
    print()

def test_joist_calculator():
    print("=== Testing Joist Calculator ===")
    
    calculator = JoistCalculator()
    
    # Test case based on client example: 3.386m span, 450mm spacing
    test_cases = [
        {"span": 3.386, "spacing": 0.45, "level": "L1"},
        {"span": 4.2, "spacing": 0.6, "level": "GF"},
        {"span": 2.8, "spacing": 0.3, "level": "RF"}
    ]
    
    for case in test_cases:
        result = calculator.calculate_joists(
            span_length=case["span"],
            joist_spacing=case["spacing"],
            building_level=case["level"]
        )
        
        print(f"Test case: {case['span']}m span, {case['spacing']}m spacing, {case['level']} level")
        print(f"  Joists required: {result['joist_count']}")
        print(f"  Joist length: {result['joist_length']:.3f}m")
        print(f"  Blocking length: {result['blocking_length']:.3f}m")
        print(f"  Material: {result['material_specification']}")
        print(f"  Reference: {result['reference_code']}")
        
        print("  Calculation notes:")
        for note in result['calculation_notes']:
            print(f"    • {note}")
        
        print("  Assumptions:")
        for assumption in result['assumptions']:
            print(f"    • {assumption}")
        
        print()

def test_cutting_list_generator():
    print("=== Testing Cutting List Generator ===")
    
    generator = CuttingListGenerator()
    
    # Create test project info
    project_info = ProjectInfo(
        project_name="Test House Project",
        client_name="Test Client",
        engineer_name="Test Engineer",
        date="2024-01-15",
        revision="A",
        delivery_number=1
    )
    
    # Create test cutting items
    cutting_items = [
        CuttingListItem(
            profile_size="200x45 E13 LVL",
            quantity=8,
            length=3.5,
            reference="L1-J1",
            application="Floor Joists",
            material_type="LVL",
            waste=0.1
        ),
        CuttingListItem(
            profile_size="200x45 E13 LVL",
            quantity=3,
            length=6.0,
            reference="L1-B1",
            application="Blocking",
            material_type="LVL",
            waste=2.1
        )
    ]
    
    # Generate cutting list
    cutting_list = generator.generate_cutting_list(
        project_info=project_info,
        cutting_items=cutting_items,
        calculation_notes=["Test calculation", "Based on span analysis"]
    )
    
    # Export to text format
    text_output = generator.export_to_text(cutting_list)
    print(text_output)

def main():
    print("Building Measurements System - Basic Test")
    print("=" * 50)
    
    test_material_system()
    test_joist_calculator()
    test_cutting_list_generator()
    
    print("All tests completed!")

if __name__ == "__main__":
    main()