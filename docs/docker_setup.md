# JP2Forge Web Docker Setup Guide

This guide provides step-by-step instructions for setting up and running the JP2Forge web application using Docker.

## Prerequisites

Before starting the Docker setup, ensure you have:

- Docker and Docker Compose installed on your system
- Docker daemon running
- At least 2GB RAM allocated to Docker (recommended)
- Git (to clone the repository)

## Quick Setup (Recommended)

For a simple and automated setup, use the provided setup script:

```bash
# Clone the repository
git clone https://github.com/yourusername/jp2forge_web.git
cd jp2forge_web

# Make the setup script executable
chmod +x docker_setup.sh

# Run the setup script
./docker_setup.sh
```

The script will:
- Check for required dependencies
- Create configuration files
- Build and start all Docker containers
- Apply database migrations
- Set up an admin user (or prompt you to create one)

## Manual Setup

If you prefer a manual setup process, follow these steps:

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

Important settings to review in the `.env` file:
- `SECRET_KEY`: Generate a secure key for production
- `DEBUG`: Set to 0 for production
- `CELERY_BROKER_URL`: Should point to the Redis container

### 3. Build and Start Docker Containers

Run the following command to build and start all necessary containers:

```bash
docker-compose up -d
```

This will start the following services:
- `db`: PostgreSQL database
- `redis`: Redis for Celery task queue
- `web`: Django web application
- `worker`: Celery worker for background tasks

### 4. Initialize the Database

The first time you run the application, you need to apply migrations:

```bash
# Apply database migrations
docker-compose exec web python manage.py migrate
```

### 5. Create an Admin User

Create a superuser (admin account) to access the application:

```bash
# Interactive method
docker-compose exec web python manage.py createsuperuser

# Or use the non-interactive method to create the default admin user
docker-compose exec web python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Default superuser created successfully')
else:
    print('Superuser already exists')
"
```

### 6. Access the Application

Once everything is set up, you can access the JP2Forge web application at:

```
http://localhost:8000
```

## Container Management

### Viewing Container Logs

To see logs from all containers:
```bash
docker-compose logs
```

To follow logs from a specific container:
```bash
docker-compose logs -f web
docker-compose logs -f worker
docker-compose logs -f redis
docker-compose logs -f db
```

### Restarting Containers

To restart all containers:
```bash
docker-compose restart
```

To restart a specific container:
```bash
docker-compose restart web
docker-compose restart worker
```

### Stopping and Removing Containers

To stop all containers:
```bash
docker-compose down
```

To stop and remove volumes (will delete database data):
```bash
docker-compose down -v
```

## Troubleshooting Common Issues

### Database Connection Problems

If you encounter database connection errors:

1. Check if the database container is running:
   ```bash
   docker-compose ps db
   ```

2. Wait for the database to initialize:
   ```bash
   # Check database readiness
   docker-compose exec db pg_isready
   ```

3. Verify database logs for any issues:
   ```bash
   docker-compose logs db
   ```

4. If problems persist, try recreating the database:
   ```bash
   docker-compose down -v
   docker-compose up -d
   docker-compose exec web python manage.py migrate
   ```

### Redis Connection Issues for Celery

If Celery tasks aren't running:

1. Check if Redis is running and responsive:
   ```bash
   docker-compose exec redis redis-cli ping
   ```
   This should return `PONG`.

2. Verify Redis connection in Celery:
   ```bash
   docker-compose logs worker
   ```
   Look for connection errors.

3. Ensure the `CELERY_BROKER_URL` environment variable is set correctly:
   ```
   CELERY_BROKER_URL=redis://redis:6379/0
   ```
   Note that `redis` is the service name in docker-compose, not `localhost`.

### Port Conflicts

If you see errors like "port already allocated" or "address already in use":

1. Check for conflicting ports:
   ```bash
   # Check for processes using port 8000
   docker-compose ps
   ```

2. Edit the `docker-compose.yml` file to change the port mapping, for example:
   ```yaml
   ports:
     - "8001:8000"  # Maps host port 8001 to container port 8000
   ```

### Container Fails to Start

If a container fails to start:

1. Check the logs:
   ```bash
   docker-compose logs [service_name]
   ```

2. Verify Docker resources:
   - Ensure Docker has enough CPU and memory allocated
   - For desktop Docker: Settings > Resources > Memory (at least 2GB recommended)

3. Try rebuilding the container:
   ```bash
   docker-compose build --no-cache [service_name]
   docker-compose up -d
   ```

## Production Deployment Considerations

For production deployments, consider the following adjustments:

1. Update `.env` file:
   - Set `DEBUG=0`
   - Change `SECRET_KEY` to a secure random string
   - Configure `ALLOWED_HOSTS` appropriately
   - Set security settings to `True` if using HTTPS

2. Use a reverse proxy:
   - Configure Nginx or similar as a front-end
   - Enable HTTPS with proper certificates
   - Set up appropriate caching

3. Improve security:
   - Don't expose PostgreSQL or Redis ports
   - Use stronger passwords
   - Consider using Docker secrets or environment variables from your deployment platform

## Maintenance and Updates

### Updating the Application

To update the application to a new version:

```bash
# Pull the latest code
git pull

# Rebuild and restart containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Apply any new migrations
docker-compose exec web python manage.py migrate
```

### Backing Up Data

To back up the PostgreSQL database:

```bash
docker-compose exec db pg_dump -U jp2forge jp2forge > backup.sql
```

To restore from backup:

```bash
cat backup.sql | docker-compose exec -T db psql -U jp2forge jp2forge
```