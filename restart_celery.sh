#!/bin/bash
# Restart Celery worker - useful after code changes
# This simple script provides a convenient way to restart Celery workers
# without having to remember the exact commands

echo "Restarting JP2Forge Celery worker..."

# Kill any existing Celery worker processes
echo "Stopping existing Celery workers..."
pkill -f "celery worker" || echo "No Celery workers running"

# Wait a moment for processes to terminate
echo "Waiting for processes to terminate..."
sleep 2

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Activate virtual environment
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: No virtual environment found."
    exit 1
fi

# Start a new Celery worker
echo "Starting new Celery worker..."
celery -A jp2forge_web worker -l INFO

echo "Celery worker restarted successfully."