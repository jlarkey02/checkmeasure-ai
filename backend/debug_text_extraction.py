#!/usr/bin/env python3
"""
Debug text extraction to see what pdfplumber is finding
"""
import pdfplumber
from pathlib import Path

def debug_text_extraction():
    """Debug what text is being extracted from the PDF"""
    
    pdf_path = "../Drawings/joist-page-clean.pdf"
    
    print(f"Debugging text extraction from: {pdf_path}")
    print("-" * 80)
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\n📄 PAGE {page_num} - Dimensions: {page.width} x {page.height}")
            print("-" * 40)
            
            # Extract plain text
            text = page.extract_text()
            if text:
                print("EXTRACTED TEXT:")
                print(text[:1000])  # First 1000 chars
                if len(text) > 1000:
                    print(f"... (truncated, total length: {len(text)} chars)")
            else:
                print("NO TEXT EXTRACTED")
            
            # Extract words with positions
            words = page.extract_words()
            print(f"\nWORD COUNT: {len(words)}")
            
            # Look for scale-related words
            scale_words = [w for w in words if 'scale' in w['text'].lower() or '1:' in w['text']]
            if scale_words:
                print("\nSCALE-RELATED WORDS FOUND:")
                for w in scale_words:
                    print(f"  '{w['text']}' at position ({w['x0']:.1f}, {w['top']:.1f})")
            
            # Look in bottom right area (typical title block location)
            title_block_words = [
                w for w in words
                if w['x0'] > page.width * 0.6 and w['top'] > page.height * 0.7
            ]
            if title_block_words:
                print(f"\nTITLE BLOCK AREA TEXT ({len(title_block_words)} words):")
                title_text = ' '.join(w['text'] for w in title_block_words[:50])
                print(f"  {title_text}")
            
            # Look for any text containing numbers that might be scale
            number_words = [w for w in words if any(c.isdigit() for c in w['text'])]
            potential_scales = [w for w in number_words if ':' in w['text'] or '1' in w['text']]
            if potential_scales:
                print(f"\nPOTENTIAL SCALE INDICATORS:")
                for w in potential_scales[:10]:
                    print(f"  '{w['text']}' at ({w['x0']:.1f}, {w['top']:.1f})")

if __name__ == "__main__":
    debug_text_extraction()