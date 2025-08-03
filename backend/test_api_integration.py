#!/usr/bin/env python3
"""
API Integration Test for Calculator Framework
============================================

This script tests the API endpoints to ensure they work correctly
with the calculator framework.
"""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_element_types_endpoint():
    """Test the element types endpoint."""
    print("\n=== Testing Element Types Endpoint ===")
    
    # Get all element types
    response = requests.get(f"{BASE_URL}/api/calculations/element-types")
    if response.status_code == 200:
        types = response.json()
        print(f"✓ Retrieved {len(types)} element types")
        for t in types[:3]:  # Show first 3
            print(f"  - {t['code']}: {t['description']}")
    else:
        print(f"✗ Failed to get element types: {response.status_code}")
    
    # Get specific element type
    response = requests.get(f"{BASE_URL}/api/calculations/element-types/J1")
    if response.status_code == 200:
        j1 = response.json()
        print(f"\n✓ Retrieved J1 details:")
        print(f"  Description: {j1['description']}")
        print(f"  Category: {j1['category']}")
        print(f"  Calculator Type: {j1['calculator_type']}")
    else:
        print(f"✗ Failed to get J1 details: {response.status_code}")


def test_categories_endpoint():
    """Test the categories endpoint."""
    print("\n\n=== Testing Categories Endpoint ===")
    
    response = requests.get(f"{BASE_URL}/api/calculations/categories")
    if response.status_code == 200:
        categories = response.json()
        print(f"✓ Retrieved {len(categories)} categories:")
        for cat in categories:
            print(f"  - {cat}")
    else:
        print(f"✗ Failed to get categories: {response.status_code}")


def test_generic_calculate_endpoint():
    """Test the generic calculation endpoint."""
    print("\n\n=== Testing Generic Calculate Endpoint ===")
    
    # Test J1 calculation
    request_data = {
        "element_code": "J1",
        "dimensions": {
            "width": 3.386,
            "length": 4.872
        },
        "options": {
            "area_suffix": "A",
            "building_level": "L1"
        }
    }
    
    print("\nTesting J1 calculation...")
    response = requests.post(
        f"{BASE_URL}/api/calculations/calculate",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Calculation successful for {result['element_code']}")
        print(f"  Description: {result['element_description']}")
        print(f"  Joists: {result['calculation_result']['number_of_joists']}")
        print("\nFormatted Output Preview:")
        print(result['formatted_output'].split('\n')[:5])  # First 5 lines
    else:
        print(f"✗ Calculation failed: {response.status_code}")
        print(f"  Error: {response.text}")
    
    # Test S1 (wall framing) calculation
    request_data = {
        "element_code": "S1",
        "dimensions": {
            "width": 3.6,
            "length": 2.4
        },
        "options": {
            "area_suffix": "W1"
        }
    }
    
    print("\n\nTesting S1 (wall framing) calculation...")
    response = requests.post(
        f"{BASE_URL}/api/calculations/calculate",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Calculation successful for {result['element_code']}")
        print(f"  Description: {result['element_description']}")
    else:
        print(f"✗ Calculation failed: {response.status_code}")


def test_backward_compatibility():
    """Test that old joist endpoint still works."""
    print("\n\n=== Testing Backward Compatibility ===")
    
    request_data = {
        "span_length": 3.386,
        "joist_spacing": 0.45,
        "building_level": "L1",
        "load_type": "residential"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/calculations/joists",
        json=request_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✓ Legacy joist endpoint still works")
        print(f"  Joist count: {result['joist_count']}")
        print(f"  Material: {result['material_specification']}")
    else:
        print(f"✗ Legacy endpoint failed: {response.status_code}")


def main():
    """Run all API tests."""
    print("CheckMeasureAI API Integration Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code != 200:
            print("❌ Server is not responding. Please start the backend first.")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the backend with:")
        print("   cd backend && python3 main.py")
        return
    
    print("✓ Server is running")
    
    # Run tests
    test_element_types_endpoint()
    test_categories_endpoint()
    test_generic_calculate_endpoint()
    test_backward_compatibility()
    
    print("\n\n" + "=" * 50)
    print("✅ API integration tests completed!")


if __name__ == "__main__":
    main()