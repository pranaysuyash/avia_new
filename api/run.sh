#!/bin/bash

# Quick start script for the API

echo "🚀 Starting Transcription Platform API..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Run database migrations (if alembic is set up)
# echo "🗄️  Running database migrations..."
# alembic upgrade head

# Start the API
echo "✅ Starting API server..."
python main.py