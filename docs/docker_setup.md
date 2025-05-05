# JP2Forge Web Docker Setup Guide

This guide provides step-by-step instructions for setting up and running the JP2Forge web application using Docker.

## Prerequisites

- Docker and Docker Compose installed on your system
- Git (to clone the repository)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/jp2forge_web.git
cd jp2forge_web
```

### 2. Configure Environment Variables

Copy the example environment file and customize it if needed:

```bash
cp .env.example .env
```

The default settings in the `.env` file should work for most local development scenarios.

### 3. Build and Start Docker Containers

Run the following command to build and start all necessary containers:

```bash
docker-compose up -d
```

This will start the following services:
- PostgreSQL database
- Redis for Celery task queue
- Django web application
- Celery worker

### 4. Initialize the Database

The first time you run the application, you need to apply migrations and create a superuser:

```bash
# Apply database migrations
docker-compose exec web python manage.py migrate

# Create a superuser (admin account)
docker-compose exec web python manage.py createsuperuser
```

Follow the prompts to create your admin user.

### 5. Access the Application

Once everything is set up, you can access the JP2Forge web application at:

```
http://localhost:8000
```

Use the superuser credentials you created to log in.

## Common Issues and Solutions

### Database Connection Problems

If you encounter database connection errors:

1. Ensure all containers are running:
   ```bash
   docker-compose ps
   ```

2. If you see issues, try restarting with a fresh setup:
   ```bash
   docker-compose down -v
   docker-compose up -d
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

### Port Conflicts

If port 8000 or 6380 (Redis) is already in use on your system:

1. Edit the `docker-compose.yml` file to change the port mapping
2. Restart the containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

## Stopping the Application

To stop the Docker containers:

```bash
docker-compose down
```

Add `-v` to also remove volumes (database data will be lost):

```bash
docker-compose down -v
```

## Development Workflow

For development, you may want to run the application with logs visible:

```bash
docker-compose up
```

Press `Ctrl+C` to stop the application when running in this mode.