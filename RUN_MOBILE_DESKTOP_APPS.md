# Running Mobile and Desktop Applications

## Next Tasks (Priority Order)
1. **Task 33: Security Integration** - Integrate security features into the main app
2. **Task 54: API Platform** - Build comprehensive REST API with documentation
3. **Task 40: Real-time Collaboration** - Add multi-user live features

## Initial Setup (Run Once)
```bash
# From project root
./setup_apps.sh
```

## Desktop App (Electron)

### Prerequisites
- Python 3.x installed
- Virtual environment activated: `source venv/bin/activate`
- Port 8501 available

### Development Mode
```bash
# Option 1: Using the run script (recommended)
cd desktop_app
./run_desktop.sh

# Option 2: Manual start
cd desktop_app
npm install
npm run dev  # Runs Python backend + Electron app together
```

### Troubleshooting Desktop App
```bash
# Kill existing Streamlit process
lsof -ti:8501 | xargs kill -9

# Start Python backend manually
cd .. && python -m streamlit run app.py --server.port 8501

# Then in another terminal
cd desktop_app && npm start
```

### Building for Distribution
```bash
# Windows
npm run build-win

# macOS  
npm run build-mac

# Linux
npm run build-linux

# All platforms
npm run dist
```

## Mobile App (React Native/Expo)

### Prerequisites
- Node.js 16+ installed
- Expo CLI: `npm install -g expo-cli` (or use npx)

### Development Mode
```bash
cd mobile_app
npm install

# Using npx (recommended)
npx expo start

# Or if Expo CLI is installed globally
expo start
```

After starting Expo:
- Press `a` - Run on Android emulator
- Press `i` - Run on iOS simulator  
- Scan QR code - Run on physical device using Expo Go app

### Building for Distribution
```bash
# Using EAS Build (recommended)
npx eas build --platform android
npx eas build --platform ios

# Or traditional build commands
npm run build:android
npm run build:ios
```

### Other Commands
- `npx expo start --clear` - Start with cache cleared
- `npm run android` - Run directly on Android
- `npm run ios` - Run directly on iOS
- `npm run web` - Run in web browser

## Important Notes

1. **Backend Connection**: 
   - Desktop: Connects to Streamlit on port 8501
   - Mobile: Connects to API on port 8000 (update in TranscriptionService.js)
   
2. **Python Environment**: Always activate virtual environment before running desktop app
   ```bash
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. **Dependencies**: 
   - Node.js 16+ and npm
   - Python 3.x with all requirements installed
   - For mobile: Expo Go app on physical device

4. **Mobile Development Setup**: 
   - Android: Android Studio with emulator
   - iOS: Xcode (macOS only)
   - Physical device: Same network as development machine

## Common Issues & Solutions

### Desktop App
- **Port 8501 in use**: Kill existing process with `lsof -ti:8501 | xargs kill -9`
- **Python not found**: Ensure virtual environment is activated
- **Missing icon**: Temporary placeholder created, replace with actual icon

### Mobile App  
- **Expo not found**: Use `npx expo` instead of `expo` command
- **AsyncStorage error**: Fixed in package.json, run `npm install` again
- **Network error**: Update API URL in TranscriptionService.js for your network

## Quick Start Commands

```bash
# One-time setup (from project root)
./setup_apps.sh

# Desktop (from project root)
source venv/bin/activate
cd desktop_app && ./run_desktop.sh

# Mobile (from project root)  
cd mobile_app && npx expo start
```