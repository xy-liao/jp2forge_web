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
- Configuring environment variables
- Building and starting Docker containers
- Setting up the database
- Creating a default administrator account

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

### Application isn't accessible

If you can't access the application at http://localhost:8000:

1. Check if containers are running:
   ```bash
   docker compose ps
   ```

2. Ensure port 8000 isn't being used by another application.

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

## For Advanced Users

Need more advanced configuration? See the [GitHub repository](https://github.com/xy-liao/jp2forge) for:
- Security hardening tips
- Custom environment configurations
- Scaling options for large deployments
- Advanced troubleshooting