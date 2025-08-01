#!/bin/bash

# Kill any existing Streamlit processes on port 8501
echo "Checking for existing Streamlit processes..."
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Activate virtual environment if it exists
if [ -d "../venv" ]; then
    echo "Activating virtual environment..."
    source ../venv/bin/activate
fi

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Start the desktop app
echo "Starting desktop app..."
npm run dev