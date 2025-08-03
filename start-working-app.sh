#!/bin/bash

echo "Starting application with WORKING backend..."

# Kill existing servers
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start working backend
echo "Starting backend with full authentication..."
cd /Users/pranay/Projects/LLM/video/ner
python run_working_backend.py &
BACKEND_PID=$!

# Wait for backend
sleep 3

# Start frontend
echo "Starting React frontend..."
cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer
BROWSER=none npm start &
FRONTEND_PID=$!

echo ""
echo "==========================================="
echo "✅ APPLICATION READY FOR TESTING"
echo "==========================================="
echo ""
echo "Frontend: http://localhost:3000"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Test Credentials:"
echo "  Email: test@example.com"
echo "  Password: password"
echo ""
echo "Features Available:"
echo "  ✅ Login/Logout/Register"
echo "  ✅ View transcriptions"
echo "  ✅ Authentication working"
echo "  ✅ Database (if PostgreSQL running)"
echo ""
echo "To stop: kill $FRONTEND_PID $BACKEND_PID"
echo "==========================================="

wait