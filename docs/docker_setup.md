# JP2Forge Web Docker Setup Guide

This guide provides instructions for setting up and running JP2Forge Web using Docker. It's primarily intended for administrators or users who need to deploy the application themselves.

## Prerequisites

Before starting, ensure you have:

- Docker Engine 20.10.0 or higher
- Docker Compose v2 (recommended) or Docker Compose standalone
- At least 2GB RAM allocated to Docker
- Git (to clone the repository)

## Quick Setup (Recommended)

For a simple and automated setup, use the provided script:

```bash
# Clone the repository
git clone https://github.com/xy-liao/jp2forge_web.git
cd jp2forge_web

# Run the setup script
chmod +x docker_setup.sh
./docker_setup.sh
```

The script handles everything automatically, including:
- Configuring environment variables with correct password defaults
- Building and starting Docker containers
- Setting up the database with authentication
- Creating a default administrator account

**Note:** The script uses fixed default passwords that match docker-compose.yml. For production deployments, change these passwords after setup.

## Accessing the Application

After the setup completes successfully, you can access JP2Forge Web at:

```
http://localhost:8000
```

Log in with the default credentials (if you used the quick setup):
- Username: `admin`
- Password: `admin123`

**Important:** Change the default password immediately after your first login.

## Basic Docker Commands

Here are some common Docker commands you might need:

### View logs

```bash
# View all logs
docker compose logs

# View specific service logs (web, worker, etc.)
docker compose logs web
```

### Restart the application

```bash
# Restart all services
docker compose restart

# Restart just the web service
docker compose restart web
```

### Stop the application

```bash
# Stop all services
docker compose down
```

### Start the application

```bash
# Start all services
docker compose up -d
```

## Common Issues

### Database authentication errors

If you see PostgreSQL authentication failures in the logs:

1. Check that your `.env` file has the correct password format:
   ```bash
   DATABASE_URL=postgres://jp2forge:jp2forge_password@db:5432/jp2forge
   POSTGRES_PASSWORD=jp2forge_password
   REDIS_PASSWORD=redis_password
   ```

2. The passwords must match the defaults in `docker-compose.yml`.

3. If you have an existing `.env` file, either delete it and re-run `./docker_setup.sh`, or manually update the passwords.

### Application isn't accessible

If you can't access the application at http://localhost:8000:

1. Check if containers are running:
   ```bash
   docker compose ps
   ```

2. Ensure port 8000 isn't being used by another application.

3. Check web container logs for errors:
   ```bash
   docker compose logs web
   ```

### Jobs remain in "pending" state

If your conversion jobs don't start processing:

1. Check worker status:
   ```bash
   docker compose logs worker
   ```

2. Restart the worker:
   ```bash
   docker compose restart worker
   ```

### File uploads fail

If you're having issues uploading files:

1. Check that you're not exceeding the maximum file size (100MB per file by default).
2. Ensure the web container has sufficient disk space.

## Manual Configuration

If you prefer to configure the environment manually:

1. Copy the example environment file:
   ```bash
   cp .env.docker.example .env
   ```

2. Edit `.env` and update:
   - `SECRET_KEY`: Generate a random secret key
   - Database passwords (must match docker-compose.yml defaults)
   - Other settings as needed

3. Ensure passwords match docker-compose.yml:
   - PostgreSQL: `jp2forge_password`
   - Redis: `redis_password`

4. Start the containers:
   ```bash
   docker compose up -d
   ```

## For Advanced Users

Need more advanced configuration? See the [GitHub repository](https://github.com/xy-liao/jp2forge) for:
- Security hardening tips
- Custom environment configurations
- Scaling options for large deployments
- Advanced troubleshooting