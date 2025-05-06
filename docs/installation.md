# JP2Forge Web Installation Guide

This guide provides detailed instructions for installing and configuring the JP2Forge Web application.

## Prerequisites

Before installing JP2Forge Web, ensure you have the following prerequisites installed:

- Python 3.8 or higher
- Redis (required for Celery task queue)
  - On macOS: `brew install redis && brew services start redis`
  - On Ubuntu/Debian: `sudo apt install redis-server && sudo service redis-server start`
  - On Windows: Download from [Redis for Windows](https://github.com/tporadowski/redis/releases)
- ExifTool (for metadata functionality)
  - On macOS: `brew install exiftool`
  - On Ubuntu/Debian: `sudo apt install libimage-exiftool-perl`
  - On Windows: Download from [ExifTool's website](https://exiftool.org)

To verify Redis is running:
```bash
redis-cli ping
```
You should get a response of `PONG`. If not, Redis is not running and needs to be started.

## Installation Options

JP2Forge Web can be installed using one of the following methods:

1. [Docker Installation](#docker-installation) (Recommended for Production)
2. [Manual Installation](#manual-installation) (For Development/Testing)

## Docker Installation

For Docker-based installation, please see the separate [Docker Setup Guide](docker_setup.md).

## Manual Installation

### 1. Clone the Repository

```bash
git clone https://github.com/xy-liao/jp2forge_web.git
cd jp2forge_web
```

### 2. Create a Virtual Environment and Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy the example environment file and edit it if needed:

```bash
cp .env.example .env
```

Available configuration options are explained in the [Configuration](#configuration) section below.

### 4. Apply Database Migrations

```bash
python manage.py migrate
```

### 5. Create a Superuser (Admin Account)

```bash
python manage.py createsuperuser
```
Follow the prompts to create your admin user.

### 6. Start the Application Services

JP2Forge Web provides a service management script that makes it easy to start all required services in the correct order:

```bash
# Make the script executable (first time only)
chmod +x reset_environment.sh

# Start all services (Django, Celery, Redis)
./reset_environment.sh start
```

Alternatively, you can start services manually:

**Start the Django Development Server**:
```bash
python manage.py runserver
```

**Start the Celery Worker** (in a separate terminal):
```bash
source .venv/bin/activate  # Activate the virtual environment again
celery -A jp2forge_web worker -l INFO
```

### 7. Access the Application

The application should now be available at http://localhost:8000

## Managing Application Services

JP2Forge Web includes tools to manage all related services (Django server, Celery workers, Redis, PostgreSQL) and prevent issues with multiple instances running during development and testing.

### Using the Service Management Scripts

#### For Daily Development and Testing

The `reset_environment.sh` script provides a simple interface for common service management tasks:

```bash
# Check status of all services
./reset_environment.sh status

# Stop all services and clean up the environment
./reset_environment.sh clean

# Start all services in the correct order
./reset_environment.sh start

# Restart all services (stop, clean, and restart)
./reset_environment.sh restart
```

#### Advanced Service Management

For more control, you can use the `manage_services.py` script directly:

```bash
# Stop only specific services (e.g., just Celery)
python manage_services.py stop --services=celery

# Force kill services that won't stop gracefully
python manage_services.py stop --force

# Start only Django server
python manage_services.py start --services=django
```

These tools ensure a clean environment for each test run and prevent port conflicts or resource contention from multiple service instances.

## Running the Celery Worker

The JP2Forge Web application requires a running Celery worker to process conversion jobs in the background. Here are the consistent methods to start the Celery worker:

### Option 1: Using Service Management Script (Recommended)

```bash
# Start all services including Celery
./reset_environment.sh start

# Or start just the Celery worker
python manage_services.py start --services=celery
```

### Option 2: Using the start_celery.sh Script

```bash
# Make sure the script is executable
chmod +x start_celery.sh

# Start the Celery worker
./start_celery.sh
```

### Option 3: Running Celery Directly

```bash
# Activate your virtual environment first
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the Celery worker
celery -A jp2forge_web worker -l INFO
```

### Restarting the Celery Worker After Code Changes

When you make changes to the code that affects task processing, you need to restart the Celery worker:

```bash
# Recommended approach
./reset_environment.sh restart --services=celery

# Alternative approach
./restart_celery.sh
```

### Verifying the Celery Worker is Running

```bash
# Check service status
./reset_environment.sh status

# Alternative: check processes directly
ps aux | grep celery
```

## JP2Forge Library Installation

The application depends on the JP2Forge JPEG2000 conversion library. There are two ways to use it:

1. **Install the JP2Forge library** (recommended for production):
   - Visit the [JP2Forge repository](https://github.com/xy-liao/jp2forge)
   - Follow the installation instructions
   - Ensure the library is in your Python path

2. **Use Mock Mode** (for testing/development):
   - The application can run without the actual JP2Forge library
   - Set `JP2FORGE_MOCK_MODE=True` in your .env file
   - This will simulate JPEG2000 conversions without actually performing them
   - Useful for testing the UI and workflows

**Note**: The mock mode provides a simulated experience but does not perform actual JPEG2000 conversions.

## Configuration

The application uses environment variables for configuration. Key variables include:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated randomly |
| `DEBUG` | Debug mode | `True` in development, `False` in production |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | SQLite in development, PostgreSQL in production |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `MAX_UPLOAD_SIZE` | Maximum upload file size in bytes | 100MB (104857600) |

### Environment Configuration Options

Below are all the available configuration options for the `.env` file:

```
# Django Settings
DEBUG=True                             # Enable debug mode (set to False in production)
SECRET_KEY=your-secret-key-here        # Django secret key (will be auto-generated if not provided)
ALLOWED_HOSTS=localhost,127.0.0.1      # Comma-separated list of allowed hosts

# Database Settings
DATABASE_URL=sqlite:///db.sqlite3      # Database URL (SQLite by default)
# For PostgreSQL, use: postgres://user:password@host:port/database

# Redis & Celery Settings
CELERY_BROKER_URL=redis://localhost:6379/0  # Redis URL for Celery broker
CELERY_RESULT_BACKEND=redis://localhost:6379/0  # Redis URL for Celery results

# File Storage Settings
MAX_UPLOAD_SIZE=104857600              # Maximum file upload size in bytes (100MB default)
MAX_PAGES_PER_FILE=200                 # Maximum number of pages in multi-page TIFF files
MEDIA_ROOT=./media                     # Root directory for media files
JOB_FILES_PATH=jobs                    # Subdirectory for job files under MEDIA_ROOT
DELETE_AFTER_DAYS=30                   # Auto-delete completed jobs after this many days (0 to disable)

# JP2Forge Integration
JP2FORGE_MOCK_MODE=False               # Run in mock mode without actual conversions
JP2FORGE_PATH=                         # Path to JP2Forge executable (optional)
CONVERSION_DEBUG=False                 # Enable detailed conversion debugging

# Email Settings (for production)
EMAIL_HOST=smtp.example.com            # SMTP server hostname
EMAIL_PORT=587                         # SMTP server port
EMAIL_HOST_USER=user@example.com       # SMTP username
EMAIL_HOST_PASSWORD=password           # SMTP password
EMAIL_USE_TLS=True                     # Use TLS for SMTP
DEFAULT_FROM_EMAIL=noreply@example.com # Default sender email address

# Security Settings (for production)
SECURE_SSL_REDIRECT=False              # Redirect all requests to HTTPS
SESSION_COOKIE_SECURE=False            # Secure session cookie (requires HTTPS)
CSRF_COOKIE_SECURE=False               # Secure CSRF cookie (requires HTTPS)
SECURE_BROWSER_XSS_FILTER=True         # Enable browser XSS filtering
SECURE_CONTENT_TYPE_NOSNIFF=True       # Prevent MIME type sniffing
```

## Production Settings

For production, use the production settings file:

```bash
export DJANGO_SETTINGS_MODULE=jp2forge_web.settings_prod
```

The production settings include:
- PostgreSQL database support
- Enhanced security settings
- SMTP email configuration
- Increased file size limits
- Proper logging configuration

## Maintenance & Cleanup

The JP2Forge Web application includes several tools to help maintain your installation and reset it to a clean state after testing or when encountering issues.

### Using the Service Management Scripts

For quick maintenance operations:

```bash
# Stop all services and clean the environment
./reset_environment.sh clean

# Check what services are currently running
./reset_environment.sh status

# Restart all services
./reset_environment.sh restart
```

### Using the Cleanup Script

For more comprehensive cleanup capabilities, use the `cleanup.py` script:

```bash
# Clean everything (standard safe options)
python cleanup.py --all

# Show what would be cleaned without actually deleting anything
python cleanup.py --dry-run

# Clean specific components
python cleanup.py --jobs            # Job records and media files
python cleanup.py --logs            # Clear log files contents (preserves files)
python cleanup.py --temp            # Temporary cache files
```

For more options, run:

```bash
python cleanup.py --help
```

## Troubleshooting

For troubleshooting installation issues, please see the [Troubleshooting Guide](troubleshooting.md).

## Common Setup Issues

### Virtual Environment Activation/Deactivation Problems

The setup scripts use a more reliable method to activate virtual environments in non-interactive shells. If you encounter issues with scripts getting stuck at the "Deactivating current virtual environment..." step:

- Use the `quick_reset.sh` script instead of `setup.sh` for a reliable reset and setup
- Or use the `cleanup.py` script with the `--quick-setup` option:

```bash
python cleanup.py --quick-setup
```

### Running Processes Preventing Clean Setup

Always ensure no previous instances of the application are running before attempting setup:

```bash
# Stop all running services
python cleanup.py
```

### Missing Dependencies

Make sure all required packages are installed. Some key dependencies might not be explicitly listed in `requirements.txt`:

```bash
# After activating your virtual environment
pip install markdown  # Required for documentation
```

### Redis Connection Issues

If you encounter errors related to Redis connectivity:

1. Verify Redis is running:
   ```bash
   redis-cli ping
   ```
   
2. If not running, start Redis:
   - macOS: `brew services start redis`
   - Linux: `sudo service redis-server start`
   - Windows: Start the Redis service
   
3. Check the Redis URL in your `.env` file:
   - For local development: `CELERY_BROKER_URL=redis://localhost:6379/0`
   - For Docker: `CELERY_BROKER_URL=redis://redis:6379/0`

### Multiple Processes and Resources Cleanup

If you've been developing for a while, you might have several Django and Celery processes running in the background. To fully clean up:

```bash
# Comprehensive cleanup
python cleanup.py

# Quick reset and setup
./quick_reset.sh
```

## Startup Sequence for Development

For the most reliable development experience, follow this sequence:

1. Stop any running processes:
   ```bash
   python cleanup.py
   ```

2. Reset the environment:
   ```bash
   ./quick_reset.sh
   ```
   
3. Start the Django server:
   ```bash
   ./start_dev.sh
   ```
   
4. Start the Celery worker (in a separate terminal):
   ```bash
   ./start_celery.sh
   ```

The application should now be available at http://localhost:8000