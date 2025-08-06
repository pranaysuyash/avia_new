#!/bin/bash

# Simple script to run Electron app
# This version doesn't start the backend automatically

echo "Starting Electron Desktop App (Simple Mode)..."
echo "============================================"
echo ""

# Change to desktop app directory
cd "$(dirname "$0")"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing desktop app dependencies..."
    npm install
fi

# Check if renderer node_modules exists
if [ ! -d "src/renderer/node_modules" ]; then
    echo "Installing React app dependencies..."
    cd src/renderer
    npm install
    cd ../..
fi

echo ""
echo "Starting React development server..."
echo "Please wait for it to compile..."
echo ""

# Start React dev server in background
cd src/renderer
npm start &
REACT_PID=$!

# Wait for React to start (check if port 3000 is open)
echo "Waiting for React dev server to start..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null; then
        echo "React dev server is ready!"
        break
    fi
    sleep 1
done

# Go back to desktop app root
cd ../..

echo ""
echo "Starting Electron app..."
# Use the simplified main file
ELECTRON_MAIN=src/main-simple.js npm start

# Clean up React process on exit
trap "kill $REACT_PID" EXIT