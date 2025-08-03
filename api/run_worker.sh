#!/bin/bash

# Run Celery Worker

echo "🚀 Starting Celery Worker..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run ./run.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it from .env.example"
    exit 1
fi

# Export environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start Celery worker
echo "✅ Starting Celery worker..."
echo "📋 Queues: transcription, video, maintenance"
echo ""

celery -A api.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=transcription,video,maintenance \
    -n worker@%h