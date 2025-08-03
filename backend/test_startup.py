#!/usr/bin/env python3
"""Test backend startup issue"""

import sys
import traceback

print("Testing backend startup...")

try:
    # Test imports
    print("1. Testing basic imports...")
    from fastapi import FastAPI
    from uvicorn import Config
    print("   ✓ FastAPI and uvicorn imports OK")
    
    # Test element registry
    print("\n2. Testing element registry...")
    from core.calculators.element_types import element_registry
    print(f"   ✓ Element registry imported, has {len(element_registry._types)} types")
    
    # Test getting element types
    print("\n3. Testing element type loading...")
    all_types = element_registry.get_all()
    print(f"   ✓ Loaded {len(all_types)} element types")
    
    # Test PDF processing imports
    print("\n4. Testing PDF processing imports...")
    from api.routers import pdf_processing
    print("   ✓ PDF processing router imported")
    
    # Test main app
    print("\n5. Testing main app import...")
    from main import app
    print("   ✓ Main app imported successfully")
    
    print("\n✅ All tests passed!")
    
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
    print("\nTraceback:")
    traceback.print_exc()
    sys.exit(1)