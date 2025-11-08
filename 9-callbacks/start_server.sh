#!/bin/bash
# Start ADK web server for AccentCoachAgent

cd "$(dirname "$0")"
source ../.venv/bin/activate

# Check if port 8000 is available, otherwise use 8001
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Port 8000 is in use, using port 8001 instead"
    PORT=8001
else
    PORT=8000
fi

echo "Starting ADK web server on port $PORT..."
echo "Open http://localhost:$PORT in your browser"
echo ""

adk web . --port $PORT

