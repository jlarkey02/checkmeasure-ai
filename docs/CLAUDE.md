# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Construction Material Calculation Assistant** for Australian residential construction projects. The system helps structural engineers automate material calculations and generate cutting lists from architectural PDF drawings.

## Development Commands

### Backend Development
```bash
# Navigate to backend directory
cd backend

# Install dependencies
pip install -r requirements.txt

# Run basic functionality tests
python3 test_basic.py

# Start FastAPI development server
python3 main.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
# Frontend will be available at http://localhost:3000

# Build for production
npm run build
```

### Full System Testing
```bash
# Terminal 1: Start backend
cd backend && python3 main.py

# Terminal 2: Start frontend
cd frontend && npm start

# Open browser to http://localhost:3000
# Backend API available at http://localhost:8000
```

### Testing
```bash
# Run basic system tests
cd backend && python3 test_basic.py

# Run specific component tests
python3 -m pytest tests/

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/materials/
```

## Architecture Overview

### Backend Structure
```
backend/
├── main.py                     # FastAPI application entry point
├── api/routers/               # API endpoints
│   ├── calculations.py        # Joist/beam calculation endpoints
│   ├── materials.py          # Material specification endpoints
│   ├── projects.py           # Project management endpoints
│   └── pdf_processing.py     # PDF analysis endpoints
├── core/                     # Core business logic
│   ├── calculators/          # Calculation engines
│   │   └── joist_calculator.py
│   ├── materials/            # Material system
│   │   └── material_system.py
│   └── optimization/         # Cutting optimization
├── pdf_processing/           # PDF analysis
│   └── pdf_analyzer.py
└── output_formats/           # Cutting list generation
    └── cutting_list_generator.py
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── pdf-viewer/       # PDF display and interaction
│   │   │   ├── PDFViewer.tsx
│   │   │   └── SelectionOverlay.tsx
│   │   ├── selection-tools/  # Area selection tools
│   │   │   └── SelectionTools.tsx
│   │   └── calculation-review/ # Results and specifications
│   │       ├── SpecificationPanel.tsx
│   │       └── CalculationResults.tsx
│   ├── stores/              # State management
│   │   └── appStore.ts
│   ├── types/               # TypeScript interfaces
│   │   └── index.ts
│   ├── utils/               # API client and utilities
│   │   └── api.ts
│   └── App.tsx              # Main application component
└── package.json
```

### Key Components

1. **Material System** (`core/materials/material_system.py`)
   - Defines LVL, treated pine, steel specifications
   - Implements Australian building standards (AS1684)
   - Handles material selection logic with assumption logging

2. **Joist Calculator** (`core/calculators/joist_calculator.py`)
   - Implements client-specific calculation formulas
   - Handles blocking requirements, spacing calculations
   - Generates reference codes (L1-J1, GF-J2, etc.)

3. **Cutting List Generator** (`output_formats/cutting_list_generator.py`)
   - Formats output to match client's existing cutting list format
   - Organizes by material type (LVL, Treated Pine, Building Products)
   - Calculates waste and optimization

4. **PDF Processing** (`pdf_processing/pdf_analyzer.py`)
   - Extracts text and dimensions from architectural drawings
   - Handles scale detection and conversion
   - Supports area selection for targeted measurement extraction

## Material Standards

### Available Materials
- **LVL**: 150x45, 200x45, 240x45, 200x63 E13 LVL
- **Treated Pine**: 90x45 H2 MGP10, 70x35 E10 H2
- **Standard Lengths**: 3.0m, 3.6m, 4.2m, 4.8m, 5.4m, 6.0m, 6.6m, 7.2m, 7.8m
- **Standard Spacings**: 300mm, 450mm, 600mm centers

### Calculation Examples
Based on client examples:
- **Joist Count**: `Span Length ÷ Joist Spacing = Number of Joists` (rounded up)
- **Blocking**: `Number of Rows × Span Length = Total Blocking Length`
- **Reference Codes**: `{Level}{Component}{Sequence}` (e.g., L1-J1, GF-B2)

## Development Workflow

### Adding New Calculators
1. Create new calculator in `core/calculators/`
2. Follow pattern from `joist_calculator.py`
3. Add corresponding API endpoint in `api/routers/calculations.py`
4. Update material system if new materials needed
5. Add tests in `test_basic.py`

### Testing Changes
1. **Always run** `python3 test_basic.py` after changes
2. Test API endpoints with curl or Postman
3. Verify cutting list format matches client examples
4. Check calculation accuracy against manual calculations

### Material System Updates
- Material selection logic in `material_system.py:get_joist_material()`
- All assumptions must be logged for engineer review
- Follow Australian building standards (AS1684)

## Client-Specific Requirements

### Cutting List Format
- Must match existing client format exactly
- Header: Project, Client, Engineer, Date, Revision, Delivery
- Grouped by material type: Treated Pine, LVL, Building Products
- Columns: Profile/Size, Quantity, Length, Reference, Application, Waste

### Reference Code System
- **Level Prefixes**: GF (Ground Floor), L1 (Level 1), RF (Roof)
- **Component Codes**: J (Joists), B (Blocking), ST (Studs), RX (Rafters)
- **Format**: `{Level}-{Component}{Sequence}` (e.g., L1-J1, GF-B2)

### Calculation Notes
- All calculations must include detailed notes
- Show step-by-step formula application
- Include all assumptions made during material selection
- Enable engineer review and validation

## Current Status

**Phase 1 Complete**: Core calculation engine with joist calculator
- Material system with Australian standards
- Joist calculation with blocking requirements
- Cutting list generation in client format
- Basic PDF processing framework

**Phase 2 Complete**: PDF Interface and frontend system
- React application with TypeScript
- PDF viewer with PDF.js integration
- Interactive selection tools for marking calculation areas
- Specification interface for material selection
- Full API integration between frontend and backend
- Real-time calculation results display

**Next Priorities**:
1. Dimension extraction from selected PDF areas
2. Scale detection and conversion
3. Wall framing and rafter calculators
4. Multi-story load transfer calculations
5. Advanced cutting optimization algorithms

## Important Notes

- **Always log assumptions** made during material selection
- **Test calculation accuracy** against client examples
- **Maintain client format** for cutting lists exactly
- **Follow Australian standards** (AS1684) for all calculations
- **Enable engineer review** - system assists, doesn't replace engineering judgment