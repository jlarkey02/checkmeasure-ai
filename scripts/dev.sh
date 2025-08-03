#!/bin/bash

echo "🚀 Starting CheckMeasureAI Development Servers"
echo "=============================================="

# Check if ports are already in use
PORT_8000=$(lsof -ti:8000 2>/dev/null)
PORT_3000=$(lsof -ti:3000 2>/dev/null)

if [ ! -z "$PORT_8000" ] || [ ! -z "$PORT_3000" ]; then
    echo "⚠️  Ports already in use!"
    [ ! -z "$PORT_8000" ] && echo "   Port 8000: PID $PORT_8000"
    [ ! -z "$PORT_3000" ] && echo "   Port 3000: PID $PORT_3000"
    echo ""
    echo "Run './scripts/stop.sh' to stop existing servers"
    exit 1
fi

# Function to kill background processes on script exit
cleanup() {
    echo ""
    echo "🛑 Stopping development servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

# Set up cleanup on script termination
trap cleanup SIGINT SIGTERM EXIT

# Start backend
echo ""
echo "🐍 Starting Backend (Port 8000)..."
cd backend
# Use explicit uvicorn command with all settings
python3 -m uvicorn main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --timeout-keep-alive 0 \
    --timeout-graceful-shutdown 0 \
    --workers 1 \
    --loop asyncio \
    --log-level info &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Wait for backend to start with retries
echo "⏳ Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend started successfully"
        break
    fi
    if [ $i -eq 10 ]; then
        echo "❌ Backend failed to start after 10 seconds"
        echo "Check backend logs for errors"
        exit 1
    fi
    sleep 1
done

# Start frontend
echo ""
echo "⚛️  Starting Frontend (Port 3000)..."
cd ../frontend
npm start &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "🌐 Application URLs:"
echo "- Frontend: http://localhost:3000"
echo "- Backend:  http://localhost:8000"
echo "- API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Tips:"
echo "- Press Ctrl+C to stop both servers"
echo "- Backend logs will appear below"
echo "- Frontend will open in your browser automatically"
echo ""
echo "📝 Development servers running..."
echo "=================================="

# Wait for processes to finish
wait $BACKEND_PID $FRONTEND_PID