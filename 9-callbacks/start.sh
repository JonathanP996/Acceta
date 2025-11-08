#!/bin/bash
# Start ADK web server - handles port conflicts

cd "$(dirname "$0")"
source ../.venv/bin/activate

# Kill any process on port 8000
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "Killing process on port 8000..."
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    sleep 1
fi

echo "Starting ADK web server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

adk web .

