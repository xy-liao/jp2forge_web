# JP2Forge Web Application v0.1.1

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge_web) 
[![Version: 0.1.1](https://img.shields.io/badge/Version-0.1.1-blue.svg)](https://github.com/xy-liao/jp2forge_web/releases/tag/v0.1.1)

A web interface for the JP2Forge JPEG2000 conversion library, providing an easy-to-use system for converting and managing image files in the JPEG2000 format.

**Important Note**: This application serves primarily as a promotional demonstration for the [JP2Forge script](https://github.com/xy-liao/jp2forge) and its BnF (Bibliothèque nationale de France) compliance capabilities. JP2Forge Web doesn't leverage all available arguments and features of the underlying JP2Forge script - it's a case study implementation showcasing selected functionality of the more comprehensive JP2Forge tool.

**Additional Documentation**: For more detailed and topic-specific guidance, see the [docs folder](docs/) which contains separate guides for [users](docs/user_guide.md), administrators, API developers, and installation instructions.

## Table of Contents

1. [Features](#features)
2. [Supported File Formats and Limitations](#supported-file-formats-and-limitations)
3. [Multi-Page TIFF Support](#multi-page-tiff-support)
4. [API Access](#api-access)
5. [Installation](#installation)
   - [Prerequisites](#prerequisites)
   - [Quick Start (Development)](#quick-start-development)
   - [Using Docker (Recommended for Production)](#using-docker-recommended-for-production)
   - [Manual Installation](#manual-installation)
   - [Troubleshooting](#troubleshooting)
6. [Troubleshooting Redis and Task Processing Issues](#troubleshooting-redis-and-task-processing-issues)
7. [Error Handling and Troubleshooting](#error-handling-and-troubleshooting)
8. [Application Structure](#application-structure)
   - [Dashboard](#dashboard)
   - [JPEG2000 Conversion](#jpeg2000-conversion)
   - [JPEG2000 Conversion Results](#jpeg2000-conversion-results)
   - [Job Management](#job-management)
9. [Maintenance & Cleanup](#maintenance--cleanup)
10. [Configuration](#configuration)
    - [Environment Variables](#environment-variables)
    - [Environment Configuration Options](#environment-configuration-options)
    - [Production Settings](#production-settings)
11. [Dependencies](#dependencies)
12. [Development](#development)
13. [Deployment](#deployment)
14. [Usage Guide](#usage-guide)
15. [Contributing](#contributing)
16. [License](#license)
17. [Acknowledgments](#acknowledgments)
18. [BnF Compliance Information](#bnf-compliance-information)

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

## Supported File Formats and Limitations

### Input Formats
- **JPEG/JPG**: Standard photographic format
- **TIFF/TIF**: Both single-page and multi-page TIFF files are supported
- **PNG**: Lossless raster graphics format
- **BMP**: Bitmap image format

### Technical Limitations
- **Maximum File Size**: 100MB per file by default (configurable via `MAX_UPLOAD_SIZE` environment variable)
- **Multi-page Support**: Up to 200 pages per multi-page TIFF (configurable)
- **Resolution Limits**: Up to 20,000 x 20,000 pixels (higher resolutions may work but are not officially supported)
- **Browser Compatibility**: Chrome 88+, Firefox 85+, Safari 14+, Edge 88+

### Performance Considerations
- Typical conversion times:
  - Small images (< 5MB): ~5-10 seconds
  - Medium images (5-20MB): ~20-40 seconds
  - Large images (20-100MB): ~1-5 minutes
  - Multi-page TIFFs: Approximately (per-page time × number of pages)
- Processing times depend on server resources and selected compression options

### Output Format
- **JPEG2000/JP2**: Converted files follow the JP2 format specification
- Compliant with ISO/IEC 15444-1 (when using BnF compliance mode)

## Multi-Page TIFF Support

JP2Forge Web provides comprehensive support for processing multi-page TIFF files, which is particularly useful for document scanning and archival applications.

### Multi-Page Processing Features

- **Page Limit**: By default, the application supports up to 200 pages per TIFF file (configurable via `MAX_PAGES_PER_FILE` in `.env`)
- **Individual Page Access**: Each page is converted separately and can be downloaded individually
- **Thumbnail Generation**: Automatic thumbnail generation for each page
- **Progress Tracking**: Page-by-page progress reporting for large files
- **Parallel Processing**: Multi-page files benefit from parallel processing for faster conversion

### Sample Processing Times

Processing times for multi-page TIFFs depend on server resources, but typical estimates are:

| Pages | Average Size | Estimated Processing Time |
|-------|-------------:|----------------------------|
| 10    | 50 MB        | 2-5 minutes                |
| 50    | 250 MB       | 10-20 minutes              |
| 100   | 500 MB       | 20-40 minutes              |
| 200   | 1 GB         | 40-80 minutes              |

### Memory Requirements

Multi-page TIFF processing requires more memory than single-page conversions. Approximate memory requirements:

- **Minimum RAM**: 4GB for files up to 50 pages
- **Recommended RAM**: 8GB for files up to 200 pages
- **Production Server**: 16GB+ for concurrent multi-page conversion jobs

### Error Handling for Large Files

When processing large multi-page files:

1. **Page Count Limit**: Files exceeding the configured page limit will be rejected with a specific error message
2. **Recovery Mechanism**: If a single page fails during conversion, the system will continue processing other pages
3. **Timeout Handling**: Extended conversion times are handled with configurable timeouts (adjust in Celery settings)

### Usage Recommendations

For optimal performance with multi-page TIFF files:

1. **Split Very Large Files**: For files with more than 200 pages, consider splitting them before uploading
2. **Monitor Server Resources**: Watch server memory usage during large file processing
3. **Consider Batch Size**: Process multiple smaller files rather than one very large file when possible
4. **Increase Resources for Production**: In production environments with frequent multi-page processing, increase worker memory allocation

## API Access

JP2Forge Web provides a RESTful API for programmatic access to its conversion capabilities. This enables integration with other systems or automation of conversion workflows.

### Authentication

API requests require authentication using token-based authentication:

```bash
# Request an authentication token
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Response will include your access token
# {"token": "93138ba960fde325b3a20471b3fd449a23fd9b5a"}
```

Include this token in all subsequent requests:

```bash
curl -H "Authorization: Token 93138ba960fde325b3a20471b3fd449a23fd9b5a" \
  http://localhost:8000/api/jobs/
```

### Available Endpoints

| Endpoint | HTTP Method | Description |
|----------|-------------|-------------|
| `/api/jobs/` | GET | List all jobs for authenticated user |
| `/api/jobs/` | POST | Create a new conversion job |
| `/api/jobs/{id}/` | GET | Get details for a specific job |
| `/api/jobs/{id}/` | DELETE | Delete a specific job |
| `/api/jobs/{id}/retry/` | POST | Retry a failed job |
| `/api/stats/` | GET | Get system-wide conversion statistics |
| `/api/health/` | GET | Check system health and component status |

### Creating a Conversion Job

To create a new conversion job via the API:

```bash
# Create a new conversion job
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -F "file=@/path/to/image.tif" \
  -F "compression_mode=lossless" \
  -F "document_type=photograph" \
  -F "bnf_compliant=false"
```

Required parameters:
- `file`: The image file to convert
- `compression_mode`: One of `lossless`, `lossy`, `supervised`, or `bnf_compliant`

Optional parameters:
- `document_type`: One of `photograph`, `heritage_document`, `color`, or `grayscale` (default: `photograph`)
- `quality`: Integer between 20-100 (only used for `lossy` and `supervised` modes)
- `bnf_compliant`: Boolean indicating whether to apply BnF compliance (default: `false`)
- `description`: Optional text description of the job

### Monitoring Job Status

To check the status of a job:

```bash
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://localhost:8000/api/jobs/123/
```

Response includes job status, progress, and result file URLs when complete:

```json
{
  "id": 123,
  "status": "completed",
  "created_at": "2025-05-04T14:30:45Z",
  "updated_at": "2025-05-04T14:32:12Z",
  "compression_mode": "lossless",
  "document_type": "photograph",
  "bnf_compliant": false,
  "original_filename": "sample.tif",
  "original_size": 15728640,
  "converted_size": 7340032,
  "compression_ratio": 2.14,
  "psnr": "Infinity",
  "ssim": "1.0",
  "result_files": [
    {
      "page": 1,
      "url": "http://localhost:8000/media/jobs/123/output/sample_page1.jp2"
    }
  ]
}
```

### API Rate Limits

To ensure system stability:
- Anonymous requests: 20 per hour
- Authenticated requests: 100 per hour, 1000 per day
- File uploads: 50 per day per user

### API Documentation

Complete API documentation is available at `/api/docs/` when the application is running. It provides an interactive interface where you can:
- Explore all available endpoints
- Test API calls directly from the browser
- See detailed parameter requirements and response formats

### Integration Examples

Sample code for common integrations:

#### Python

```python
import requests

# Authentication
auth_response = requests.post(
    'http://localhost:8000/api/token/',
    json={'username': 'your_username', 'password': 'your_password'}
)
token = auth_response.json()['token']
headers = {'Authorization': f'Token {token}'}

# Upload and convert a file
with open('image.tif', 'rb') as file:
    response = requests.post(
        'http://localhost:8000/api/jobs/',
        headers=headers,
        files={'file': file},
        data={
            'compression_mode': 'lossless',
            'document_type': 'photograph'
        }
    )
    
job_id = response.json()['id']

# Check job status
job_response = requests.get(
    f'http://localhost:8000/api/jobs/{job_id}/',
    headers=headers
)
job_data = job_response.json()

# Download result when complete
if job_data['status'] == 'completed':
    for result in job_data['result_files']:
        file_url = result['url']
        output_filename = f"converted_page{result['page']}.jp2"
        
        with requests.get(file_url, stream=True) as r:
            with open(output_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
```

#### JavaScript

```javascript
// Authenticate
async function getToken() {
  const response = await fetch('http://localhost:8000/api/token/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      username: 'your_username',
      password: 'your_password'
    })
  });
  const data = await response.json();
  return data.token;
}

// Convert a file
async function convertFile(file) {
  const token = await getToken();
  
  const formData = new FormData();
  formData.append('file', file);
  formData.append('compression_mode', 'lossless');
  formData.append('document_type', 'photograph');
  
  const response = await fetch('http://localhost:8000/api/jobs/', {
    method: 'POST',
    headers: { 'Authorization': `Token ${token}` },
    body: formData
  });
  
  return await response.json();
}

// Monitor job status
async function checkJobStatus(jobId) {
  const token = await getToken();
  
  const response = await fetch(`http://localhost:8000/api/jobs/${jobId}/`, {
    headers: { 'Authorization': `Token ${token}` }
  });
  
  return await response.json();
}
```

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

## Troubleshooting Redis and Task Processing Issues

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

This section of documentation provides practical solutions to the Redis issues that can cause JP2Forge processing jobs to get stuck in "pending" state.

## Error Handling and Troubleshooting

### Common Conversion Errors

Below are common errors you may encounter during the conversion process and how to resolve them:

#### File Upload Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "File too large" | File exceeds the `MAX_UPLOAD_SIZE` setting | Resize the image or increase the `MAX_UPLOAD_SIZE` in your `.env` file |
| "Unsupported file format" | File extension not recognized | Ensure your file has one of these extensions: .jpg, .jpeg, .tif, .tiff, .png, .bmp |
| "Invalid file content" | File is corrupted or not the format its extension suggests | Check the file integrity with another application or convert to a supported format |

#### Conversion Process Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "Memory error during conversion" | Server lacks sufficient memory for large file processing | Use a smaller file or increase the server memory allocation |
| "JP2Forge command failed" | Issue with the underlying JP2Forge library | Check logs/converter.log for detailed error messages |
| "Metadata extraction failed" | ExifTool not properly installed or accessible | Verify ExifTool is installed and in your PATH |
| "Timeout during conversion" | Conversion taking longer than allowed time | Adjust the Celery task timeout setting in `settings.py` |

#### Task Queue Errors

| Error | Possible Cause | Solution |
|-------|---------------|----------|
| "Task stuck in pending state" | Redis connection issues | See [Redis Troubleshooting](#troubleshooting-redis-and-task-processing-issues) section |
| "Task failed with unknown error" | Unhandled exception in the worker process | Check logs/celery.log for the full traceback |

### Debugging Conversion Issues

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

### JPEG2000 Conversion Results

#### Expected Output Quality

The JP2Forge Web application produces high-quality JPEG2000 files with different characteristics based on the selected compression mode. Below are typical results you can expect for each compression option:

##### Lossless Mode
- **Visual Quality**: Identical to the original image with no perceptible differences
- **PSNR**: Infinity (mathematically lossless)
- **SSIM**: 1.0 (perfect structural similarity)
- **Compression Ratio**: Typically 1.5:1 to 3:1 depending on image content
- **Best For**: Archival purposes, medical imaging, scientific data

##### Lossy Mode (Quality = 90)
- **Visual Quality**: Visually indistinguishable from original for most content
- **PSNR**: 40-50 dB (excellent quality)
- **SSIM**: 0.97-0.99
- **Compression Ratio**: Typically 10:1 to 20:1
- **Best For**: High-quality access copies, general distribution

##### Lossy Mode (Quality = 50)
- **Visual Quality**: Minor artifacts may be visible in detailed areas
- **PSNR**: 32-38 dB (good quality)
- **SSIM**: 0.90-0.95
- **Compression Ratio**: Typically 30:1 to 50:1
- **Best For**: Web distribution, storage optimization

##### BnF Compliant Mode
- **Visual Quality**: Optimized for cultural heritage standards
- **PSNR**: Varies by document type but typically 38+ dB
- **SSIM**: 0.95+ (high fidelity)
- **Compression Ratio**: Fixed based on document type (4:1 for photographs and heritage documents, 6:1 for color, 16:1 for grayscale)
- **Best For**: Heritage collections, library digitization projects

#### Example Output Comparison

Here's a comparison of file sizes and quality metrics for typical input files:

| Original Format | Size | JP2 Lossless | JP2 Lossy (Q90) | JP2 Lossy (Q50) | JP2 BnF Mode |
|-----------------|------|--------------|-----------------|-----------------|--------------|
| 24MP JPEG Photo | 8 MB | 4.5 MB (1.8:1) | 600 KB (13:1) | 300 KB (27:1) | 2 MB (4:1) |
| A4 Color TIFF | 70 MB | 30 MB (2.3:1) | 7 MB (10:1) | 2.5 MB (28:1) | 11.7 MB (6:1) |
| A3 Grayscale TIFF | 40 MB | 15 MB (2.7:1) | 4 MB (10:1) | 1.5 MB (27:1) | 2.5 MB (16:1) |

**Important Note About BnF Mode**: The "BnF Mode" column shows results when using the Bibliothèque nationale de France (BnF) compliant settings. This mode applies specific standardized compression ratios required by the BnF for digital preservation:
- 4:1 compression ratio for photographs and heritage documents (fixed, not adjustable)
- 6:1 compression ratio for color documents (fixed, not adjustable)
- 16:1 compression ratio for grayscale documents (fixed, not adjustable)

These standardized ratios ensure that cultural heritage materials meet the BnF's specific requirements for digital archives. Unlike other modes where compression can be adjusted, BnF mode uses these preset ratios to guarantee compliance with their preservation standards.

#### Quality Metrics Explained

The application provides two key metrics to assess the quality of converted images:

1. **PSNR (Peak Signal-to-Noise Ratio)**:
   - Measured in decibels (dB)
   - Higher values indicate better quality
   - 30+ dB: Good quality
   - 40+ dB: Excellent quality
   - 50+ dB: Nearly indistinguishable from original

2. **SSIM (Structural Similarity Index)**:
   - Range from 0 to 1
   - Higher values indicate better structural similarity
   - 0.90+: Good quality
   - 0.95+: Excellent quality
   - 0.98+: Nearly indistinguishable from original

#### JPEG2000 Format Advantages

The JPEG2000 format offers several advantages over traditional formats:

- **Progressive decoding**: Images can be viewed at lower resolution before fully downloading
- **Region of interest coding**: Important parts of an image can be encoded with higher quality
- **Multiple resolution levels**: Different resolution versions are embedded in a single file
- **Alpha channel support**: Transparency information can be preserved
- **High bit-depth support**: Up to 16 bits per component (vs. 8 bits in standard JPEG)
- **Lossless and lossy compression**: Both options available in the same format

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

You can copy the above block to create your `.env` file, or use the provided `.env.example` file as a starting point.

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
- **JP2Forge 0.9.6**: JPEG2000 conversion library (updated from 0.9.1)
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

**Important Update (May 2025)**: JP2Forge 0.9.6 includes significant improvements to the reporting mechanism, fixing issues in single file processing mode and adding comprehensive testing capabilities. The JP2Forge Web adapter is fully compatible with this new version and benefits from the enhanced reporting features.

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

## BnF Compliance Information

The JP2Forge Web application provides support for creating JPEG2000 files that comply with the Bibliothèque nationale de France (BnF) digitization standards. This implementation is based on the following official BnF documents:

1. **BnF Referential (2015)**: [Référentiel de format de fichier image v2](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)

2. **BnF Documentation (2021)**: [Formats de données pour la préservation à long terme](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

### BnF Compliance Features

The BnF compliance mode ensures that JPEG2000 files meet the specific technical requirements set by the Bibliothèque nationale de France for digital preservation of cultural heritage materials. According to the JP2Forge documentation, this includes:

#### Compression Ratios

BnF mode uses fixed compression ratios based on document types:

| Document Type | BnF Notation | Standard Notation | Option |
|---------------|--------------|-------------------|--------|
| Photograph | 1:4 | 4:1 | `document_type=photograph` |
| Heritage Document | 1:4 | 4:1 | `document_type=heritage_document` |
| Color | 1:6 | 6:1 | `document_type=color` |
| Grayscale | 1:16 | 16:1 | `document_type=grayscale` |

**Note on Notation**: The BnF documentation uses input:output notation (1:X), whereas the compression ratios in JP2Forge Web are typically shown in output:input notation (X:1). For example, a BnF ratio of 1:6 means the output is 6 times smaller than the input, which is equivalent to a 6:1 ratio in standard notation.

#### Technical Parameters

When BnF compliance mode is enabled, the following technical parameters are applied:

- **Compression**: Irreversible (9-7 floating transform, ICT)
- **Resolution Levels**: 10
- **Quality Levels**: 10
- **Progression Order**: RPCL (Resolution-Position-Component-Layer)
- **Robustness Markers**: SOP, EPH, PLT
- **Code Block Size**: 64x64
- **Tile Size**: 1024x1024

Users can enable BnF compliance in two ways:
1. By selecting the dedicated "BnF Compliant" compression mode
2. By enabling the BnF compliance checkbox while using other compression modes
