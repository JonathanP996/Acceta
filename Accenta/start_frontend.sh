#!/bin/bash

# Start Accenta Frontend Server
# Usage: ./start_frontend.sh

cd "$(dirname "$0")/frontend"

echo "🚀 Starting Accenta Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "❌ Dependencies not installed!"
    echo "Installing dependencies..."
    npm install
fi

echo ""
echo "Starting React app on http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

npm start

