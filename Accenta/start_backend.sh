#!/bin/bash

# Start Accenta Backend Server
# Usage: ./start_backend.sh

cd "$(dirname "$0")"

echo "🚀 Starting Accenta Backend..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r backend/requirements.txt
else
    echo "✓ Virtual environment found"
    source venv/bin/activate
fi

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "Installing uvicorn..."
    pip install uvicorn
fi

echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000
