#!/bin/bash

# Kill any existing React processes on port 3000
echo "Checking for existing React processes..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

# Install desktop app npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing desktop app dependencies..."
    npm install
fi

# Install React app dependencies if needed
if [ ! -d "src/renderer/node_modules" ]; then
    echo "Installing React app dependencies..."
    cd src/renderer
    npm install
    cd ../..
fi

# Start the desktop app with React
echo "Starting React-based desktop app..."
npm run dev