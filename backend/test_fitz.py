#!/usr/bin/env python3
"""Test if PyMuPDF (fitz) is properly installed and working"""

import sys
print(f"Python version: {sys.version}")

try:
    import fitz
    print(f"✓ PyMuPDF (fitz) imported successfully")
    print(f"  Version: {fitz.version}")
    print(f"  PyMuPDF version: {fitz.VersionBind}")
    
    # Test creating a simple document
    doc = fitz.open()
    page = doc.new_page()
    print(f"✓ Created test PDF with page size: {page.rect}")
    doc.close()
    print(f"✓ PDF operations work correctly")
    
except ImportError as e:
    print(f"✗ Failed to import fitz: {e}")
    print("  Install with: pip install PyMuPDF")
except Exception as e:
    print(f"✗ Error testing fitz: {e}")
    import traceback
    traceback.print_exc()