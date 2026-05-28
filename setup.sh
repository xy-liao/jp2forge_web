#!/bin/bash
#
# JP2Forge Web Application Setup Script
# Version 0.2.0
#
# Consolidates: docker_setup.sh, setup_noninteractive.sh, init.py, and cleanup.py
#
# Usage:
#   ./setup.sh                 - Interactive manual setup
#   ./setup.sh docker          - Docker setup (recommended)
#   ./setup.sh -y | --yes      - Non-interactive manual setup

set -e

# Color definitions
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(pwd)"

show_help() {
    echo "Usage: ./setup.sh [option]"
    echo ""
    echo "Options:"
    echo "  docker            Set up JP2Forge Web in Docker containers (recommended)"
    echo "  -y, --yes         Run manual setup in non-interactive mode"
    echo "  -h, --help        Show this help message"
    echo ""
    echo "If no option is provided, the script runs in interactive manual setup mode."
}

cleanup_env() {
    echo -e "${YELLOW}Performing environment cleanup...${NC}"
    # Stop running processes
    pkill -f "manage.py runserver" || true
    pkill -f "celery -A jp2forge_web" || true
    
    # Remove caches
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove old venvs
    rm -rf .venv venv env 2>/dev/null || true
    
    # Remove compiled static files
    rm -rf staticfiles 2>/dev/null || true
    
    # Remove media directory content
    rm -rf media 2>/dev/null || true
    mkdir -p media/jobs
    
    # Remove database files
    rm -f *.sqlite3 2>/dev/null || true
    
    # Remove log files
    rm -rf logs 2>/dev/null || true
    mkdir -p logs
    rm -f *.log 2>/dev/null || true
    
    echo -e "${GREEN}✓ Cleanup complete${NC}"
}

run_docker_setup() {
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}     JP2FORGE WEB DOCKER SETUP (UNIFIED)      ${NC}"
    echo -e "${BLUE}==============================================${NC}"

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: Docker is not installed.${NC}"
        echo -e "Please install Docker from https://www.docker.com/get-started"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is installed${NC}"

    # Determine Compose Command
    if docker compose version &> /dev/null; then
        COMPOSE_COMMAND="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_COMMAND="docker-compose"
    else
        echo -e "${RED}Error: Neither Docker Compose v2 plugin nor docker-compose is available.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Using: $COMPOSE_COMMAND${NC}"

    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker daemon is not running.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker daemon is running${NC}"

    # Stop and clean existing containers
    echo -e "\n${YELLOW}Cleaning up existing JP2Forge containers...${NC}"
    $COMPOSE_COMMAND down -v &> /dev/null || true
    $COMPOSE_COMMAND down &> /dev/null || true

    # Environment file setup
    # If .env exists and does NOT contain SECURE_DOCKER_ENVIRONMENT=true, it might be a manual config.
    if [ -f ".env" ] && ! grep -q "SECURE_DOCKER_ENVIRONMENT=true" .env; then
        echo -e "${YELLOW}Existing .env file is configured for manual dev. Backing it up to .env.manual...${NC}"
        mv .env .env.manual
    fi

    if [ ! -f ".env" ]; then
        echo -e "Creating new .env file..."
        SECRET_KEY=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9!@#$%^&*()_+{}[]|;:,.<>?=' | fold -w 60 | head -n 1)
        POSTGRES_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
        REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)

        cat > .env << EOF
# JP2Forge Web Docker Environment Configuration
SECRET_KEY=${SECRET_KEY}
DEBUG=0
DJANGO_SETTINGS_MODULE=jp2forge_web.settings
ALLOWED_HOSTS=*

# Database Settings
DATABASE_URL=postgres://jp2forge:${POSTGRES_PASSWORD}@db:5432/jp2forge
DB_ENGINE=django.db.backends.postgresql
DB_NAME=jp2forge
DB_USER=jp2forge
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_HOST=db
DB_PORT=5432

# PostgreSQL Settings
POSTGRES_USER=jp2forge
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
POSTGRES_DB=jp2forge

# Redis Settings
REDIS_PASSWORD=${REDIS_PASSWORD}

# Celery Settings
CELERY_BROKER_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
CELERY_RESULT_BACKEND=django-db

# File Upload & JP2Forge
MAX_UPLOAD_SIZE=10485760
JP2FORGE_OUTPUT_DIR=/app/media/jobs
JP2FORGE_REPORT_DIR=/app/media/reports
JP2FORGE_MOCK_MODE=False

# Security Settings
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
SECURE_DOCKER_ENVIRONMENT=true
CREATE_SUPERUSER=true
EOF
        echo -e "${GREEN}✓ Created new secure .env file${NC}"
    else
        echo -e "${YELLOW}Using existing .env file${NC}"
    fi

    # Perms
    chmod +x *.sh 2>/dev/null || true

    # Clear conflicting local environment variables
    unset POSTGRES_USER POSTGRES_PASSWORD POSTGRES_DB REDIS_PASSWORD
    unset DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT

    # Build and start containers
    echo -e "\n${YELLOW}Building and starting containers...${NC}"
    $COMPOSE_COMMAND build
    $COMPOSE_COMMAND up -d

    # Wait for database
    attempt=1
    max_attempts=20
    while [ $attempt -le $max_attempts ]; do
        echo -ne "${YELLOW}Checking database connection (attempt $attempt/$max_attempts)...${NC}\r"
        if $COMPOSE_COMMAND exec -T db pg_isready &> /dev/null; then
            echo -e "${GREEN}✓ Database is ready                                     ${NC}"
            break
        fi
        attempt=$((attempt+1))
        sleep 3
    done

    # Setup admin user in Django
    echo -e "\n${YELLOW}Setting up default superuser...${NC}"
    $COMPOSE_COMMAND exec -T web python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Default superuser \"admin\" with password \"admin123\" created successfully')
