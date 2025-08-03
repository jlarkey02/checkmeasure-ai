#!/bin/bash

# Backend auto-restart wrapper
# This script will automatically restart the backend if it crashes or stops

echo "🔄 Backend Auto-Restart Manager"
echo "================================"
echo "This will automatically restart the backend if it stops"
echo "Press Ctrl+C twice to stop completely"
echo ""

RESTART_COUNT=0
MAX_RESTART_DELAY=30
CURRENT_DELAY=2

while true; do
    RESTART_COUNT=$((RESTART_COUNT + 1))
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting backend (attempt #$RESTART_COUNT)..."
    
    # Run uvicorn with all our settings
    python3 -m uvicorn main:app \
        --host 127.0.0.1 \
        --port 8000 \
        --timeout-keep-alive 0 \
        --timeout-graceful-shutdown 0 \
        --workers 1 \
        --loop asyncio \
        --log-level info
    
    EXIT_CODE=$?
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Backend stopped with exit code: $EXIT_CODE"
    
    # Check exit code
    case $EXIT_CODE in
        0)
            echo "Backend exited cleanly"
            CURRENT_DELAY=2
            ;;
        130)
            echo "Backend stopped by Ctrl+C (SIGINT)"
            exit 0
            ;;
        *)
            echo "Backend crashed or was terminated"
            # Exponential backoff for restart delay
            if [ $CURRENT_DELAY -lt $MAX_RESTART_DELAY ]; then
                CURRENT_DELAY=$((CURRENT_DELAY * 2))
            fi
            ;;
    esac
    
    echo "Waiting $CURRENT_DELAY seconds before restart..."
    sleep $CURRENT_DELAY
    echo ""
done