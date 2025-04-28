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

# Check if Python virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
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
