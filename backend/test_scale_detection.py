#!/usr/bin/env python3
"""
Test script for scale detection on joist drawings
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from pdf_processing.hybrid_analyzer import HybridPDFAnalyzer
import json

def test_scale_detection():
    """Test scale detection on the clean joist PDF"""
    
    # Path to test PDF
    pdf_path = "../Drawings/joist-page-clean.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Error: Test PDF not found at {pdf_path}")
        return
    
    print("Testing scale detection on joist-page-clean.pdf...")
    print("-" * 50)
    
    # Create analyzer
    analyzer = HybridPDFAnalyzer()
    
    # Analyze PDF
    results = analyzer.analyze_pdf(pdf_path)
    
    # Display scale detection results
    scale = results['scale']
    print(f"\n📏 SCALE DETECTION RESULTS:")
    print(f"  Scale: {scale.scale_ratio}")
    print(f"  Confidence: {scale.confidence}%")
    print(f"  Method: {scale.method}")
    print(f"  Source: {scale.source_text}")
    print(f"  Page: {scale.page_number}")
    
    # Display joist detection results
    joists = results['joists']
    print(f"\n🏗️ JOIST DETECTION RESULTS:")
    print(f"  Found {len(joists)} joists:")
    for joist in joists:
        print(f"    - {joist.label} (Type: {joist.joist_type})")
        if joist.dimensions:
            print(f"      Dimensions: {joist.dimensions}")
        if joist.material:
            print(f"      Material: {joist.material}")
    
    # Display assumptions
    assumptions = results['assumptions']
    print(f"\n📋 ANALYSIS ASSUMPTIONS:")
    for assumption in assumptions:
        print(f"  [{assumption.category}] {assumption.description}:")
        print(f"    Value: {assumption.value}")
        print(f"    Confidence: {assumption.confidence}%")
        print(f"    Source: {assumption.source}")
        print(f"    Editable: {'Yes' if assumption.editable else 'No'}")
        print()
    
    # Save results to file for inspection
    output_file = "scale_detection_results.json"
    with open(output_file, 'w') as f:
        # Convert dataclasses to dicts for JSON serialization
        json_results = {
            'scale': {
                'scale_ratio': scale.scale_ratio,
                'scale_factor': scale.scale_factor,
                'confidence': scale.confidence,
                'method': scale.method,
                'source_text': scale.source_text,
                'page_number': scale.page_number
            },
            'joists': [
                {
                    'label': j.label,
                    'joist_type': j.joist_type,
                    'sublabel': j.sublabel,
                    'dimensions': j.dimensions,
                    'material': j.material,
                    'confidence': j.confidence
                }
                for j in joists
            ],
            'assumptions': [
                {
                    'id': a.id,
                    'category': a.category,
                    'description': a.description,
                    'value': a.value,
                    'confidence': a.confidence,
                    'source': a.source,
                    'editable': a.editable
                }
                for a in assumptions
            ]
        }
        json.dump(json_results, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")

if __name__ == "__main__":
    test_scale_detection()