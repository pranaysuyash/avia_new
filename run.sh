#!/bin/bash

# Audio/Video Transcription App - Quick Start Script
# One-command deployment for Unix-like systems (macOS, Linux)

set -e  # Exit on any error

echo "🎵 Audio/Video Transcription App - Quick Start"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "💡 Please install Python 3.8+ and try again."
    exit 1
fi

# Check if pip is available
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip is required but not installed."
    echo "💡 Please install pip and try again."
    exit 1
fi

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies..."
    python3 -m pip install -r requirements.txt
else
    echo "⚠️ requirements.txt not found. Assuming dependencies are installed."
fi

# Run the startup script
echo "🚀 Starting application..."
python3 start.py