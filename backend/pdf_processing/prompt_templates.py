"""
Specialized prompts for Claude Vision analysis of architectural drawings
"""

def get_joist_detection_prompt() -> str:
    """Main prompt for joist detection and analysis"""
    return """You are an expert structural engineer analyzing architectural drawings for joist detection and measurements.

Please analyze these technical drawings and identify:

1. **Joist Labels**: Look for labels like "J1", "J2", "J3", etc. that indicate joist specifications
2. **Joist Specifications**: Find text near joist labels describing dimensions and materials (e.g., "200 x 45 LVL at 450 centres")
3. **Measurements**: Identify span lengths and spacing measurements
4. **Visual Elements**: 
   - Red lines typically indicate joist placement
   - Blue lines typically show rim boards
   - Parallel lines may represent joists
   - Dimension lines with measurements

**CRITICAL**: Return your analysis as a JSON object with this exact structure:

```json
{
  "detected_joists": [
    {
      "label": "J1",
      "specification": "200 x 45 LVL at 450 centres", 
      "location": {"x": 100, "y": 200},
      "confidence": 0.95,
      "reasoning": "Clear label 'J1' with specification text nearby",
      "measurements": {
        "width_mm": 200,
        "depth_mm": 45,
        "material": "LVL",
        "spacing_mm": 450
      }
    }
  ],
  "span_length_m": 3.386,
  "joist_spacing_m": 0.45,
  "overall_confidence": 0.90,
  "claude_reasoning": "Found clear joist labels with specifications. The drawing shows a span of 3.386m with 450mm centres spacing. Red lines indicate joist placement.",
  "visual_elements_found": [
    "Joist labels (J1, J2)",
    "Dimension lines", 
    "Specification text",
    "Red joist placement lines"
  ]
}
```

**Important Guidelines:**
- Only include joists you can clearly identify with high confidence
- Convert all measurements to meters for span_length_m and joist_spacing_m
- Keep measurements in mm for the individual joist measurements object
- If you cannot find clear measurements, set values to null
- Confidence scores should be between 0.0 and 1.0
- Provide detailed reasoning for your findings
- Focus on structural elements, ignore architectural details like windows/doors

Look carefully at the drawing and provide your analysis:"""

def get_clarification_prompt(initial_findings: dict, question: str) -> str:
    """Prompt for asking Claude to clarify or re-examine specific areas"""
    return f"""Based on your initial analysis:

{initial_findings}

The user has a specific question: {question}

Please re-examine the drawings with this question in mind and provide an updated analysis. Focus particularly on the area or element the user is asking about.

Return your response in the same JSON format as before, but include additional detail about the specific question asked."""

def get_multi_page_correlation_prompt() -> str:
    """Prompt for analyzing multiple pages together"""
    return """You are analyzing multiple pages of architectural drawings that may show different views of the same structure (plan view, elevation, details, etc.).

Please correlate information across all pages to provide a comprehensive analysis of:

1. **Consistent Joist Information**: Find joists referenced across multiple pages
2. **Cross-Referenced Details**: Match detail callouts with detailed drawings
3. **Measurement Verification**: Verify measurements shown in different views
4. **Complete Specifications**: Combine partial information from different pages

Return a comprehensive JSON analysis that includes:
- All unique joists found across pages
- Cross-references between pages
- Confidence levels based on multiple confirmations
- Any discrepancies found between pages

Use the same JSON structure as the single-page analysis, but add a "page_references" field to each finding indicating which pages support that finding."""

def get_focused_area_prompt(area_description: str) -> str:
    """Prompt for analyzing a specific cropped area of a drawing"""
    return f"""You are analyzing a specific cropped section of an architectural drawing.

Focus area: {area_description}

Since this is a cropped view, focus on:
1. Any joist labels or specifications visible in this area
2. Dimension lines and measurements
3. Structural elements and their relationships
4. Text annotations and callouts

Provide a detailed analysis of just this area using the same JSON format, but note in your reasoning that this is a focused area analysis."""

def get_measurement_extraction_prompt() -> str:
    """Specialized prompt for extracting measurements only"""
    return """Focus specifically on extracting dimensional information from these architectural drawings.

Look for:
1. **Dimension Lines**: Lines with arrows and numerical values
2. **Grid Lines**: Coordinate systems with dimensions
3. **Specification Text**: Text blocks containing measurements
4. **Scale References**: Any scale indicators

Return a JSON object focused on measurements:

```json
{
  "dimensions_found": [
    {
      "value": 3386,
      "unit": "mm", 
      "type": "span_length",
      "location": {"x": 100, "y": 200},
      "confidence": 0.95
    }
  ],
  "spacing_measurements": [
    {
      "value": 450,
      "unit": "mm",
      "type": "joist_spacing", 
      "confidence": 0.90
    }
  ],
  "scale_information": {
    "scale": "1:100",
    "units": "mm"
  }
}
```

Focus only on numerical measurements and their context."""