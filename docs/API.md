# API Documentation

CheckMeasureAI provides a comprehensive REST API built with FastAPI. All endpoints are documented with OpenAPI/Swagger.

## API Base URL
```
http://localhost:8000
```

## Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Authentication
Currently, the API does not require authentication for development. Future versions may include API key authentication.

## Core Endpoints

### Health Check
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy"
}
```

### Materials API

#### Get All Materials
```http
GET /api/materials/
```
**Response:**
```json
{
  "lvl": [
    {
      "size": "150x45",
      "grade": "E13 LVL",
      "max_span": 4.2,
      "cost_per_meter": 15.50
    }
  ],
  "treated_pine": [
    {
      "size": "90x45",
      "grade": "H2 MGP10",
      "max_span": 3.6,
      "cost_per_meter": 8.20
    }
  ],
  "standard_lengths": [3.0, 3.6, 4.2, 4.8, 5.4, 6.0],
  "standard_spacings": [0.3, 0.45, 0.6]
}
```

#### Get Joist Materials
```http
GET /api/calculations/materials/joists
```

### Calculations API

#### Calculate Joists
```http
POST /api/calculations/joists
```

**Request Body:**
```json
{
  "span_length": 4.2,
  "joist_spacing": 0.45,
  "building_level": "L1",
  "room_type": "living",
  "load_type": "residential",
  "project_name": "Sample Project",
  "client_name": "Sample Client",
  "engineer_name": "Sample Engineer"
}
```

**Response:**
```json
{
  "joist_count": 10,
  "joist_length": 4.4,
  "blocking_count": 2,
  "blocking_length": 8.4,
  "material_specification": "200x45 E13 LVL",
  "reference_code": "L1-J1",
  "cutting_list": [
    {
      "profile_size": "200x45 E13 LVL",
      "quantity": 10,
      "length": 4.8,
      "cut_length": 4.4,
      "reference": "L1-J1",
      "application": "Joists",
      "waste": 0.4
    }
  ],
  "calculation_notes": [
    "Joist calculation: 4.2m ÷ 0.45m = 9.333 → 10 joists",
    "Joist length: 4.2m + 0.2m bearing = 4.4m"
  ],
  "assumptions": [
    "Selected 200x45 E13 LVL for span ≤4.2m",
    "Assumed residential loading (1.5 kPa live load)"
  ]
}
```

### PDF Processing API

#### Upload PDF
```http
POST /api/pdf/upload
```
**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: PDF file

#### Extract Measurements
```http
POST /api/pdf/extract
```
**Content-Type:** `multipart/form-data`

**Form Data:**
- `file`: PDF file
- `selection_areas`: JSON array of selection coordinates

### Multi-Agent System API

#### System Health
```http
GET /api/agents/system/health
```

**Response:**
```json
{
  "overall_health": "healthy",
  "total_agents": 2,
  "healthy_agents": 2,
  "available_capabilities": 3
}
```

#### Control System
```http
POST /api/agents/system/control
```

**Request Body:**
```json
{
  "action": "restart"
}
```

#### List Agents
```http
GET /api/agents/agents
```

#### Create Agent
```http
POST /api/agents/agents/create
```

**Request Body:**
```json
{
  "agent_type": "joist_calculation",
  "name": "JoistCalculator1"
}
```

#### Execute Task
```http
POST /api/agents/tasks/execute
```

**Request Body:**
```json
{
  "agent_type": "joist_calculation",
  "task_type": "joist_calculation",
  "parameters": {
    "span_length": 4.2,
    "joist_spacing": 0.45,
    "building_level": "L1"
  },
  "priority": 3
}
```

**Response:**
```json
{
  "status": "task_queued",
  "project_id": "uuid-here",
  "task_type": "joist_calculation"
}
```

#### Get Project Status
```http
GET /api/agents/projects/{project_id}
```

#### Get Project Results
```http
GET /api/agents/projects/{project_id}/results
```

**Response:**
```json
{
  "project_id": "uuid-here",
  "project_status": "completed",
  "results": [
    {
      "task_id": "task-uuid",
      "output_data": {
        "calculation_result": {
          "joist_count": 10,
          "ai_recommendations": ["Consider 600mm spacing"],
          "cost_estimation": {
            "total_cost": 450.00,
            "currency": "AUD"
          },
          "environmental_impact": {
            "carbon_footprint_kg": 25.5,
            "sustainability_rating": "A"
          }
        }
      }
    }
  ]
}
```

#### Demo Calculation
```http
POST /api/agents/demo/joist-calculation
```

## Error Handling

### Standard Error Response
```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

### Common Error Codes
- **400**: Bad Request (invalid input)
- **404**: Not Found (resource doesn't exist)
- **422**: Validation Error (invalid data format)
- **500**: Internal Server Error

## Request/Response Examples

### Complete Calculation Workflow

1. **Upload PDF**
```bash
curl -X POST "http://localhost:8000/api/pdf/upload" \
  -F "file=@sample-plan.pdf"
```

2. **Calculate Joists**
```bash
curl -X POST "http://localhost:8000/api/calculations/joists" \
  -H "Content-Type: application/json" \
  -d '{
    "span_length": 4.2,
    "joist_spacing": 0.45,
    "building_level": "L1",
    "project_name": "Test Project"
  }'
```

3. **Execute Multi-Agent Task**
```bash
curl -X POST "http://localhost:8000/api/agents/tasks/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "joist_calculation",
    "task_type": "joist_calculation",
    "parameters": {
      "span_length": 4.2,
      "joist_spacing": 0.45
    }
  }'
```

## Rate Limiting
Currently no rate limiting is implemented. For production deployment, consider implementing rate limiting based on your requirements.

## WebSocket Support
Future versions may include WebSocket support for real-time updates during long-running calculations.

## API Versioning
The current API is version 1. Future versions will use URL versioning:
- v1: `/api/...` (current)
- v2: `/api/v2/...` (future)

## SDKs and Libraries
Currently, the frontend uses a custom TypeScript API client. Community SDKs are welcome!

## Testing the API
Use the interactive documentation at `http://localhost:8000/docs` for easy API testing, or use tools like:
- **Postman**
- **curl**
- **HTTPie**
- **Insomnia**