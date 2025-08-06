# Frontend Directory Deprecation Notice

## Status: DEPRECATED

The `/frontend` directory contains incomplete React/TypeScript components that are not part of a functioning application.

## Current State
- Contains TypeScript component files (.tsx)
- No package.json or build configuration
- No index.html or app entry point
- Components appear to be design mockups or incomplete implementations

## Active Frontend Applications
The project has three fully functional frontend applications:

1. **Main Streamlit App** (`app.py`)
   - Primary web interface
   - Full feature set
   - Now supports both API and direct mode

2. **Desktop Application** (`/desktop_app`)
   - Electron-based desktop app
   - React frontend with TypeScript
   - Fully integrated with API

3. **Mobile Application** (`/mobile`)
   - React Native mobile app
   - Cross-platform (iOS/Android)
   - API-integrated

## Recommendation
The `/frontend` directory should be:
1. Archived for reference (components could be useful for future development)
2. Removed from active development consideration
3. Not included in deployment or build processes

## Migration Path
If any components from `/frontend` are needed:
1. Copy the component to the appropriate active frontend
2. Update imports and dependencies
3. Integrate with the existing application structure

---
Date: 2025-08-04
Status: Officially Deprecated