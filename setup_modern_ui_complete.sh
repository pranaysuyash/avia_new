#!/bin/bash

echo "===================================================="
echo "Complete Modern UI Setup for Desktop and Mobile Apps"
echo "===================================================="

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed. Please install Node.js first.${NC}"
    exit 1
fi

# Desktop React App Setup
echo -e "\n${YELLOW}1. Setting up Desktop React App...${NC}"
cd desktop_app/src/renderer

# Clean any existing node_modules
if [ -d "node_modules" ]; then
    echo "   - Cleaning existing node_modules..."
    rm -rf node_modules package-lock.json
fi

# Create necessary directories
echo "   - Creating component directories..."
mkdir -p src/components/{layout,dashboard,workspace,common,animations}
mkdir -p src/screens src/services src/store/slices src/styles src/utils
mkdir -p src/contexts src/hooks

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
        secondary: {
          500: '#8B5CF6',
          600: '#7C3AED',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s ease-in-out infinite',
        'slide-in': 'slideIn 0.3s ease-out',
        'fade-in': 'fadeIn 0.3s ease-in',
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

# Create tsconfig if it doesn't exist
if [ ! -f "tsconfig.json" ]; then
    echo "   - Creating TypeScript configuration..."
    cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
EOF
fi

echo -e "   ${GREEN}✅ Desktop React app setup complete!${NC}"
echo "   To start: cd desktop_app/src/renderer && npm start"

# Update Electron main.js to load React
echo -e "\n${YELLOW}2. Updating Electron configuration...${NC}"
cd ../../

# Backup main.js if not already backed up
if [ ! -f "src/main.js.backup" ]; then
    cp src/main.js src/main.js.backup
    echo "   - Created backup of main.js"
fi

# Add React configuration to main.js
if ! grep -q "REACT_DEV_URL" src/main.js; then
    echo "   - Adding React app URL configuration..."
    # Create a temporary file with the new configuration
    cat > src/main_react_config.tmp << 'EOF'
// REACT_APP_URL - Configuration for React UI
const REACT_DEV_URL = "http://localhost:3000";
const USE_REACT = true; // Set to true to use React UI, false for Streamlit

EOF
    
    # Prepend to main.js
    cat src/main_react_config.tmp src/main.js > src/main_new.js
    mv src/main_new.js src/main.js
    rm src/main_react_config.tmp
fi

echo -e "   ${GREEN}✅ Electron configuration updated!${NC}"

# Mobile App Setup
echo -e "\n${YELLOW}3. Setting up Mobile App...${NC}"
cd ../mobile_app

if [ ! -d "node_modules" ]; then
    echo "   - Installing mobile app dependencies..."
    npm install
    
    # Install additional UI dependencies
    echo "   - Installing UI enhancement packages..."
    npm install react-native-linear-gradient react-native-reanimated
    
    echo -e "   ${GREEN}✅ Mobile app dependencies installed!${NC}"
else
    echo -e "   ${GREEN}✅ Mobile app dependencies already installed${NC}"
fi

# Create modern components directory if it doesn't exist
if [ ! -d "src/components/modern" ]; then
    echo "   - Creating modern components directory..."
    mkdir -p src/components/modern
fi

# Back to root
cd ..

# Create a quick start script
echo -e "\n${YELLOW}4. Creating quick start scripts...${NC}"

# Desktop start script
cat > start_desktop_modern.sh << 'EOF'
#!/bin/bash
echo "Starting Modern Desktop App..."

# Terminal 1: Start React development server
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"'/desktop_app/src/renderer && npm start"'

# Wait for React to start
echo "Waiting for React dev server to start..."
sleep 5

# Terminal 2: Start Electron
osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"'/desktop_app && npm start"'

echo "Desktop app starting in separate terminals..."
EOF

# Mobile start script
cat > start_mobile_modern.sh << 'EOF'
#!/bin/bash
echo "Starting Modern Mobile App..."
cd mobile_app && npx expo start
EOF

chmod +x start_desktop_modern.sh start_mobile_modern.sh

echo -e "${GREEN}✅ Created quick start scripts!${NC}"

# Summary
echo -e "\n${GREEN}===================================================="
echo "Setup Complete! 🎉"
echo "====================================================${NC}"
echo ""
echo "Quick Start Commands:"
echo ""
echo -e "${YELLOW}Desktop App:${NC}"
echo "  Option 1: ./start_desktop_modern.sh (opens in new terminals)"
echo "  Option 2: Manual start:"
echo "    Terminal 1: cd desktop_app/src/renderer && npm start"
echo "    Terminal 2: cd desktop_app && npm start"
echo ""
echo -e "${YELLOW}Mobile App:${NC}"
echo "  Option 1: ./start_mobile_modern.sh"
echo "  Option 2: cd mobile_app && npx expo start"
echo ""
echo -e "${YELLOW}Important Notes:${NC}"
echo "- Desktop app will now load React UI instead of Streamlit"
echo "- To switch back to Streamlit, edit USE_REACT in desktop_app/src/main.js"
echo "- Mobile app uses system theme (dark/light) automatically"
echo "- Both apps share the same design system (Indigo primary color)"
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "- If npm install fails, use: npm install --legacy-peer-deps"
echo "- If ports are busy, kill processes on ports 3000 and 8501"
echo "- Clear cache: npm start -- --reset-cache"
echo ""
echo -e "${GREEN}Ready to build amazing transcription apps! 🚀${NC}"