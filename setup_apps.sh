#!/bin/bash

echo "Setting up Desktop and Mobile Apps"
echo "=================================="

# Desktop App Setup
echo -e "\n1. Setting up Desktop App..."
cd desktop_app

# Kill any existing Streamlit on port 8501
echo "   - Killing existing Streamlit processes..."
lsof -ti:8501 | xargs kill -9 2>/dev/null || true

# Install desktop dependencies
echo "   - Installing desktop app dependencies..."
npm install

echo "   ✅ Desktop app ready!"
echo "   To run: cd desktop_app && npm run dev"

# Mobile App Setup
echo -e "\n2. Setting up Mobile App..."
cd ../mobile_app

# Install Expo CLI globally if not installed
if ! command -v expo &> /dev/null; then
    echo "   - Installing Expo CLI globally..."
    npm install -g expo-cli
fi

# Install mobile dependencies
echo "   - Installing mobile app dependencies..."
npm install

echo "   ✅ Mobile app ready!"
echo "   To run: cd mobile_app && npx expo start"

# Back to root
cd ..

echo -e "\n=================================="
echo "Setup Complete!"
echo -e "\nQuick Start Commands:"
echo "Desktop: cd desktop_app && ./run_desktop.sh"
echo "Mobile:  cd mobile_app && npx expo start"
echo -e "\nNote: Make sure Python virtual environment is activated for desktop app"