#!/bin/bash

echo "Starting servers for manual testing..."

# Kill any existing servers
echo "Cleaning up existing servers..."
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the simple FastAPI backend
echo "Starting FastAPI backend on port 8000..."
cd /Users/pranay/Projects/LLM/video/ner
python test_api.py &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"

# Give backend time to start
sleep 2

# Start React frontend
echo "Starting React frontend on port 3000..."
cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer
npm start &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "==========================================="
echo "Servers are starting up..."
echo "==========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo ""
echo "Backend API endpoints:"
echo "  - http://localhost:8000/api/health"
echo "  - http://localhost:8000/api/auth/me"
echo ""
echo "To stop the servers, run:"
echo "  kill $FRONTEND_PID $BACKEND_PID"
echo "  OR"
echo "  lsof -ti:3000 | xargs kill -9"
echo "  lsof -ti:8000 | xargs kill -9"
echo ""
echo "==========================================="

# Keep script running
wait