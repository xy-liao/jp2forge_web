#!/bin/bash
# Start Celery worker with unique name
cd "$(dirname "$0")"
source venv/bin/activate

# Generate a truly unique name for this worker
UNIQUE_NAME="jp2forge_worker_$(hostname)_$(date +%s)_$$"
echo "Worker unique name: $UNIQUE_NAME"

# Kill any existing Celery workers
echo "Stopping any existing Celery workers..."
pkill -f "celery worker" || echo "No Celery workers to stop"

# Wait a moment to ensure workers are fully stopped
sleep 2

# Start a new Celery worker with the unique name
echo "Starting Celery worker..."
celery -A jp2forge_web worker -l INFO -n "$UNIQUE_NAME" --concurrency=2