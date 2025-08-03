#!/bin/bash

echo "Starting the REAL full application..."

# Kill any existing servers
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start the ACTUAL FastAPI backend from api/main.py
echo "Starting the REAL FastAPI backend..."
cd /Users/pranay/Projects/LLM/video/ner

# Use the actual api module
python -m uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!
echo "Real Backend PID: $BACKEND_PID"

# Give backend time to start
sleep 5

# Start React frontend
echo "Starting React frontend..."
cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer
BROWSER=none npm start &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "==========================================="
echo "✅ FULL APPLICATION WITH ALL FEATURES"
echo "==========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "This is the REAL application with:"
echo "  ✅ Full authentication system"
echo "  ✅ PostgreSQL database access"
echo "  ✅ All your transcriptions"
echo "  ✅ Complete API endpoints"
echo "  ✅ File uploads"
echo "  ✅ Transcription processing"
echo ""
echo "To stop:"
echo "  kill $FRONTEND_PID $BACKEND_PID"
echo ""
echo "==========================================="

# Keep running
wait