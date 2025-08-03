# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CheckMeasureAI is an AI-powered construction material calculation assistant for Australian structural engineers and builders. It automates material takeoffs from architectural drawings and generates professional cutting lists compliant with Australian standards (AS1684).

## Development Commands

### Docker Development (Recommended)

```bash
# First time setup
./setup-docker.sh

# Start all services
make up

# View logs
make logs

# Stop services
make down

# Clean everything
make clean

# Access backend shell
make shell

# Run tests
make test
```

### Traditional Development

```bash
# Start both servers with one command
./scripts/dev.sh

# Stop all servers cleanly
./scripts/stop.sh

# Manual backend start
cd backend && python3 main.py

# Manual frontend start
cd frontend && npm start
```

## Architecture

### Backend (FastAPI)

The backend follows a modular architecture with clear separation of concerns:

- **API Layer** (`api/routers/`): RESTful endpoints organized by domain
  - `calculations.py`: Generic calculation endpoint supporting all element types
  - `materials.py`: Material specifications and selection
  - `pdf_processing.py`: PDF dimension extraction
  - `agents.py`: Multi-agent system for complex calculations
  
- **Core Business Logic** (`core/`):
  - `calculators/`: Implements AS1684-compliant calculations
    - `element_types.py`: Central registry for all structural elements
    - `calculator_factory.py`: Creates appropriate calculator for each element
    - `joist_calculator.py`: Reference implementation
  - `materials/material_system.py`: Material database and selection logic
  - `agents/`: Multi-agent architecture for complex workflows

- **PDF Processing** (`pdf_processing/`): PyMuPDF-based coordinate extraction

### Frontend (React/TypeScript)

- **State Management**: Zustand store (`stores/appStore.ts`)
- **PDF Interaction**: Interactive viewer with selection tools
- **API Client**: Axios-based with proper error handling

### Element Type System

The codebase uses a flexible element registry system where each structural element (J1, S1, RX, etc.) is defined with:
- Calculator type (joist, wall_frame, bearer, etc.)
- Material specifications
- Category grouping
- Active/inactive status

New element types can be added to `element_types.py` without modifying calculator code.

## Key API Endpoints

- `POST /api/calculations/calculate`: Generic calculation for any element type
- `GET /api/calculations/element-types`: List all available elements
- `POST /api/pdf/calculate-dimensions`: Convert PDF coordinates to real dimensions
- `POST /api/agents/calculate`: Multi-agent calculation workflow

## Testing

```bash
# Backend unit tests
cd backend && python3 test_basic.py

# Run pytest suite
python3 -m pytest tests/

# Test specific endpoint
curl -X POST http://localhost:8000/api/calculations/calculate \
  -H "Content-Type: application/json" \
  -d '{"element_code": "J1", "dimensions": {"width": 3.386, "length": 4.872}}'
```

## Adding New Features

1. **New Element Types**: Add to `element_registry` in `core/calculators/element_types.py`
2. **New Calculators**: Implement in `core/calculators/`, register in `calculator_factory.py`
3. **API Endpoints**: Add router in `api/routers/`, include in `main.py`
4. **Frontend Components**: Add to `components/`, update state in `appStore.ts`

## Australian Standards Compliance

- **Materials**: AS1684-compliant sizes (150x45, 200x45, 240x45 LVL)
- **Spacings**: Standard 300mm, 450mm, 600mm centers
- **Reference System**: Level-Component-Sequence (e.g., L1-J1)
- **Lengths**: 3.0m to 7.8m in 0.6m increments

## Critical Notes

- Material selection assumptions must be logged for engineer review
- All calculations show step-by-step formula application
- PDF scale detection uses mathematical calculation, not AI
- Error handling provides graceful degradation
- Process monitoring disabled to prevent idle crashes