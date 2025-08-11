#!/bin/bash

echo "========================================="
echo "Starting All Applications"
echo "========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Kill any existing processes
echo -e "${YELLOW}Cleaning up existing processes...${NC}"
pkill -f "react-scripts" 2>/dev/null
pkill -f "electron" 2>/dev/null
pkill -f "uvicorn" 2>/dev/null
pkill -f "python.*run_api" 2>/dev/null
sleep 2

# Start API Server (needed for full functionality)
echo -e "\n${YELLOW}1. Starting API Server...${NC}"
cd /Users/pranay/Projects/LLM/video/ner
if [ -f "run_api.py" ]; then
    python run_api.py > api.log 2>&1 &
    API_PID=$!
    echo -e "${GREEN}✓ API Server started (PID: $API_PID)${NC}"
    echo "   Check logs: tail -f api.log"
    sleep 3
else
    echo -e "${RED}✗ run_api.py not found${NC}"
fi

# Start React App
echo -e "\n${YELLOW}2. Starting React App...${NC}"
cd /Users/pranay/Projects/LLM/video/ner/frontend
if [ -f "package.json" ]; then
    # Set environment variables
    export REACT_APP_API_URL=http://localhost:8000
    export REACT_APP_ENVIRONMENT=development
    
    npm start > react.log 2>&1 &
    REACT_PID=$!
    echo -e "${GREEN}✓ React app starting (PID: $REACT_PID)${NC}"
    echo "   URL: http://localhost:3000"
    echo "   Logs: tail -f react.log"
    
    # Wait for React to start
    sleep 5
else
    echo -e "${RED}✗ React app package.json not found${NC}"
fi

# Start Electron App
echo -e "\n${YELLOW}3. Starting Electron App...${NC}"
cd /Users/pranay/Projects/LLM/video/ner/desktop_app
if [ -f "package.json" ]; then
    # Electron will connect to the running React app
    npm run electron-only > electron.log 2>&1 &
    ELECTRON_PID=$!
    echo -e "${GREEN}✓ Electron app starting (PID: $ELECTRON_PID)${NC}"
    echo "   Logs: tail -f electron.log"
else
    echo -e "${RED}✗ Electron app package.json not found${NC}"
fi

# React Native setup instructions
echo -e "\n${YELLOW}4. React Native App${NC}"
echo "   To run React Native:"
echo "   iOS:     cd mobile && npm run ios"
echo "   Android: cd mobile && npm run android"

echo -e "\n========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================="
echo
echo "Services running:"
echo "  • API Server:    http://localhost:8000/docs"
echo "  • React App:     http://localhost:3000"
echo "  • Electron:      Desktop application"
echo
echo "New Features Available:"
echo "  • Real-time Translation: /translation"
echo "  • Distributed Processing Monitor: /distributed"
echo
echo "To stop all services:"
echo "  pkill -f 'react-scripts|electron|uvicorn|run_api'"
echo
echo "To view logs:"
echo "  API:      tail -f api.log"
echo "  React:    tail -f frontend/react.log"
echo "  Electron: tail -f desktop_app/electron.log"