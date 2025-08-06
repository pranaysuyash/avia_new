# Desktop App

This is the Electron desktop application for the transcription service.

## Quick Start

### Method 1: Simple Mode (Recommended for Development)
```bash
# From the desktop_app directory
./run-simple.sh
```

This will:
1. Install dependencies if needed
2. Start the React development server
3. Launch the Electron app

### Method 2: Manual Steps
```bash
# Terminal 1: Start React dev server
cd src/renderer
npm install
npm start

# Terminal 2: Start Electron (after React is running)
cd desktop_app
npm install
npm start
```

### Method 3: With Backend
```bash
# Terminal 1: Start API backend
cd /Users/pranay/Projects/LLM/video/ner
python api/app.py

# Terminal 2: Start React dev server
cd desktop_app/src/renderer
npm start

# Terminal 3: Start Electron
cd desktop_app
npm run dev
```

## Troubleshooting

### React dev server not starting
- Make sure port 3000 is free: `lsof -i :3000`
- Kill any stuck processes: `killall -9 node`

### Electron window shows error
- Make sure React dev server is running on http://localhost:3000
- Press Cmd+R (Mac) or Ctrl+R (Windows/Linux) to reload

### Dependencies issues
```bash
# Clean install
rm -rf node_modules src/renderer/node_modules
npm install
cd src/renderer && npm install
```

## Development

- React app source: `src/renderer/src/`
- Electron main process: `src/main.js` (full) or `src/main-simple.js` (simple)
- Preload script: `src/preload.js`

## Building for Production

```bash
# Build React app first
cd src/renderer
npm run build

# Then build Electron app
cd ../..
npm run build-mac  # or build-win, build-linux
```