#!/usr/bin/env python3
"""
Test script for J1 pattern detection functionality
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_processing.claude_vision_analyzer import ClaudeVisionAnalyzer
from pdf_processing.hybrid_analyzer import HybridPDFAnalyzer

def test_pattern_detection():
    """Test the joist pattern detection with both PDFs"""
    print("Testing J1 Pattern Detection\n")
    
    # Paths to test PDFs
    clean_pdf = "../Drawings/joist-page-clean.pdf"
    example_pdf = "../Drawings/joist-page-example-measured.pdf"
    
    # Check if PDFs exist
    if not os.path.exists(clean_pdf):
        print(f"ERROR: Clean PDF not found at {clean_pdf}")
        return
    
    if not os.path.exists(example_pdf):
        print(f"ERROR: Example PDF not found at {example_pdf}")
        return
    
    try:
        # Test 1: Direct Claude Vision pattern detection
        print("=== Test 1: Direct Claude Vision Pattern Detection ===")
        analyzer = ClaudeVisionAnalyzer()
        
        with open(clean_pdf, 'rb') as f:
            pdf_content = f.read()
        
        result = analyzer.detect_joist_patterns(pdf_content, example_pdf)
        
        if result.get('error'):
            print(f"ERROR: {result['error']}")
        else:
            patterns = result.get('patterns_found', [])
            print(f"Patterns found: {len(patterns)}")
            
            for pattern in patterns:
                print(f"\n{pattern['label']}:")
                print(f"  - Orientation: {pattern['orientation']}")
                print(f"  - Confidence: {pattern['confidence']}%")
                print(f"  - Characteristics: {pattern['characteristics']}")
                print(f"  - Location: ({pattern['bounding_box']['x']}, {pattern['bounding_box']['y']})")
                print(f"  - Size: {pattern['bounding_box']['width']}x{pattern['bounding_box']['height']}")
                if pattern.get('nearby_text'):
                    print(f"  - Nearby text: {pattern['nearby_text']}")
        
        # Test 2: Hybrid analyzer with pattern detection
        print("\n\n=== Test 2: Hybrid Analyzer with Pattern Detection ===")
        hybrid_analyzer = HybridPDFAnalyzer(claude_vision_analyzer=analyzer)
        results = hybrid_analyzer.analyze_pdf(clean_pdf)
        
        print(f"\nScale detected: {results['scale'].scale_ratio} (confidence: {results['scale'].confidence}%)")
        print(f"Joists detected: {len(results['joists'])}")
        print(f"Patterns detected: {len(results.get('joist_patterns', []))}")
        
        # Check assumptions
        print("\nAssumptions:")
        for assumption in results['assumptions']:
            print(f"  - {assumption.description}: {assumption.value} ({assumption.confidence}% from {assumption.source})")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pattern_detection()