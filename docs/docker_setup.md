# JP2Forge Web Docker Setup Guide

This guide provides step-by-step instructions for setting up and running the JP2Forge web application using Docker. Version 0.2.0 introduces significant security improvements and dependency updates.

## Prerequisites

Before starting the Docker setup, ensure you have:

- Docker Engine 20.10.0 or higher
- Docker Compose v2 (recommended) or Docker Compose standalone
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

The enhanced script (v0.2.0) now includes:
- Support for Docker Compose v2 plugin
- Automatic security checks and base image updates
- Enhanced password security with strong random generation
- Support for Redis authentication
- Multi-stage Docker builds for improved security
- More robust service health checks
- Detailed security recommendations and best practices
- Automatic vulnerability scanning with pip-audit

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

Important security settings to review in the `.env` file:
- `SECRET_KEY`: Generate a secure key (at least 50 characters)
- `DEBUG`: Set to 0 for production
- `REDIS_PASSWORD`: Set a strong password for Redis
- `CELERY_BROKER_URL`: Update to include Redis password: `redis://:password@redis:6379/0`

### 3. Build and Start Docker Containers

Run the following command to build and start all necessary containers:

```bash
# With Docker Compose v2
docker compose up -d

# With Docker Compose standalone
docker-compose up -d
```

This will start the following services:
- `db`: PostgreSQL 16 database (upgraded from 13)
- `redis`: Redis 7.2 for Celery task queue (upgraded from 6.0)
- `web`: Django web application using Python 3.12 (upgraded from 3.11)
- `worker`: Celery worker for background tasks

### 4. Initialize the Database

The first time you run the application, you need to apply migrations:

```bash
# With Docker Compose v2
docker compose exec web python manage.py migrate

# With Docker Compose standalone
docker-compose exec web python manage.py migrate
```

### 5. Create an Admin User

Create a superuser (admin account) to access the application:

```bash
# Interactive method
docker compose exec web python manage.py createsuperuser

# Or use the non-interactive method to create the default admin user
docker compose exec web python -c "
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
docker compose logs
```

To follow logs from a specific container:
```bash
docker compose logs -f web
docker compose logs -f worker
docker compose logs -f redis
docker compose logs -f db
```

### Restarting Containers

To restart all containers:
```bash
docker compose restart
```

To restart a specific container:
```bash
docker compose restart web
docker compose restart worker
```

### Stopping and Removing Containers

To stop all containers:
```bash
docker compose down
```

To stop and remove volumes (will delete database data):
```bash
docker compose down -v
```

## Security Audit and Checking for Vulnerabilities

JP2Forge Web 0.2.0 includes integrated vulnerability scanning:

```bash
# Run vulnerability check on installed Python packages
docker compose exec web pip-audit

# Check for outdated base images
docker pull python:3.12-slim
docker pull postgres:16-alpine
docker pull redis:7.2-alpine

# View dependency versions
docker compose exec web pip list
```

## Troubleshooting Common Issues

### Database Connection Problems

If you encounter database connection errors:

1. Check if the database container is running:
   ```bash
   docker compose ps db
   ```

2. Wait for the database to initialize:
   ```bash
   # Check database readiness
   docker compose exec db pg_isready -U jp2forge
   ```

3. Verify database logs for any issues:
   ```bash
   docker compose logs db
   ```

4. If problems persist, try recreating the database:
   ```bash
   docker compose down -v
   docker compose up -d
   docker compose exec web python manage.py migrate
   ```

### Redis Connection Issues for Celery

If Celery tasks aren't running:

1. Check if Redis is running and responsive:
   ```bash
   # Replace 'password' with your actual Redis password
   docker compose exec redis redis-cli -a password ping
   ```
   This should return `PONG`.

2. Verify Redis connection in Celery:
   ```bash
   docker compose logs worker
   ```
   Look for connection errors.

3. Ensure the `CELERY_BROKER_URL` environment variable includes the password:
   ```
   CELERY_BROKER_URL=redis://:password@redis:6379/0
   ```
   Note that `redis` is the service name in docker-compose, not `localhost`.

### Health Check Failures

If containers are restarting due to failed health checks:

1. Check the container logs:
   ```bash
   docker compose logs web
   ```

2. Manually test the health endpoint:
   ```bash
   curl http://localhost:8000/health/
   ```
   Should return "OK"

3. Verify the Docker health check configuration in docker-compose.yml

## Production Deployment Considerations

For production deployments, consider the following security enhancements:

1. Update `.env` file:
   - Set `DEBUG=0`
   - Use a very strong `SECRET_KEY` (60+ characters)
   - Configure `ALLOWED_HOSTS` appropriately
   - Set all security settings to `True` if using HTTPS
   - Use strong passwords for database and Redis

2. Use a reverse proxy:
   - Configure Nginx or similar as a front-end
   - Enable HTTPS with proper certificates
   - Set up appropriate caching
   - Implement rate limiting

3. Enhanced security:
   - Don't expose PostgreSQL or Redis ports
   - Use Docker secrets or environment variables from your deployment platform
   - Set `no-new-privileges:true` for all containers
   - Regularly update base images with `docker compose build --pull`
   - Run periodic vulnerability scans with `pip-audit`

4. Container resource limits:
   - Set appropriate CPU and memory limits in docker-compose.yml
   - Monitor container resource usage

## Major Security Improvements in v0.2.0

The Docker configuration has been completely redesigned with security in mind:

1. **Updated Base Images**:
   - Python updated to 3.12 (from 3.11)
   - PostgreSQL updated to 16-alpine (from 13)
   - Redis updated to 7.2-alpine (from 6)

2. **Multi-stage Build Process**:
   - Smaller attack surface
   - Reduced image size
   - Separation of build and runtime environments

3. **Dependency Security**:
   - Automatic vulnerability scanning with pip-audit
   - Updated all Python dependencies to latest versions
   - More secure version pinning with >= operators

4. **Enhanced Authentication**:
   - Required Redis password authentication
   - Stronger password generation
   - Improved database security

5. **Container Hardening**:
   - Non-root user execution
   - No-new-privileges restriction
   - Proper health checks and monitoring
   - Improved container dependency chains

## Maintenance and Updates

### Updating the Application

To update the application to a new version:

```bash
# Pull the latest code
git pull

# Rebuild and restart containers
docker compose down
docker compose build --pull --no-cache
docker compose up -d

# Apply any new migrations
docker compose exec web python manage.py migrate
```

### Backing Up Data

To back up the PostgreSQL database:

```bash
docker compose exec db pg_dump -U jp2forge jp2forge > backup.sql
```

To restore from backup:

```bash
cat backup.sql | docker compose exec -T db psql -U jp2forge jp2forge
```