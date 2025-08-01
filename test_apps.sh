#!/bin/bash

echo "Testing Desktop and Mobile Apps Setup"
echo "====================================="

# Test Desktop App
echo -e "\n1. Testing Desktop App..."
cd desktop_app

# Check if Streamlit is running
if lsof -i :8501 | grep -q LISTEN; then
    echo "   ✅ Streamlit backend is running on port 8501"
else
    echo "   ❌ Streamlit backend is NOT running"
    echo "   Please run: python -m streamlit run app.py"
fi

# Check if npm dependencies are installed
if [ -d "node_modules" ]; then
    echo "   ✅ Desktop app dependencies are installed"
else
    echo "   ❌ Desktop app dependencies NOT installed"
    echo "   Please run: npm install"
fi

# Check if Electron can start
if command -v electron &> /dev/null || [ -f "node_modules/.bin/electron" ]; then
    echo "   ✅ Electron is available"
else
    echo "   ❌ Electron is NOT available"
fi

# Test Mobile App
echo -e "\n2. Testing Mobile App..."
cd ../mobile_app

# Check if npm dependencies are installed
if [ -d "node_modules" ]; then
    echo "   ✅ Mobile app dependencies are installed"
else
    echo "   ❌ Mobile app dependencies NOT installed"
    echo "   Note: The dependencies might take time to install due to React Native/Expo size"
fi

# Check if Expo is available
if command -v expo &> /dev/null || command -v npx &> /dev/null; then
    echo "   ✅ Can run Expo (via npx)"
else
    echo "   ❌ Cannot run Expo"
fi

echo -e "\n====================================="
echo "Summary:"
echo "- Desktop app: Should open Electron window connected to Streamlit"
echo "- Mobile app: Requires Expo Go app on phone or emulator"
echo -e "\nQuick commands:"
echo "Desktop: cd desktop_app && npm start"
echo "Mobile: cd mobile_app && npx expo start --tunnel"