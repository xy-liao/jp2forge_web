#!/bin/bash
# JP2Forge Web Docker Setup Script
# This script automates the setup process for JP2Forge web application

# Color codes for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}====== JP2Forge Web Docker Setup ======${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Check if .env file exists, create from example if not
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}Created .env file successfully.${NC}"
    else
        echo -e "${YELLOW}Creating default .env file...${NC}"
        cat > .env << EOF
# JP2Forge Web - Environment Configuration

# Django settings
SECRET_KEY=change_me_in_production
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database settings
DB_NAME=jp2forge
DB_USER=jp2forge
DB_PASSWORD=jp2forge_password
DB_HOST=db
DB_PORT=5432
DATABASE_URL=postgres://jp2forge:jp2forge_password@db:5432/jp2forge

# PostgreSQL credentials (used by docker-compose.yml)
POSTGRES_USER=jp2forge
POSTGRES_PASSWORD=jp2forge_password
POSTGRES_DB=jp2forge

# Celery settings
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=django-db

# File upload limits
MAX_UPLOAD_SIZE=10485760  # 10MB

# JP2Forge settings
JP2FORGE_OUTPUT_DIR=media/jobs
JP2FORGE_REPORT_DIR=media/reports
JP2FORGE_MOCK_MODE=False

# Security settings - disable for local Docker development
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False
SECURE_HSTS_SECONDS=0
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False

# Additional settings for production
DJANGO_ALLOWED_HOSTS=localhost 127.0.0.1 [::1] 0.0.0.0
DJANGO_SETTINGS_MODULE=jp2forge_web.settings_prod
EOF
        echo -e "${GREEN}Created default .env file successfully.${NC}"
    fi
else
    echo -e "${GREEN}.env file already exists.${NC}"
fi

# Stop any existing containers, remove volumes for clean setup
echo -e "${YELLOW}Stopping any existing containers and cleaning up...${NC}"
docker-compose down -v

# Build and start the containers
echo -e "${YELLOW}Building and starting Docker containers...${NC}"
docker-compose up -d --build

# Wait for database to be ready
echo -e "${YELLOW}Waiting for database to be ready...${NC}"
sleep 10

# Apply database migrations
echo -e "${YELLOW}Applying database migrations...${NC}"
docker-compose exec -T web python manage.py migrate

# Check if migration was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database migrations applied successfully.${NC}"
else
    echo -e "${RED}Error applying migrations. Will retry in 5 seconds...${NC}"
    sleep 5
    docker-compose exec -T web python manage.py migrate
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Database migrations applied successfully on second attempt.${NC}"
    else
        echo -e "${RED}Error applying migrations. Please check database connection.${NC}"
    fi
fi

# Ask if user wants to create a superuser
echo -e "${YELLOW}Do you want to create a superuser? (y/n)${NC}"
read -r create_user

if [[ "$create_user" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Creating superuser...${NC}"
    docker-compose exec web python manage.py createsuperuser
fi

# Display success message
echo -e "${GREEN}====== Setup Complete! ======${NC}"
echo -e "${GREEN}JP2Forge web application is now running.${NC}"
echo -e "${GREEN}You can access it at: http://localhost:8000${NC}"

# Check the status of the containers
echo -e "${YELLOW}Docker container status:${NC}"
docker-compose ps