#!/bin/bash

echo "🚀 Starting All Application Servers"
echo "=================================="

# Kill existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f uvicorn 2>/dev/null
pkill -f streamlit 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f electron 2>/dev/null

sleep 2

# Change to project directory
cd /Users/pranay/Projects/LLM/video/ner

echo ""
echo "🔧 Starting API Server (Port 8001)..."
python run_api.py &
API_PID=$!

echo "🎨 Starting Streamlit App (Port 8501)..."  
streamlit run app.py --server.port 8501 &
STREAMLIT_PID=$!

echo "⚛️ Starting React Frontend (Port 3000)..."
cd frontend
npm start &
REACT_PID=$!

cd ..

echo "🖥️ Starting Electron Desktop..."
cd desktop_app
npm start &
ELECTRON_PID=$!

cd ..

echo "📱 Starting React Native Metro (Mobile)..."
cd mobile
npm start &
METRO_PID=$!

cd ..

echo ""
echo "🎉 All servers starting up!"
echo "=================================="
echo "📍 API Server:      http://localhost:8001/docs"
echo "📍 Streamlit:       http://localhost:8501"  
echo "📍 React Frontend:  http://localhost:3000"
echo "📍 Electron:        Desktop app window"
echo "📍 React Native:    Metro bundler running"
echo ""
echo "⏳ Wait 10-15 seconds for all servers to fully start"
echo "🛑 Press Ctrl+C to stop all servers"
echo ""
echo "📱 FOR MOBILE TESTING:"
echo "   iOS: Open new terminal → cd mobile → npm run ios"
echo "   Android: Open new terminal → cd mobile → npm run android"

# Wait for interrupt
trap 'echo ""; echo "🛑 Stopping all servers..."; kill $API_PID $STREAMLIT_PID $REACT_PID $ELECTRON_PID $METRO_PID 2>/dev/null; exit' INT

# Keep script running
wait