else:
    print('Superuser \"admin\" already exists')
" || echo -e "${YELLOW}⚠ Could not verify admin user${NC}"

    echo -e "\n${GREEN}==============================================${NC}"
    echo -e "${GREEN}       JP2FORGE WEB DOCKER SETUP COMPLETE!     ${NC}"
    echo -e "${GREEN}==============================================${NC}"
    echo -e "Web application is running at: ${BLUE}http://localhost:8000${NC}"
    echo -e "Default credentials: admin / admin123"
}

run_manual_setup() {
    local interactive=$1
    echo -e "${BLUE}==============================================${NC}"
    echo -e "${BLUE}     JP2FORGE WEB MANUAL SETUP (UNIFIED)      ${NC}"
    echo -e "${BLUE}==============================================${NC}"

    # Stop processes and clean directories first
    cleanup_env

    # Check dependencies
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed.${NC}"
        exit 1
    fi
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}Error: pip3 is not installed.${NC}"
        exit 1
    fi

    # Verify Redis (for Celery)
    if ! command -v redis-cli &> /dev/null; then
        echo -e "${YELLOW}Warning: Redis is not installed or not in PATH.${NC}"
        if [ "$interactive" = "true" ]; then
            read -p "Do you want to continue without Redis? (y/n) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    else
        if ! redis-cli ping > /dev/null 2>&1; then
            echo -e "${YELLOW}Warning: Redis is installed but not running.${NC}"
            if [ "$interactive" = "true" ]; then
                read -p "Do you want to continue without starting Redis? (y/n) " -n 1 -r
                echo ""
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
        fi
    fi

    # Verify ExifTool
    if ! command -v exiftool &> /dev/null; then
        echo -e "${YELLOW}Warning: ExifTool is not installed or not in PATH.${NC}"
        if [ "$interactive" = "true" ]; then
            read -p "Do you want to continue without ExifTool? (y/n) " -n 1 -r
            echo ""
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # Create fresh virtualenv
    echo -e "\n${YELLOW}Creating Python virtual environment (.venv)...${NC}"
    python3 -m venv .venv
    
    # Activate virtual environment
    VIRTUAL_ENV_PATH="$(pwd)/.venv"
    export VIRTUAL_ENV="$VIRTUAL_ENV_PATH"
    export PATH="$VIRTUAL_ENV_PATH/bin:$PATH"
    unset PYTHONHOME

    # Update pip and install packages
    echo -e "${YELLOW}Installing Python packages...${NC}"
    pip install --upgrade pip
    
    # Install requirement dependencies
    pip install -r requirements.txt || {
        echo -e "${YELLOW}Warning: Full requirements install failed. Trying core fallback...${NC}"
        pip install django>=4.2.20 celery>=5.3.6 redis>=5.0.1 django-crispy-forms>=2.1 \
                    crispy-bootstrap4>=2023.1 django-celery-results>=2.5.1 Pillow>=10.3.0 \
                    python-dotenv>=1.0.0 gunicorn>=23.0.0 psycopg2-binary>=2.9.9 markdown>=3.8
    }

    # Verify JP2Forge core availability
    JP2FORGE_AVAILABLE=0
    if python -c "import core.types" &> /dev/null; then
        JP2FORGE_AVAILABLE=1
    fi

    # Create environment configurations
    # If .env exists and contains SECURE_DOCKER_ENVIRONMENT=true, it will break manual SQLite setup.
    if [ -f ".env" ] && grep -q "SECURE_DOCKER_ENVIRONMENT=true" .env; then
        echo -e "${YELLOW}Existing .env file is configured for Docker. Backing it up to .env.docker...${NC}"
        mv .env .env.docker
    fi

    if [ ! -f ".env" ]; then
        echo -e "Creating basic .env file..."
        SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(50))")
        cat > .env << EOF
SECRET_KEY=${SECRET_KEY}
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CELERY_BROKER_URL=redis://localhost:6379/0
MAX_UPLOAD_SIZE=10485760
JP2FORGE_MOCK_MODE=$([ $JP2FORGE_AVAILABLE -eq 0 ] && echo "True" || echo "False")
EOF
    fi

    # Apply database migrations
    echo -e "\n${YELLOW}Applying Django migrations...${NC}"
    python manage.py makemigrations converter accounts
    python manage.py migrate

    # Collect staticfiles
    echo -e "\n${YELLOW}Collecting Django static files...${NC}"
    python manage.py collectstatic --noinput

    # Create Media & Logs directories
    mkdir -p media/jobs logs

    # Setup Superuser
    if [ "$interactive" = "true" ]; then
        read -p "Do you want to create a Django superuser account now? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            python manage.py createsuperuser
        fi
    else
        # Auto-create admin superuser non-interactively
        python -c "
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Default superuser \"admin\" with password \"admin123\" created successfully')
else:
    print('Superuser already exists')
"
    fi

    echo -e "\n${GREEN}==============================================${NC}"
    echo -e "${GREEN}       JP2FORGE WEB SETUP COMPLETE!            ${NC}"
    echo -e "${GREEN}==============================================${NC}"
    echo -e "To start development server:   ${BLUE}./dev.sh${NC}"
    echo -e "To stop services:              ${BLUE}./dev.sh stop${NC}"
}

# Main routing logic based on arguments
if [ "$1" = "docker" ]; then
    run_docker_setup
elif [ "$1" = "-y" ] || [ "$1" = "--yes" ] || [ "$1" = "--non-interactive" ]; then
    run_manual_setup false
elif [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_help
elif [ -z "$1" ]; then
    run_manual_setup true
else
    echo -e "${RED}Unknown option: $1${NC}"
    show_help
    exit 1
fi
