#!/bin/bash
echo "🚀 Setting up Docker environment for CheckMeasureAI..."

# Create necessary directories
mkdir -p uploads temp nginx/ssl

# Create .gitignore entries if they don't exist
if ! grep -q "uploads/" .gitignore 2>/dev/null; then
    echo "uploads/" >> .gitignore
fi

if ! grep -q "temp/" .gitignore 2>/dev/null; then
    echo "temp/" >> .gitignore
fi

if ! grep -q "docker-compose.override.yml" .gitignore 2>/dev/null; then
    echo "docker-compose.override.yml" >> .gitignore
fi

if ! grep -q ".env.prod" .gitignore 2>/dev/null; then
    echo ".env.prod" >> .gitignore
fi

# Copy environment file
if [ -f "backend/.env" ]; then
    cp backend/.env .env
    echo "✅ Copied .env file"
else
    echo "⚠️  No .env file found in backend/"
fi

# Make scripts executable
chmod +x setup-docker.sh

echo "✅ Docker environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Review the .env file in the root directory"
echo "2. Run 'make up' to start services"
echo "3. Access the app at http://localhost:3000"