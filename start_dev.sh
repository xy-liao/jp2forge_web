#!/bin/bash

# Script to start the JP2Forge Web application in development mode
# This will start both the Django development server and Celery worker

# Function to cleanup on exit
cleanup() {
    echo "Shutting down services..."
    
    # Kill the Django server process
    if [ -n "$DJANGO_PID" ]; then
        kill $DJANGO_PID
        echo "Django server stopped."
    fi
    
    # Kill the Celery worker process
    if [ -n "$CELERY_PID" ]; then
        kill $CELERY_PID
        echo "Celery worker stopped."
    fi
    
    exit 0
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

# Deactivate any active virtual environments first
# This ensures we start with a clean slate
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Deactivating current virtual environment..."
    deactivate 2>/dev/null || true
    # Give the system a moment to complete deactivation
    sleep 1
fi

# Check for virtual environment (.venv preferred)
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating legacy virtual environment..."
    source venv/bin/activate
    echo "Note: Consider migrating to .venv by running setup.sh"
else
    echo "Error: No virtual environment found. Please run setup.sh first."
    exit 1
fi

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "Redis is not running. Starting Redis..."
    
    # Different ways to start Redis depending on the platform
    if [ "$(uname)" == "Darwin" ]; then
        # macOS
        if command -v brew > /dev/null 2>&1; then
            brew services start redis
        else
            echo "Warning: Could not start Redis automatically. Please start Redis manually."
        fi
    elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
        # Linux
        if command -v systemctl > /dev/null 2>&1; then
            sudo systemctl start redis-server
        elif command -v service > /dev/null 2>&1; then
            sudo service redis-server start
        else
            echo "Warning: Could not start Redis automatically. Please start Redis manually."
        fi
    else
        echo "Warning: Could not start Redis automatically on this platform. Please start Redis manually."
    fi
    
    # Verify Redis started successfully
    sleep 2
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "Error: Redis could not be started. Celery worker will not function correctly."
        echo "Please start Redis manually before continuing."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup aborted. Please start Redis and try again."
            exit 1
        fi
    else
        echo "Redis started successfully."
    fi
fi

echo "Starting JP2Forge Web Application in development mode..."

# Create log directory if it doesn't exist
mkdir -p logs

# Start Django development server in the background
echo "Starting Django development server..."
python manage.py runserver 0.0.0.0:8000 > logs/django.log 2>&1 &
DJANGO_PID=$!
echo "Django server started (PID: $DJANGO_PID). Logs at logs/django.log"

# Start Celery worker in the background
echo "Starting Celery worker..."
celery -A jp2forge_web worker -l INFO > logs/celery.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started (PID: $CELERY_PID). Logs at logs/celery.log"

echo ""
echo "JP2Forge Web Application is running at http://localhost:8000"
echo "Press Ctrl+C to stop all services."
echo ""

# Wait for user to press Ctrl+C
wait $DJANGO_PID $CELERY_PID
