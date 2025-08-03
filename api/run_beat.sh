#!/bin/bash

# Run Celery Beat Scheduler

echo "🚀 Starting Celery Beat Scheduler..."

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

# Start Celery beat
echo "✅ Starting Celery beat scheduler..."
echo "📅 Scheduled tasks:"
echo "  - cleanup-old-files: Daily"
echo "  - update-storage-stats: Hourly"
echo ""

celery -A api.celery_app beat --loglevel=info