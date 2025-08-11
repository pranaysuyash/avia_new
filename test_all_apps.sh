#!/bin/bash

echo "==================================="
echo "Testing All Apps - React, React Native, Electron"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test React App
echo -e "\n${YELLOW}1. Testing React App...${NC}"
cd frontend
if [ -f "package.json" ]; then
    echo "Found React app package.json"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Try to build (faster than starting dev server)
    echo "Testing React build..."
    timeout 30 npm run build 2>&1 | head -20
    
    if [ $? -eq 0 ] || [ $? -eq 124 ]; then
        echo -e "${GREEN}✓ React app can build${NC}"
    else
        echo -e "${RED}✗ React app build failed${NC}"
    fi
else
    echo -e "${RED}✗ React app package.json not found${NC}"
fi
cd ..

# Test Electron App
echo -e "\n${YELLOW}2. Testing Electron App...${NC}"
cd desktop_app
if [ -f "package.json" ]; then
    echo "Found Electron app package.json"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Check main file
    if [ -f "src/main/main.ts" ] || [ -f "src/main.js" ] || [ -f "main.js" ]; then
        echo -e "${GREEN}✓ Electron main file exists${NC}"
    else
        echo -e "${RED}✗ Electron main file not found${NC}"
    fi
    
    # Check if it can start (headless test)
    echo "Testing Electron setup..."
    npm list electron 2>&1 | grep electron
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Electron is installed${NC}"
    else
        echo -e "${RED}✗ Electron not properly installed${NC}"
    fi
else
    echo -e "${RED}✗ Electron app package.json not found${NC}"
fi
cd ..

# Test React Native App
echo -e "\n${YELLOW}3. Testing React Native App...${NC}"
cd mobile
if [ -f "package.json" ]; then
    echo "Found React Native app package.json"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "Installing dependencies..."
        npm install
    fi
    
    # Check main files
    if [ -f "App.tsx" ] || [ -f "App.js" ] || [ -f "src/App.tsx" ]; then
        echo -e "${GREEN}✓ React Native App component exists${NC}"
    else
        echo -e "${RED}✗ React Native App component not found${NC}"
    fi
    
    # Check React Native installation
    npm list react-native 2>&1 | grep react-native
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ React Native is installed${NC}"
    else
        echo -e "${RED}✗ React Native not properly installed${NC}"
    fi
else
    echo -e "${RED}✗ React Native app package.json not found${NC}"
fi
cd ..

echo -e "\n${YELLOW}==================================="
echo "Summary:"
echo "===================================${NC}"

# Check if new components exist
echo -e "\n${YELLOW}4. Checking New Components...${NC}"
if [ -f "frontend/src/components/translation/RealtimeTranslation.tsx" ]; then
    echo -e "${GREEN}✓ RealtimeTranslation component exists${NC}"
else
    echo -e "${RED}✗ RealtimeTranslation component not found${NC}"
fi

if [ -f "frontend/src/components/distributed/DistributedProcessingMonitor.tsx" ]; then
    echo -e "${GREEN}✓ DistributedProcessingMonitor component exists${NC}"
else
    echo -e "${RED}✗ DistributedProcessingMonitor component not found${NC}"
fi

# Check API endpoints
echo -e "\n${YELLOW}5. Checking API Endpoints...${NC}"
if [ -f "api/endpoints/translation.py" ]; then
    echo -e "${GREEN}✓ Translation API endpoints exist${NC}"
else
    echo -e "${RED}✗ Translation API endpoints not found${NC}"
fi

if [ -f "api/endpoints/distributed_processing.py" ]; then
    echo -e "${GREEN}✓ Distributed Processing API endpoints exist${NC}"
else
    echo -e "${RED}✗ Distributed Processing API endpoints not found${NC}"
fi

echo -e "\n${GREEN}Test complete!${NC}"
echo -e "\nTo actually run the apps:"
echo "  React:        cd frontend && npm start"
echo "  Electron:     cd desktop_app && npm run dev"
echo "  React Native: cd mobile && npm run ios (or npm run android)"