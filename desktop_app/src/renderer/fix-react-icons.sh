#!/bin/bash

echo "Fixing react-icons type compatibility issues..."

# The issue is that react-icons v5 has type issues with React 18
# We need to either downgrade react-icons or update type definitions

cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer

# Option 1: Downgrade to react-icons v4 which has better compatibility
npm uninstall react-icons
npm install react-icons@^4.12.0

echo "✅ Downgraded react-icons to v4 for better type compatibility"