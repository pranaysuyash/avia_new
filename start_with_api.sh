#!/bin/bash
# Start the application with API server

echo "🚀 Starting Audio/Video Transcription System with API..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    if [ ! -z "$API_PID" ]; then
        kill $API_PID 2>/dev/null
    fi
    if [ ! -z "$APP_PID" ]; then
        kill $APP_PID 2>/dev/null
    fi
    exit 0
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Port 8000 is already in use. Please stop the existing service.${NC}"
    exit 1
fi

# Check if port 8501 is already in use
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${RED}❌ Port 8501 is already in use. Please stop the existing Streamlit app.${NC}"
    exit 1
fi

# Start API server
echo -e "${BLUE}Starting API server on http://localhost:8000${NC}"
uvicorn api.app:app --reload --port 8000 &
API_PID=$!

# Wait for API to start
echo -e "${YELLOW}Waiting for API server to start...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/v1/health > /dev/null; then
        echo -e "${GREEN}✅ API server is running!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ API server failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Start Streamlit app
echo -e "${BLUE}Starting Streamlit app on http://localhost:8501${NC}"
streamlit run app.py &
APP_PID=$!

# Wait for Streamlit to start
echo -e "${YELLOW}Waiting for Streamlit app to start...${NC}"
sleep 5

# Open browser (optional - comment out if not desired)
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
fi

echo -e "${GREEN}✅ System is running!${NC}"
echo -e "${BLUE}API Docs: http://localhost:8000/api/docs${NC}"
echo -e "${BLUE}App: http://localhost:8501${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep script running
wait