#!/bin/bash
# Start Celery worker with unique name
cd "$(dirname "$0")"

# Don't attempt to deactivate - this causes issues when run as a script
# Instead, we'll just activate the virtual environment directly

# Check for virtual environment (.venv preferred)
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    VIRTUAL_ENV_PATH="$(pwd)/.venv"
    export VIRTUAL_ENV="$VIRTUAL_ENV_PATH"
    export PATH="$VIRTUAL_ENV_PATH/bin:$PATH"
    unset PYTHONHOME
    echo "Virtual environment activated."
elif [ -d "venv" ]; then
    echo "Activating legacy virtual environment..."
    VIRTUAL_ENV_PATH="$(pwd)/venv"
    export VIRTUAL_ENV="$VIRTUAL_ENV_PATH"
    export PATH="$VIRTUAL_ENV_PATH/bin:$PATH"
    unset PYTHONHOME
    echo "Legacy virtual environment activated."
    echo "Note: Consider migrating to .venv by running setup.sh"
else
    echo "Error: No virtual environment found. Please run setup.sh first."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is not running. Celery worker requires Redis."
    echo "Please start Redis before continuing."
    exit 1
fi

# Generate a truly unique name for this worker
UNIQUE_NAME="jp2forge_worker_$(hostname)_$(date +%s)_$$"
echo "Worker unique name: $UNIQUE_NAME"

# Kill any existing Celery workers
echo "Stopping any existing Celery workers..."
pkill -f "celery worker" || echo "No Celery workers to stop"

# Wait a moment to ensure workers are fully stopped
sleep 2

# Create log directory if it doesn't exist
mkdir -p logs

# Start a new Celery worker with the unique name
echo "Starting Celery worker..."
celery -A jp2forge_web worker -l INFO -n "$UNIQUE_NAME" --concurrency=2 > logs/celery_$(date +%Y%m%d_%H%M%S).log 2>&1