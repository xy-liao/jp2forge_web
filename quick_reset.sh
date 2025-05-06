#!/bin/bash
# Quick reset script for JP2Forge Web
# This script performs a simple reset without any interactive prompts

set -e  # Exit on errors

echo "=========================================================="
echo "JP2FORGE WEB QUICK RESET"
echo "=========================================================="

# Kill running processes
echo "Stopping running Django and Celery processes..."
pkill -f "runserver" || echo "No Django processes to kill"
pkill -f "celery -A jp2forge_web" || echo "No Celery processes to kill"

# Clean up existing files
echo "Cleaning up environment..."
rm -rf __pycache__ */__pycache__ */*/__pycache__
rm -rf .venv venv env
rm -rf staticfiles
rm -rf media
rm -f db.sqlite3
rm -f *.log logs/*.log

# Create fresh virtual environment
echo "Creating fresh virtual environment..."
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Apply migrations
echo "Setting up database..."
python manage.py makemigrations
python manage.py migrate

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create media directories
echo "Creating media directories..."
mkdir -p media/jobs

# Create admin user
echo "Creating default admin user..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
"

echo "=========================================================="
echo "SETUP COMPLETE!"
echo "=========================================================="
echo ""
echo "To start the development server:"
echo "  ./start_dev.sh"
echo ""
echo "To start the Celery worker (in a separate terminal):"
echo "  ./start_celery.sh"
echo ""
echo "Default admin credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo "=========================================================="