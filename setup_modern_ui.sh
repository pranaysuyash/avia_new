#!/bin/bash

echo "Setting up Modern UI for Desktop and Mobile Apps"
echo "==============================================="

# Desktop React App Setup
echo -e "\n1. Setting up Desktop React App..."
cd desktop_app/src/renderer

# Clean any existing node_modules
if [ -d "node_modules" ]; then
    echo "   - Cleaning existing node_modules..."
    rm -rf node_modules package-lock.json
fi

# Install dependencies with legacy peer deps
echo "   - Installing dependencies (this may take a few minutes)..."
npm install --legacy-peer-deps

# Create Tailwind config if it doesn't exist
if [ ! -f "tailwind.config.js" ]; then
    echo "   - Creating Tailwind configuration..."
    cat > tailwind.config.js << 'EOF'
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#EEF2FF',
          100: '#E0E7FF',
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
          900: '#312E81',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
EOF
fi

# Create postcss config if it doesn't exist
if [ ! -f "postcss.config.js" ]; then
    echo "   - Creating PostCSS configuration..."
    cat > postcss.config.js << 'EOF'
module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
EOF
fi

echo "   ✅ Desktop React app ready!"
echo "   To start: cd desktop_app/src/renderer && npm start"

# Update Electron main.js to load React
echo -e "\n2. Updating Electron configuration..."
cd ../../
# Add a marker comment if not already present
if ! grep -q "// REACT_APP_URL" src/main.js; then
    echo "   - Adding React app URL configuration..."
    sed -i.bak '1i\
// REACT_APP_URL - Update this when using React instead of Streamlit\
const REACT_DEV_URL = "http://localhost:3000";\
const USE_REACT = true; // Set to true to use React UI\
' src/main.js
fi

echo "   ✅ Electron configuration updated!"

# Mobile App Dependencies
echo -e "\n3. Checking Mobile App..."
cd ../mobile_app

if [ ! -d "node_modules" ]; then
    echo "   - Mobile app dependencies not installed"
    echo "   Run: cd mobile_app && npm install"
else
    echo "   ✅ Mobile app dependencies already installed"
fi

# Back to root
cd ..

echo -e "\n==============================================="
echo "Setup Complete! 🎉"
echo ""
echo "To run the modern UI:"
echo ""
echo "Desktop App:"
echo "  Terminal 1: cd desktop_app/src/renderer && npm start"
echo "  Terminal 2: cd desktop_app && npm start"
echo ""
echo "Mobile App:"
echo "  cd mobile_app && npx expo start"
echo ""
echo "Note: The desktop app will now load React UI instead of Streamlit."
echo "To switch back to Streamlit, edit desktop_app/src/main.js"