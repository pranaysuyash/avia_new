#!/bin/bash

echo "========================================"
echo "Starting Transcription API Server"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade pip
pip install --upgrade pip

# Install API requirements
echo -e "${YELLOW}Installing API dependencies...${NC}"
pip install -r api_requirements.txt

# Install main requirements if needed
if [ -f "requirements.txt" ]; then
    echo -e "${YELLOW}Installing main dependencies...${NC}"
    pip install -r requirements.txt
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p uploads
mkdir -p exports
mkdir -p cache

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export API_ENV="development"
export API_HOST="0.0.0.0"
export API_PORT="8000"

# Check if admin user exists, create if not
echo -e "${YELLOW}Checking admin user...${NC}"
python3 -c "
from security_manager import SecurityManager
sm = SecurityManager()
if not sm.access_control.authenticate_user('admin', 'admin_password123'):
    sm.access_control.create_user('admin', 'admin_password123', 'admin')
    print('Admin user created')
else:
    print('Admin user already exists')
"

# Display API information
echo -e "\n${GREEN}========================================"
echo "API Server Configuration"
echo "========================================"
echo "Host: $API_HOST"
echo "Port: $API_PORT"
echo "Environment: $API_ENV"
echo ""
echo "API Documentation:"
echo "- Swagger UI: http://localhost:${API_PORT}/docs"
echo "- ReDoc: http://localhost:${API_PORT}/redoc"
echo "- OpenAPI JSON: http://localhost:${API_PORT}/openapi.json"
echo ""
echo "Default Admin Credentials:"
echo "- Username: admin"
echo "- Password: admin_password123"
echo ""
echo "Test the API:"
echo "- Health Check: curl http://localhost:${API_PORT}/health"
echo "- API Info: curl http://localhost:${API_PORT}/"
echo "========================================${NC}\n"

# Start the API server
echo -e "${GREEN}Starting FastAPI server...${NC}"
cd api
uvicorn api_main:app \
    --host $API_HOST \
    --port $API_PORT \
    --reload \
    --log-level info \
    --access-log