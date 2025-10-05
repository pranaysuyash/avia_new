#!/bin/bash

# AI Media Platform - Development Stack Startup Script
# Starts both backend API server and frontend development server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print banner
echo -e "${PURPLE}================================================================================${NC}"
echo -e "${CYAN}🚀 AI Media Platform - Development Stack${NC}"
echo -e "${PURPLE}================================================================================${NC}"
echo -e "Starting backend API server and frontend development server..."
echo ""

# Function to cleanup processes on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down development stack...${NC}"
    
    if [ ! -z "$BACKEND_PID" ]; then
        echo -e "${BLUE}🔄 Stopping backend server...${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        wait $BACKEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Backend stopped${NC}"
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}🔄 Stopping frontend server...${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
        wait $FRONTEND_PID 2>/dev/null || true
        echo -e "${GREEN}✅ Frontend stopped${NC}"
    fi
    
    echo -e "${GREEN}👋 Development stack stopped${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

# Check if frontend directory exists
if [ ! -d "frontend-v2" ]; then
    echo -e "${RED}❌ Frontend directory 'frontend-v2' not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies found (using existing environment)${NC}"
echo ""

# Start backend server
echo -e "${BLUE}🔧 Starting backend API server...${NC}"

# Use current Python (should be in virtual environment)
PYTHON_CMD="python"
echo -e "${GREEN}✅ Using current Python environment${NC}"

# Start backend in background
$PYTHON_CMD backend_server.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend is still running
if ! kill -0 $BACKEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Backend server failed to start${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Backend API server started on http://localhost:8000${NC}"
echo -e "${GREEN}📚 API docs available at http://localhost:8000/docs${NC}"

# Start frontend server
echo -e "${BLUE}🎨 Starting frontend development server...${NC}"

cd frontend-v2

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to install frontend dependencies${NC}"
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    fi
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
fi

# Start frontend in background
npm run dev &
FRONTEND_PID=$!

cd ..

# Wait for frontend to start
sleep 5

# Check if frontend is still running
if ! kill -0 $FRONTEND_PID 2>/dev/null; then
    echo -e "${RED}❌ Frontend server failed to start${NC}"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

echo -e "${GREEN}✅ Frontend development server started on http://localhost:5173${NC}"

echo ""
echo -e "${PURPLE}================================================================================${NC}"
echo -e "${CYAN}🎉 Development stack is running!${NC}"
echo -e "${PURPLE}================================================================================${NC}"
echo -e "${GREEN}🔧 Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
echo -e "${GREEN}🎨 Frontend: http://localhost:5173${NC}"
echo ""
echo -e "${YELLOW}💡 Login credentials for testing:${NC}"
echo -e "   Email: dev@example.com"
echo -e "   Password: password"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop all servers${NC}"
echo -e "${PURPLE}================================================================================${NC}"
echo ""

# Wait for processes to finish or be interrupted
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Backend process has stopped unexpectedly${NC}"
        break
    fi
    
    # Check if frontend is still running
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${RED}❌ Frontend process has stopped unexpectedly${NC}"
        break
    fi
    
    sleep 1
done

# If we get here, one of the processes died
cleanup