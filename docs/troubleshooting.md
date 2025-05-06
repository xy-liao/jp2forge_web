# JP2Forge Web Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the JP2Forge Web application.

## Table of Contents
1. [Managing Multiple Service Instances](#managing-multiple-service-instances)
2. [Redis and Task Processing Issues](#redis-and-task-processing-issues)
3. [Docker Setup Issues](#docker-setup-issues)
4. [Conversion Errors](#conversion-errors)
5. [Debugging Conversion Issues](#debugging-conversion-issues)

## Managing Multiple Service Instances

One of the most common issues during development and testing is having multiple instances of services (Django, Celery, Redis) running simultaneously, which can cause port conflicts, resource contention, and unexpected behavior.

### Using Service Management Tools

JP2Forge Web now includes dedicated tools to manage services and prevent these issues:

```bash
# Check what services are currently running
./reset_environment.sh status

# Stop all services and clean up the environment
./reset_environment.sh clean

# Start fresh instances of all required services
./reset_environment.sh start

# Restart all services (combines clean and start)
./reset_environment.sh restart
```

### Common Service Management Issues

| Issue | Symptoms | Solution |
|-------|----------|----------|
| Multiple Celery workers | Jobs processed multiple times or inconsistent results | `./reset_environment.sh clean` to stop all workers |
| Django port conflicts | "Address already in use" errors when starting the server | `./reset_environment.sh status` to find the conflicting process, then `clean` |
| Multiple Redis instances | Celery tasks not processed, inconsistent caching | `./reset_environment.sh clean` to stop all Redis instances |
| Resource contention | System running slow, high CPU/memory usage | `./reset_environment.sh status` to identify the processes, then `clean` |

### When Starting a New Testing Session

Before starting a new testing session, always clean up the environment to ensure you're starting fresh:

```bash
# Stop services and clean environment
./reset_environment.sh clean

# Start fresh services
./reset_environment.sh start
```

### Advanced Service Management

For more control over specific services:

```bash
# Stop only specific services
python manage_services.py stop --services=celery,redis

# Force kill services that won't stop gracefully
python manage_services.py stop --force

# Start only the Django server
python manage_services.py start --services=django
```

## Redis and Task Processing Issues

### Preventing Stuck Jobs

The JP2Forge Web application uses Redis as a message broker for Celery tasks. Sometimes jobs may get stuck in the "pending" state due to Redis configuration issues. We've implemented several solutions to help prevent this:

1. **Automatic Redis Configuration**: The startup script now automatically configures Redis to prevent the most common cause of stuck jobs - the `stop-writes-on-bgsave-error` setting.

2. **Redis Health Monitoring**: A dedicated monitoring script checks and fixes Redis issues:

   ```bash
   # Run the Redis monitor to check for issues and fix them
   python monitor_redis.py
   ```

3. **Recovery Management Command**: A Django management command to recover stuck jobs:

   ```bash
   # Find and recover jobs stuck in pending state for more than 15 minutes
   python manage.py recover_stuck_jobs

   # Dry run to see what would be done without making changes
   python manage.py recover_stuck_jobs --dry-run

   # Fix Redis configuration to prevent future issues
   python manage.py recover_stuck_jobs --fix-redis-config

   # Reset Redis task queues if they appear corrupted
   python manage.py recover_stuck_jobs --reset-redis
   ```

### Common Redis Issues

#### Jobs Stuck in "Pending" State

If your jobs are stuck in the "pending" state, it's often due to one of these Redis issues:

1. **Redis Persistence Error**: Redis is configured to stop accepting writes when it can't save snapshots to disk. This can be fixed with:

   ```bash
   # Via Redis CLI
   redis-cli config set stop-writes-on-bgsave-error no

   # Or use our management command
   python manage.py recover_stuck_jobs --fix-redis-config
   ```

2. **Queue Corruption**: Sometimes the Celery task queue in Redis can become corrupted. Reset it with:

   ```bash
   # Reset the queue and recover jobs
   python manage.py recover_stuck_jobs --reset-redis
   ```

3. **Redis Memory Issues**: If Redis runs out of memory, it can't store new tasks. Check memory usage:

   ```bash
   # Check Redis memory usage
   redis-cli info memory | grep used_memory_human
   ```

#### Redis Connection Issues

If the application can't connect to Redis:

1. **Check if Redis is running**:
   ```bash
   redis-cli ping
   ```
   
   If this doesn't return "PONG", Redis isn't running.

2. **Start Redis**:
   ```bash
   # On macOS
   brew services start redis
   
   # On Ubuntu/Debian
   sudo service redis-server start
   ```

3. **Check Redis log files** for errors:
   ```bash
   # Typical locations (may vary by system)
   cat /var/log/redis/redis-server.log  # Linux
   ```

### Monitoring Redis Health

To ensure Redis operates correctly and prevent issues:

1. **Run the Redis Monitor Periodically**:
   ```bash
   python monitor_redis.py
   ```

2. **Set up a Cron Job** for automatic monitoring:
   ```bash
   # Edit crontab
   crontab -e
   
   # Add this line to run every 15 minutes
   */15 * * * * cd /path/to/jp2forge_web && /path/to/python monitor_redis.py >> logs/redis_monitor_cron.log 2>&1
   ```

3. **Check Web App Logs** for Redis-related errors:
   ```bash
   # Look for Redis errors in the django log
   grep "Redis" logs/django.log
   ```

### If All Else Fails: Full Reset

If you're still experiencing issues, a complete reset of the Redis system can help:

```bash
# Stop Redis
brew services stop redis  # macOS
sudo service redis-server stop  # Ubuntu/Debian

# Delete Redis data file (⚠️ Warning: This removes all Redis data)
rm /usr/local/var/db/redis/dump.rdb  # macOS (location may vary)
rm /var/lib/redis/dump.rdb  # Ubuntu/Debian (location may vary)

# Start Redis fresh
brew services start redis  # macOS
sudo service redis-server start  # Ubuntu/Debian

# Recover any stuck jobs
python manage.py recover_stuck_jobs
```

## Docker Setup Issues

The v0.1.3 release includes significant improvements to Docker setup reliability. However, if you still encounter issues:

1. **General Docker setup troubleshooting**:
   ```bash
   # Get a comprehensive setup with improved error handling
   ./docker_setup.sh
   ```

2. **Container logs for specific services**:
   ```bash
   docker-compose logs web
   docker-compose logs worker
   docker-compose logs db
   docker-compose logs redis
   ```

3. **Git-based dependency issues** (fixed in v0.1.3):
   - If you see errors about 'git not found' or errors fetching GitHub repositories, ensure your Dockerfile has Git installed:
   ```
   RUN apt-get update && apt-get install -y git
   ```

4. **Database connection errors**:
   ```bash
   # Check if the PostgreSQL service is running
   docker-compose ps db
   
   # Check if the database is ready to accept connections
   docker-compose exec db pg_isready
   
   # Rebuild from scratch in case of persistent issues
   docker-compose down -v  # Remove volumes to start fresh
   docker-compose up -d    # Restart containers
   docker-compose exec web python manage.py migrate  # Apply migrations
   ```

5. **Redis connection issues**:
   ```bash
   # Verify Redis is responding
   docker-compose exec redis redis-cli ping
   # Should return "PONG"
   
   # Check connectivity from the web container
   docker-compose exec web nc -zv redis 6379
   ```

6. **Container restart loops** (improved handling in v0.1.3):
   - Check container logs to determine why a service keeps restarting
   - Use the enhanced docker-entrypoint.sh script from v0.1.3 that includes better error handling
   - Look for connection failures to dependent services (DB or Redis)

7. **Environment variable issues**:
   - Ensure your .env file is properly located in the project root
   - Verify that environment variables are being passed correctly to containers
   - The improved docker_setup.sh script in v0.1.3 creates a default .env file if needed

8. **Volume mounting issues**:
   - Check if Docker has permissions to mount volumes on your host system
   - Inspect volume status: `docker volume ls` and `docker volume inspect [volume_name]`
   - The v0.1.3 Docker setup uses properly defined named volumes for better persistence

9. **If you're switching from a local development environment to Docker**:
   - Ensure no local processes are using the same ports (8000, 6379, etc.)
   - Stop any local Celery workers that might be running
   - Run `pkill -f "celery -A jp2forge_web"` to stop any running Celery processes

## Conversion Errors

Below are common errors you may encounter during the conversion process and how to resolve them:

### File Upload Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "File too large" | File exceeds the `MAX_UPLOAD_SIZE` setting | Resize the image or increase the `MAX_UPLOAD_SIZE` in your `.env` file |
| "Unsupported file format" | File extension not recognized | Ensure your file has one of these extensions: .jpg, .jpeg, .tif, .tiff, .png, .bmp |
| "Invalid file content" | File is corrupted or not the format its extension suggests | Check the file integrity with another application or convert to a supported format |

### Conversion Process Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "Memory error during conversion" | Server lacks sufficient memory for large file processing | Use a smaller file or increase the server memory allocation |
| "JP2Forge command failed" | Issue with the underlying JP2Forge library | Check logs/converter.log for detailed error messages |
| "Metadata extraction failed" | ExifTool not properly installed or accessible | Verify ExifTool is installed and in your PATH |
| "Timeout during conversion" | Conversion taking longer than allowed time | Adjust the Celery task timeout setting in `settings.py` |

### Task Queue Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "Task stuck in pending state" | Redis connection issues | See [Redis Troubleshooting](#redis-and-task-processing-issues) section |
| "Task failed with unknown error" | Unhandled exception in the worker process | Check logs/celery.log for the full traceback |

## Debugging Conversion Issues

For detailed debugging of conversion issues:

1. **Check Application Logs**:
   ```bash
   tail -n 100 logs/converter.log  # For conversion-specific issues
   tail -n 100 logs/celery.log     # For task queue issues
   tail -n 100 logs/django.log     # For web application issues
   tail -n 100 logs/error.log      # For general error messages
   ```

2. **Run a Test Conversion Manually**:
   ```bash
   # From project directory
   python test_jp2forge.py --input path/to/image.tif --mode lossless
   ```

3. **Verify JP2Forge Library Installation**:
   ```bash
   python check_jp2forge.py
   ```

4. **Enable Debug Mode**:
   In your `.env` file, set:
   ```
   DEBUG=True
   CONVERSION_DEBUG=True
   ```
   This will provide more detailed logs during the conversion process.