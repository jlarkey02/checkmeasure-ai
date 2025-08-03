#!/bin/bash

echo "🛑 Stopping CheckMeasureAI Servers"
echo "================================="

# Kill Python backend processes
BACKEND_PIDS=$(pgrep -f "python.*main.py")
if [ ! -z "$BACKEND_PIDS" ]; then
    echo "📍 Found backend process(es): $BACKEND_PIDS"
    kill $BACKEND_PIDS 2>/dev/null
    echo "✅ Backend stopped"
else
    echo "ℹ️  No backend processes found"
fi

# Kill Node frontend processes
FRONTEND_PIDS=$(pgrep -f "node.*react-scripts")
if [ ! -z "$FRONTEND_PIDS" ]; then
    echo "📍 Found frontend process(es): $FRONTEND_PIDS"
    kill $FRONTEND_PIDS 2>/dev/null
    echo "✅ Frontend stopped"
else
    echo "ℹ️  No frontend processes found"
fi

# Check if any processes are still using the ports
echo ""
echo "🔍 Checking ports..."

PORT_8000=$(lsof -ti:8000 2>/dev/null)
if [ ! -z "$PORT_8000" ]; then
    echo "⚠️  Port 8000 still in use by PID: $PORT_8000"
    echo "   Run 'kill $PORT_8000' to force stop"
else
    echo "✅ Port 8000 is free"
fi

PORT_3000=$(lsof -ti:3000 2>/dev/null)
if [ ! -z "$PORT_3000" ]; then
    echo "⚠️  Port 3000 still in use by PID: $PORT_3000"
    echo "   Run 'kill $PORT_3000' to force stop"
else
    echo "✅ Port 3000 is free"
fi

echo ""
echo "✨ Done!"