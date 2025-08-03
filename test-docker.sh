#!/bin/bash

echo "Testing Docker setup..."

# Test 1: Docker is running
if docker info > /dev/null 2>&1; then
    echo "✅ Docker is running"
else
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Test 2: Docker Compose is available
if docker-compose version > /dev/null 2>&1; then
    echo "✅ Docker Compose is available"
else
    echo "❌ Docker Compose is not available"
    exit 1
fi

# Test 3: Required files exist
if [ -f "docker-compose.yml" ] && [ -f "backend/Dockerfile" ] && [ -f "frontend/Dockerfile" ]; then
    echo "✅ All Docker files exist"
else
    echo "❌ Missing Docker files"
    exit 1
fi

# Test 4: Environment file exists
if [ -f ".env" ]; then
    echo "✅ Environment file exists"
else
    echo "⚠️  No .env file found - copying from backend/.env"
    cp backend/.env .env
fi

echo ""
echo "Docker setup is ready! You can now run:"
echo "  make up     - to start all services"
echo "  make logs   - to view logs"
echo "  make down   - to stop services"