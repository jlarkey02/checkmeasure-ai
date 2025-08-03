#!/usr/bin/env python3
"""
Debug joist label extraction
"""
import pdfplumber
import re
from pathlib import Path

def debug_joist_labels():
    """Debug joist label extraction"""
    
    pdf_path = "../Drawings/joist-page-clean.pdf"
    
    print(f"Looking for joist labels in: {pdf_path}")
    print("-" * 80)
    
    # Patterns to look for
    joist_patterns = [
        r'(J\d+)([A-Z])?',  # J1, J1A
        r'(RJ\d+)([A-Z])?',  # RJ1, RJ1A
        r'(FJ\d+)([A-Z])?',  # FJ1, FJ1A
        r'(\d+J\d+)',  # 1J1, 2J1 (alternative format)
    ]
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\n📄 PAGE {page_num}")
            
            # Get all text
            text = page.extract_text()
            
            # Get all words with positions
            words = page.extract_words()
            
            # Look for joist-related words
            joist_words = []
            for word in words:
                word_text = word['text']
                # Check if word matches any joist pattern
                for pattern in joist_patterns:
                    if re.match(pattern, word_text):
                        joist_words.append(word)
                        break
                # Also check if it contains J followed by number
                if re.search(r'J\d', word_text):
                    if word not in joist_words:
                        joist_words.append(word)
            
            print(f"\nFOUND {len(joist_words)} JOIST-RELATED WORDS:")
            for w in sorted(joist_words, key=lambda x: x['text']):
                print(f"  '{w['text']}' at position ({w['x0']:.1f}, {w['top']:.1f})")
            
            # Look for combinations like "1B13" which might be joists
            building_refs = [w for w in words if re.match(r'\d+[A-Z]\d+', w['text'])]
            if building_refs:
                print(f"\nBUILDING REFERENCES (might include joists):")
                for w in building_refs[:20]:
                    print(f"  '{w['text']}'")
            
            # Check the member schedule area
            print(f"\nMEMBER SCHEDULE TEXT EXTRACTION:")
            schedule_area_words = [
                w for w in words
                if 'MEMBER' in w['text'].upper() or 'SCHEDULE' in w['text'].upper()
            ]
            if schedule_area_words:
                # Get words near "MEMBER SCHEDULE"
                schedule_y = schedule_area_words[0]['top']
                nearby_words = [
                    w for w in words
                    if abs(w['top'] - schedule_y) < 200  # Within 200 pixels vertically
                ]
                schedule_text = ' '.join(w['text'] for w in sorted(nearby_words, key=lambda x: (x['top'], x['x0'])))
                print(f"  {schedule_text[:500]}...")

if __name__ == "__main__":
    debug_joist_labels()