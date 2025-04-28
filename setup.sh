#!/bin/bash

echo "Setting up JP2Forge Web Application..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file from example
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    # Generate a random SECRET_KEY
    SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
    # Replace the placeholder with the generated key
    sed -i.bak "s/SECRET_KEY=changeme/SECRET_KEY=$SECRET_KEY/g" .env
    rm .env.bak
fi

# Apply migrations
echo "Applying database migrations..."
python manage.py makemigrations
python manage.py migrate

# Create media directories
echo "Creating media directories..."
mkdir -p media/jobs

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup complete!"
echo ""
echo "To create a superuser, run:"
echo "python manage.py createsuperuser"
echo ""
echo "To run the development server:"
echo "python manage.py runserver"
echo ""
echo "To run the Celery worker (in a separate terminal):"
echo "celery -A jp2forge_web worker -l INFO"
