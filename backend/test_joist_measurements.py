#!/usr/bin/env python3
"""
Test script for joist structural line measurement functionality
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pdf_processing.claude_vision_analyzer import ClaudeVisionAnalyzer

def test_joist_measurements():
    """Test the joist measurement extraction from structural lines"""
    print("Testing Joist Structural Line Measurements\n")
    
    # Path to test PDF
    clean_pdf = "../Drawings/joist-page-clean.pdf"
    
    # Check if PDF exists
    if not os.path.exists(clean_pdf):
        print(f"ERROR: Clean PDF not found at {clean_pdf}")
        return
    
    try:
        # Initialize Claude Vision analyzer
        print("=== Joist Measurement Detection Test ===")
        analyzer = ClaudeVisionAnalyzer()
        
        # Read PDF content
        with open(clean_pdf, 'rb') as f:
            pdf_content = f.read()
        
        # Detect measurements with scale factor 100 (1:100)
        print("Detecting joist measurements with scale 1:100...")
        measurements = analyzer.detect_joist_measurements(pdf_content, scale_factor=100.0)
        
        if not measurements:
            print("No measurements detected!")
            return
        
        print(f"\nMeasurements found: {len(measurements)}")
        print("-" * 60)
        
        for measurement in measurements:
            print(f"\n{measurement.pattern_label}:")
            print(f"  Horizontal span: {measurement.horizontal_span_m:.3f}m")
            if measurement.vertical_span_m:
                print(f"  Vertical span: {measurement.vertical_span_m:.3f}m")
            print(f"  Joist count: {measurement.joist_count}")
            print(f"  Confidence: {measurement.confidence * 100:.0f}%")
            print(f"  Method: {measurement.measurement_method}")
            
            if measurement.line_details:
                print("  Line details:")
                for key, value in measurement.line_details.items():
                    print(f"    - {key}: {value}")
        
        # Summary
        print("\n" + "=" * 60)
        print("Summary:")
        print(f"Total sections measured: {len(measurements)}")
        total_horizontal = sum(m.horizontal_span_m for m in measurements)
        print(f"Total horizontal span: {total_horizontal:.3f}m")
        
        if any(m.vertical_span_m for m in measurements):
            avg_vertical = sum(m.vertical_span_m or 0 for m in measurements) / len([m for m in measurements if m.vertical_span_m])
            print(f"Average vertical span: {avg_vertical:.3f}m")
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_joist_measurements()