#!/bin/bash

echo "🔨 Monitoring Docker build progress..."
echo "This may take 5-10 minutes for the first build."
echo ""

while true; do
    # Check if containers exist
    BACKEND=$(docker ps -a | grep checkmeasure-backend | wc -l)
    FRONTEND=$(docker ps -a | grep checkmeasure-frontend | wc -l)
    
    if [ $BACKEND -gt 0 ] && [ $FRONTEND -gt 0 ]; then
        echo "✅ Build complete! Containers created."
        echo ""
        docker-compose ps
        break
    else
        echo -n "⏳ Building... Backend: "
        [ $BACKEND -gt 0 ] && echo -n "✓" || echo -n "building"
        echo -n " | Frontend: "
        [ $FRONTEND -gt 0 ] && echo "✓" || echo "building"
        sleep 5
    fi
done

echo ""
echo "To view logs: make logs"
echo "To access app: http://localhost:3000"