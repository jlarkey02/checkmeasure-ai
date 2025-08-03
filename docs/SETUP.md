# Development Environment Setup

This guide will help you set up CheckMeasureAI for development on your local machine.

## Prerequisites

### Required Software
- **Python 3.11+** - [Download](https://www.python.org/downloads/)
- **Node.js 18+** - [Download](https://nodejs.org/)
- **Git** - [Download](https://git-scm.com/)

### Optional but Recommended
- **VS Code** - [Download](https://code.visualstudio.com/)
- **Postman** - For API testing

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/checkmeasure-ai.git
cd checkmeasure-ai
```

### 2. Backend Setup

#### Install Python Dependencies
```bash
cd backend
pip install -r requirements.txt
```

#### Environment Variables (Optional)
Create a `.env` file in the backend directory:
```env
# Claude AI API Key (optional - for enhanced analysis)
ANTHROPIC_API_KEY=your_api_key_here

# CORS Origins (for production)
CORS_ORIGINS=["http://localhost:3000"]
```

#### Start Backend Server
```bash
python3 main.py
```
Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend will be available at: `http://localhost:8000`

### 3. Frontend Setup

#### Install Node Dependencies
```bash
cd frontend
npm install
```

#### Start Development Server
```bash
npm start
```

The frontend will be available at: `http://localhost:3000`

## Verification

### Test the Application
1. **Backend Health Check**: Visit `http://localhost:8000/health`
2. **Frontend**: Open `http://localhost:3000`
3. **API Documentation**: Visit `http://localhost:8000/docs`

### Test Basic Functionality
1. Navigate to "Traditional Calculations"
2. Enter test values:
   - Span Length: 4.2m
   - Joist Spacing: 450mm
   - Building Level: L1
3. Click "Calculate Materials"
4. Verify results appear with cutting list

## Development Workflow

### Project Structure
```
checkmeasure-ai/
├── backend/
│   ├── main.py              # FastAPI application entry
│   ├── api/routers/         # API endpoints
│   ├── core/                # Business logic
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── utils/           # API client
│   │   └── types/           # TypeScript types
│   └── package.json         # Node dependencies
└── docs/                    # Documentation
```

### Common Development Tasks

#### Running Tests
```bash
# Backend tests
cd backend
python3 test_basic.py

# Frontend tests (if available)
cd frontend
npm test
```

#### Code Quality
```bash
# Python formatting (if available)
cd backend
black .
flake8 .

# TypeScript checking
cd frontend
npm run type-check
```

#### Building for Production
```bash
# Frontend build
cd frontend
npm run build

# Backend is ready for production as-is
```

## Troubleshooting

### Common Issues

#### Backend Won't Start
- **Check Python version**: `python3 --version` (should be 3.11+)
- **Install dependencies**: `pip install -r requirements.txt`
- **Check port availability**: Make sure port 8000 isn't in use

#### Frontend Won't Start
- **Check Node version**: `node --version` (should be 18+)
- **Clear cache**: `npm install --force`
- **Check port availability**: Make sure port 3000 isn't in use

#### API Connection Issues
- **CORS errors**: Check backend CORS settings
- **Network issues**: Verify backend is running on port 8000
- **Firewall**: Check if firewall is blocking connections

### Development Tips

#### Hot Reloading
- **Backend**: Uses uvicorn's `--reload` flag
- **Frontend**: React's built-in hot reloading

#### Debugging
- **Backend**: Add `print()` statements or use Python debugger
- **Frontend**: Use browser DevTools and React DevTools extension

#### API Testing
- **Swagger UI**: Visit `http://localhost:8000/docs`
- **Postman**: Import API endpoints for testing
- **curl**: Command-line API testing

## Next Steps

Once your development environment is set up:

1. **Read the [Architecture Guide](ARCHITECTURE.md)**
2. **Explore the [API Documentation](API.md)**
3. **Check out [Deployment Guide](DEPLOYMENT.md)**
4. **Start developing!**

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/yourusername/checkmeasure-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/checkmeasure-ai/discussions)
- **Documentation**: Check other files in the `docs/` folder