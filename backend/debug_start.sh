#!/bin/bash

echo "Starting backend with debug wrapper..."
echo "PID: $$"
echo "Time: $(date)"

# Trap all signals
trap 'echo "Caught signal: $?"; exit' SIGINT SIGTERM SIGHUP

# Run Python with verbose output
python3 -u main.py 2>&1

EXIT_CODE=$?
echo ""
echo "Backend exited with code: $EXIT_CODE"
echo "Time: $(date)"

# Check exit code
if [ $EXIT_CODE -eq 0 ]; then
    echo "Clean exit"
elif [ $EXIT_CODE -eq 1 ]; then
    echo "General error"
elif [ $EXIT_CODE -eq 130 ]; then
    echo "Interrupted by Ctrl+C"
else
    echo "Unknown exit code: $EXIT_CODE"
fi