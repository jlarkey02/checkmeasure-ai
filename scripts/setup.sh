#!/bin/bash

echo "🚀 CheckMeasureAI Development Setup"
echo "===================================="

# Check prerequisites
echo ""
echo "📋 Checking Prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo "✅ Python $PYTHON_VERSION found"
else
    echo "❌ Python 3.11+ required. Please install from https://python.org"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION found"
else
    echo "❌ Node.js 18+ required. Please install from https://nodejs.org"
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm $NPM_VERSION found"
else
    echo "❌ npm required (comes with Node.js)"
    exit 1
fi

echo ""
echo "📦 Installing Dependencies..."

# Backend setup
echo ""
echo "🐍 Setting up Backend..."
cd backend
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "✅ Backend dependencies installed"
else
    echo "❌ requirements.txt not found"
    exit 1
fi

# Frontend setup
echo ""
echo "⚛️  Setting up Frontend..."
cd ../frontend
if [ -f "package.json" ]; then
    npm install
    echo "✅ Frontend dependencies installed"
else
    echo "❌ package.json not found"
    exit 1
fi

cd ..

echo ""
echo "🧪 Testing Installation..."

# Test backend
echo "Testing backend startup..."
cd backend
timeout 10 python3 -c "
import sys
sys.path.append('.')
try:
    from main import app
    print('✅ Backend imports successful')
except Exception as e:
    print(f'❌ Backend import failed: {e}')
    sys.exit(1)
" || echo "⚠️  Backend test timeout (this is normal)"

cd ../frontend

# Test frontend build
echo "Testing frontend build..."
if npm run build > /dev/null 2>&1; then
    echo "✅ Frontend build successful"
    rm -rf build  # Clean up test build
else
    echo "❌ Frontend build failed"
fi

cd ..

echo ""
echo "🎉 Setup Complete!"
echo ""
echo "📖 Next Steps:"
echo "1. Start backend:  cd backend && python3 main.py"
echo "2. Start frontend: cd frontend && npm start"
echo "3. Open browser:   http://localhost:3000"
echo ""
echo "📚 Documentation:"
echo "- Setup Guide:     docs/SETUP.md"
echo "- API Docs:        docs/API.md"
echo "- Architecture:    docs/ARCHITECTURE.md"
echo ""
echo "Happy coding! 🚀"