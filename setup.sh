#!/bin/bash

echo "Setting up JP2Forge Web Application..."

# Don't attempt to deactivate - this causes issues when run as a script
# Instead, we'll just create a fresh virtual environment

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is not installed. Please install pip and try again."
    exit 1
fi

# Check if Redis is installed and running
echo "Checking Redis installation..."
if ! command -v redis-cli &> /dev/null; then
    echo "Warning: Redis is not installed or not in PATH."
    echo "Redis is required for Celery. Please install Redis:"
    echo "  - On macOS: brew install redis && brew services start redis"
    echo "  - On Ubuntu/Debian: sudo apt install redis-server && sudo service redis-server start"
    echo "  - On Windows: Download from https://github.com/tporadowski/redis/releases"
    
    read -p "Do you want to continue without Redis? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted. Please install Redis and try again."
        exit 1
    fi
else
    # Check if Redis is running
    if ! redis-cli ping > /dev/null 2>&1; then
        echo "Warning: Redis is installed but not running."
        echo "Please start Redis:"
        echo "  - On macOS: brew services start redis"
        echo "  - On Ubuntu/Debian: sudo service redis-server start"
        echo "  - On Windows: Start the Redis service"
        
        read -p "Do you want to continue without starting Redis? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Setup aborted. Please start Redis and try again."
            exit 1
        fi
    else
        echo "Redis is running correctly."
    fi
fi

# Check if ExifTool is installed
echo "Checking ExifTool installation..."
if ! command -v exiftool &> /dev/null; then
    echo "Warning: ExifTool is not installed or not in PATH."
    echo "ExifTool is required for metadata extraction. Please install ExifTool:"
    echo "  - On macOS: brew install exiftool"
    echo "  - On Ubuntu/Debian: sudo apt install libimage-exiftool-perl"
    echo "  - On Windows: Download from https://exiftool.org"
    
    read -p "Do you want to continue without ExifTool? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted. Please install ExifTool and try again."
        exit 1
    fi
fi

# Clean up any existing virtual environments to avoid conflicts
if [ -d ".venv" ]; then
    echo "Removing existing .venv directory..."
    rm -rf .venv
fi

if [ -d "venv" ]; then
    echo "Removing existing venv directory..."
    rm -rf venv
fi

# Create a fresh virtual environment
echo "Creating fresh virtual environment..."
python3 -m venv .venv

# Activate the virtual environment directly without sourcing
VIRTUAL_ENV_PATH="$(pwd)/.venv"
export VIRTUAL_ENV="$VIRTUAL_ENV_PATH"
export PATH="$VIRTUAL_ENV_PATH/bin:$PATH"
unset PYTHONHOME
echo "Virtual environment activated."

# Ensure pip is updated
echo "Updating pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install markdown package (needed for documentation) 
echo "Installing markdown package for documentation..."
pip install markdown

# Verify critical dependencies are installed
echo "Verifying critical dependencies..."
MISSING_DEPS=0

# Check for Django
if ! python -c "import django" &> /dev/null; then
    echo "Error: Django is not installed correctly."
    MISSING_DEPS=1
fi

# Check for crispy-bootstrap4
if ! python -c "import crispy_bootstrap4" &> /dev/null; then
    echo "Error: crispy-bootstrap4 is not installed correctly."
    echo "Trying to install it again..."
    pip install crispy-bootstrap4
    if ! python -c "import crispy_bootstrap4" &> /dev/null; then
        echo "Failed to install crispy-bootstrap4. This may cause issues with form rendering."
        MISSING_DEPS=1
    fi
fi

# Check for django-celery-results
if ! python -c "import django_celery_results" &> /dev/null; then
    echo "Error: django-celery-results is not installed correctly."
    echo "Trying to install it again..."
    pip install django-celery-results
    if ! python -c "import django_celery_results" &> /dev/null; then
        echo "Failed to install django-celery-results. This may cause issues with task handling."
        MISSING_DEPS=1
    fi
fi

# Check for markdown package
if ! python -c "import markdown" &> /dev/null; then
    echo "Error: markdown is not installed correctly."
    echo "Trying to install it again..."
    pip install markdown
    if ! python -c "import markdown" &> /dev/null; then
        echo "Failed to install markdown. This may cause issues with documentation."
        MISSING_DEPS=1
    fi
fi

# Check for JP2Forge if it's supposed to be available
# Note: JP2Forge might not be pip-installable, so we'll just warn if it's not found
if ! python -c "import core.types" &> /dev/null; then
    echo "Warning: JP2Forge core modules are not found."
    echo "The application will run in mock mode without real JPEG2000 conversion capabilities."
    echo "This is acceptable for testing the UI, but not for production use."
fi

if [ $MISSING_DEPS -eq 1 ]; then
    echo "Warning: Some dependencies could not be installed properly."
    echo "The application may not function correctly."
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup aborted. Please resolve the dependency issues and try again."
        exit 1
    fi
else
    echo "All critical dependencies verified!"
fi

# Create .env file from example
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    if [ ! -f .env.example ]; then
        echo "Error: .env.example file not found. Creating a basic .env file..."
        echo "SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")" > .env
        echo "DEBUG=True" >> .env
        echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env
        echo "CELERY_BROKER_URL=redis://localhost:6379/0" >> .env
        echo "MAX_UPLOAD_SIZE=10485760" >> .env
    else
        cp .env.example .env
        # Generate a random SECRET_KEY
        SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
        # Replace the placeholder with the generated key
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS sed requires an empty string for -i
            sed -i '' "s/SECRET_KEY=changeme/SECRET_KEY=$SECRET_KEY/g" .env
        else
            # Linux sed
            sed -i "s/SECRET_KEY=changeme/SECRET_KEY=$SECRET_KEY/g" .env
        fi
    fi
fi

# Make script files executable
echo "Making script files executable..."
chmod +x *.sh

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

# Offer to create a superuser
read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
fi

echo "Setup complete!"
echo ""
echo "To run the development server:"
echo "./start_dev.sh"
echo ""
echo "Or manually:"
echo "python manage.py runserver"
echo ""
echo "To run the Celery worker (in a separate terminal):"
echo "./start_celery.sh"
echo ""
echo "Or manually:"
echo "celery -A jp2forge_web worker -l INFO"
