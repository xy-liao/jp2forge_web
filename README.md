# JP2Forge Web Application v0.1.0

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge_web) 
[![Version: 0.1.0](https://img.shields.io/badge/Version-0.1.0-blue.svg)](https://github.com/xy-liao/jp2forge_web/releases/tag/v0.1.0)

A web interface for the JP2Forge JPEG2000 conversion library, providing an easy-to-use system for converting and managing image files in the JPEG2000 format.

**Important Note**: This application serves primarily as a promotional demonstration for the [JP2Forge script](https://github.com/xy-liao/jp2forge) and its BnF (Bibliothèque nationale de France) compliance capabilities. JP2Forge Web doesn't leverage all available arguments and features of the underlying JP2Forge script - it's a case study implementation showcasing selected functionality of the more comprehensive JP2Forge tool.

## Features

- Interactive Dashboard with conversion statistics, storage metrics, and job monitoring
- Convert images to JPEG2000 format with various options
- Support for different compression modes: lossless, lossy, supervised, and BnF-compliant
- Support for multiple document types: photograph, heritage document, color, grayscale
- Parallel processing of conversion jobs with Celery
- User authentication and job management
- Detailed conversion reports with quality metrics
- Multi-page TIFF support
- Real-time progress tracking

## Installation

### Prerequisites

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

### Quick Start (Development)

For a quick development setup:

```bash
# Clone the repository
git clone https://github.com/xy-liao/jp2forge_web.git
cd jp2forge_web

# Run the setup script
chmod +x setup.sh
./setup.sh

# Initialize the application
python init.py

# Start the development server and Celery worker
./start_dev.sh
```

### Using Docker (Recommended for Production)

1. Clone the repository:
   ```
   git clone https://github.com/xy-liao/jp2forge_web.git
   cd jp2forge_web
   ```

2. Copy the example environment file and edit it if needed:
   ```
   cp .env.example .env
   ```

3. Configure database credentials:
   
   The docker-compose.yml file uses environment variables for database credentials, following security best practices:
   ```
   # In your .env file or exported in your shell:
   POSTGRES_USER=your_secure_username
   POSTGRES_PASSWORD=your_secure_password
   ```
   
   If these variables are not set, default values (`postgres` for both) will be used.

4. Start the Docker containers:
   ```
   docker-compose up -d
   ```

5. Create a superuser:
   ```
   docker-compose exec web python manage.py createsuperuser
   ```

6. Access the application at http://localhost:8000

### Manual Installation

1. Clone the repository:
   ```
   git clone https://github.com/xy-liao/jp2forge_web.git
   cd jp2forge_web
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Copy the example environment file and edit it if needed:
   ```
   cp .env.example .env
   ```

4. Apply database migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Ensure Redis is running (check with `redis-cli ping`), then start the development server:
   ```
   python manage.py runserver
   ```

7. In a separate terminal, start the Celery worker:
   ```
   source .venv/bin/activate  # Activate the virtual environment again
   celery -A jp2forge_web worker -l INFO
   ```

8. Access the application at http://localhost:8000

### Troubleshooting

- **Celery worker won't start**: Ensure Redis is running with `redis-cli ping`
- **Missing media directory**: Create the directory structure with `mkdir -p media/jobs`
- **Permission issues**: Make sure that all script files are executable with `chmod +x *.sh`

## Application Structure

### Dashboard

The dashboard provides a comprehensive overview of your JP2Forge activity:

- **Job Statistics**: Total jobs, completed jobs, in-progress jobs, and failed jobs
- **Storage Metrics**: Original size, converted size, space saved, and average compression ratio
- **Recent Jobs**: Quick view of your most recent conversion jobs with real-time status indicators
- **Quick Actions**: Direct links to common tasks

![JP2Forge Dashboard](static/images/docs/jp2forge_web_welcome.png)

### JPEG2000 Conversion

The application provides a user-friendly interface for JP2Forge's powerful conversion capabilities:

![JP2Forge Conversion Interface](static/images/docs/jp2forge_web_config.png)

- **Multiple Compression Modes**:
  - `lossless`: No data loss, larger file size
  - `lossy`: Higher compression with data loss
  - `supervised`: Quality-controlled compression with analysis
  - `bnf_compliant`: BnF standards with fixed compression ratios

- **Document Type Options**:
  - `photograph`: Standard photographic images (default)
  - `heritage_document`: Historical documents with high-quality settings
  - `color`: General color images
  - `grayscale`: Grayscale images

- **Quality Analysis**:
  - PSNR (Peak Signal-to-Noise Ratio) calculation
  - SSIM (Structural Similarity Index) analysis
  - Compression ratio reporting

### Job Management

- Track conversion progress in real-time
- View detailed conversion reports
- Download converted JPEG2000 files
- Manage and delete conversion jobs
- Retry failed conversions

## Maintenance & Cleanup

The JP2Forge Web application includes a cleanup tool to help maintain your installation and reset it to a clean state after testing or when encountering issues.

### Using the Cleanup Script

The `cleanup.py` script provides comprehensive cleanup capabilities:

```bash
# Clean everything (standard safe options)
python cleanup.py --all

# Show what would be cleaned without actually deleting anything
python cleanup.py --dry-run

# Clean specific components
python cleanup.py --jobs            # Job records and media files
python cleanup.py --logs            # Clear log files contents (preserves files)
python cleanup.py --remove-all-logs # Remove log files completely
python cleanup.py --temp            # Temporary cache files
python cleanup.py --celery          # Reset Celery tasks
python cleanup.py --sqlite          # Clean SQLite journal files and optimize DB
python cleanup.py --sqlite-backups  # Remove SQLite database backup files
python cleanup.py --static          # Remove collected static files (requires collectstatic afterward)
python cleanup.py --sessions        # Clean Django session files

# User account options
python cleanup.py --jobs --keep-users     # Keep user accounts (default behavior)
python cleanup.py --jobs --no-keep-users  # Remove user accounts when cleaning jobs

# Full project reinitialization (recreates database, removes all data)
python cleanup.py --reinit

# Complete thorough cleanup (removes all non-essential files)
python cleanup.py --complete

# Skip backup creation before clearing files
python cleanup.py --logs --no-backup

# Combine multiple cleanup operations
python cleanup.py --jobs --logs --sqlite
```

### Cleanup Features

The script provides the following cleanup features:

- **Database cleanup**: Removes conversion job records, with options to preserve or remove user accounts
- **Media files cleanup**: Deletes all job-related files in the media/jobs directory
- **Log files management**: 
  - Clear log contents while preserving files (creates backups before clearing)
  - Completely remove log files with `--remove-all-logs`
  - Manage backup rotations (keeping only the latest backups)
- **Temporary files cleanup**: Removes Python cache files and other temporary data
- **Celery task management**: Resets the Celery task queue and can restart workers
- **SQLite optimization**: Cleans journal files, optimizes the database with VACUUM, and manages backups
- **Static files management**: Removes collected static files when needed
- **Session management**: Cleans Django session files
- **Complete reinitialization**: Recreates the database from scratch with the `--reinit` option

### When to Use Cleanup

- **After testing**: Clear out test data while preserving your user account
- **Before demos**: Start with a clean slate when demonstrating features
- **Storage management**: Free up disk space by removing old job files
- **Troubleshooting**: Reset the application to a clean state when diagnosing issues
- **Application reset**: Use `--reinit` for a complete fresh start, recreating the database

### Regular Maintenance

For regular maintenance, consider running the cleanup script periodically, especially if you're performing lots of conversions or tests:

```bash
# Monthly maintenance (cleans jobs and logs while keeping user accounts)
python cleanup.py --jobs --logs
```

**Note**: By default, the script creates backups of log files before clearing them, ensuring you don't lose important debugging information. Use the `--no-backup` option to skip backup creation.

## Configuration

### Environment Variables

The application uses environment variables for configuration. Key variables include:

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Generated randomly |
| `DEBUG` | Debug mode | `True` in development, `False` in production |
| `ALLOWED_HOSTS` | Allowed hosts (comma-separated) | `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection string | SQLite in development, PostgreSQL in production |
| `CELERY_BROKER_URL` | Celery broker URL | `redis://localhost:6379/0` |
| `MAX_UPLOAD_SIZE` | Maximum upload file size in bytes | 100MB (104857600) |

See `.env.example` for a complete list of available options.

### Production Settings

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

## Dependencies

- **Django 4.2**: Web framework
- **JP2Forge 0.9.1**: JPEG2000 conversion library
- **Celery 5.3.1**: Distributed task queue
- **Redis**: Message broker for Celery
- **ExifTool**: For metadata handling
- **PostgreSQL** (optional, for production): Database

### JP2Forge Library Installation

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

### System Dependencies

- **ExifTool** (required for metadata functionality):
  - On macOS: `brew install exiftool`
  - On Ubuntu/Debian: `sudo apt install libimage-exiftool-perl`
  - On Windows: Download from [ExifTool's website](https://exiftool.org)

## Development

### Project Structure

```
jp2forge_web/
├── accounts/                   # User authentication app
├── converter/                  # Main conversion app
│   ├── context_processors/     # Custom context processors
│   ├── migrations/             # Database migrations
│   ├── templates/              # HTML templates
│   ├── admin.py                # Admin interface
│   ├── forms.py                # Form definitions
│   ├── models.py               # Data models
│   ├── tasks.py                # Celery tasks
│   ├── urls.py                 # URL routing
│   └── views.py                # View functions
├── jp2forge_web/              # Project settings
│   ├── settings.py             # Development settings
│   ├── settings_prod.py        # Production settings
│   ├── urls.py                 # Main URL routing
│   └── wsgi.py                 # WSGI configuration
├── logs/                       # Application logs
├── media/                      # User-uploaded files
│   └── jobs/                   # Conversion jobs
├── static/                     # Static assets
│   ├── css/                    # CSS files
│   ├── js/                     # JavaScript files
│   └── images/                 # Image assets
├── templates/                  # Global templates
├── .env.example                # Example environment variables
├── docker-compose.yml          # Docker configuration
├── Dockerfile                  # Docker build configuration
├── init.py                     # Initialization script
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── setup.sh                    # Setup script
└── start_dev.sh                # Development startup script
```

### Running Tests

```bash
python manage.py test
```

### Linting

```bash
flake8 .
```

## Deployment

### Using Docker

The provided Docker configuration includes:
- Web application container
- Celery worker container
- PostgreSQL database container
- Redis container

To deploy with Docker:

```bash
# Build and start containers
docker-compose up -d

# Create a superuser
docker-compose exec web python manage.py createsuperuser

# For production, use the production settings
docker-compose exec web python manage.py collectstatic --no-input --settings=jp2forge_web.settings_prod
```

### Manual Deployment

For manual deployment to a production server:

1. Set up a PostgreSQL database
2. Configure environment variables
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run migrations:
   ```
   python manage.py migrate --settings=jp2forge_web.settings_prod
   ```
5. Collect static files:
   ```
   python manage.py collectstatic --settings=jp2forge_web.settings_prod
   ```
6. Set up a web server (Nginx, Apache) with WSGI (Gunicorn, uWSGI)
7. Configure Celery as a system service
8. Configure Redis

## Usage Guide

### Creating a Conversion Job

1. Log in to the application
2. Click on "New Conversion" from the dashboard
3. Upload an image file (JPEG, TIFF, PNG, or BMP)
4. Select your desired compression mode:
   - **Lossless**: For perfect reproduction with moderate compression
   - **Lossy**: For higher compression with some data loss
   - **Supervised**: Smart compression that analyzes quality
   - **BnF Compliant**: Follows Bibliothèque nationale de France standards
5. Choose the document type that best matches your image
6. Adjust the quality setting if using lossy compression
7. Click "Upload and Convert" to start the conversion

### Monitoring Jobs

1. The dashboard shows recent jobs with real-time status updates
2. The job list page provides a filterable view of all your jobs
3. Click on a job to view detailed information and progress

### Viewing Results

1. When a job completes, you'll see the conversion details:
   - Before/after file sizes
   - Compression ratio achieved
   - Quality metrics (PSNR, SSIM)
2. Download options become available for completed jobs
3. For multi-page files, all pages are available individually

### Managing Jobs

1. Delete unwanted jobs from the job detail page
2. Retry failed jobs if needed
3. Filter jobs by status, compression mode, or document type

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [JP2Forge](https://github.com/xy-liao/jp2forge) - The core JPEG2000 conversion library
- [Django](https://www.djangoproject.com/) - The web framework used
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
