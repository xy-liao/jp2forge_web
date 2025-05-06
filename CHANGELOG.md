# Release Notes

## v0.1.8 (May 6, 2025) - Django Security Update

This release addresses a potential denial-of-service vulnerability in Django.

### Security Updates

- Updated Django from 4.2.17 to 4.2.20 to address:
  - Potential denial-of-service vulnerability in django.utils.text.wrap() method and wordwrap template filter when used with very long strings

## v0.1.7 (May 6, 2025) - Django Security Update

This release addresses a SQL injection vulnerability in Django when using Oracle databases.

### Security Updates

- Updated Django from 4.2.15 to 4.2.17 to address:
  - SQL injection vulnerability in django.db.models.fields.json.HasKey lookup when using Oracle databases
  - The vulnerability affects direct usage of the HasKey lookup with untrusted data as an lhs value

## v0.1.6 (May 6, 2025) - Gunicorn Security Update

This release addresses a critical HTTP Request/Response Smuggling vulnerability in Gunicorn.

### Security Updates

- Updated Gunicorn from 22.0.0 to 23.0.0 to address:
  - HTTP Request/Response Smuggling vulnerability (CVE not assigned yet)
  - Vulnerability related to improper validation of 'Transfer-Encoding' header
  - This fixes potential issues including cache poisoning, data exposure, session manipulation, and other serious security risks

## v0.1.5 (May 6, 2025) - Django Security Update

This release addresses a critical SQL injection vulnerability in Django.

### Security Updates

- Updated Django from 4.2.14 to 4.2.15 to address:
  - SQL injection vulnerability in QuerySet.values() and values_list() methods when using JSONField

## v0.1.4 (May 6, 2025) - Security Updates

This release addresses critical security vulnerabilities in several dependencies.

### Security Updates

- Updated Django from 4.2.10 to 4.2.14 to address:
  - CVE-2024-53908 (High severity)
  - CVE-2024-27351 (Moderate severity)
  - CVE-2024-53907 (Moderate severity)
- Updated Pillow from 10.1.0 to 10.3.0 to address:
  - CVE-2023-50447 (Critical severity)
  - CVE-2024-28219 (High severity)
- Updated Gunicorn from 21.2.0 to 22.0.0 to address:
  - CVE-2024-1135 (High severity)
  - CVE-2024-6827 (High severity)

## v0.1.3 (May 6, 2025) - Docker Improvements & Build Reliability

This release significantly improves the Docker setup with a more reliable and robust configuration that addresses previous deployment issues.

### Docker Improvements

- Completely redesigned Docker setup with improved reliability and error handling
- Added proper dependency checks for both PostgreSQL and Redis in container startup
- Fixed Git dependency issue that prevented proper installation of requirements
- Added robust error recovery and fallbacks in the entrypoint script
- Enhanced container networking and service discovery
- Added comprehensive health checks for all services

### Build & Setup Enhancements

- Fixed the issue with Git-based dependencies in Docker build
- Improved Docker Compose configuration with better volume management
- Enhanced environment variable handling with sane defaults
- Added more robust container restart policies
- Created new docker_setup.sh script with comprehensive error handling
- Improved database initialization and migration handling

### Technical Improvements

- Removed obsolete Docker Compose configuration attributes
- Added socket connectivity checks before database connection attempts
- Improved startup sequence with proper service dependency handling
- Enhanced logging for easier troubleshooting
- Added timeout management with multiple retry attempts

## v0.1.2 (May 5, 2025) - JSON Serialization Fix & Documentation Improvements

This release fixes the JSON serialization issue that caused some conversion jobs to fail and improves documentation for running the Celery worker.

### Critical Fixes

- Fixed JSON serialization error in metrics handling that was causing jobs to fail with "CHECK constraint failed: JSON_VALID("metrics")" error
- Fixed KeyError 'checks' in BnF compliance validation that was causing BnF mode jobs to fail
- Enhanced JSON data handling with robust error recovery for special values like infinity and NaN
- Added comprehensive validation and fallback mechanisms to prevent job failures due to serialization issues

### Documentation & Usability Improvements

- Added dedicated section in README on running and managing the Celery worker
- Created new `restart_celery.sh` script for easily restarting Celery worker after code changes
- Improved consistency in worker management commands
- Enhanced troubleshooting guidance for Celery-related issues

### Technical Improvements

- Implemented `ensure_json_serializable()` function with better validation for metrics data
- Improved error handling throughout the task processing pipeline
- Added proper handling for special numeric values in quality metrics

## v0.1.1 (May 4, 2025) - Redis Stability & Security Updates

This release focuses on improving Redis stability to prevent jobs from getting stuck and updating dependencies to address security vulnerabilities.

### Critical Fixes

- Fixed Redis persistence issues that were causing jobs to get stuck in "pending" state
- Added automatic Redis configuration in startup script to prevent write errors
- Created `monitor_redis.py` tool to detect and fix Redis configuration issues 
- Added `recover_stuck_jobs` management command to recover stuck jobs
- Updated documentation with comprehensive Redis troubleshooting guide

### Security Updates

- Updated Django from 4.2 to 4.2.10 to address security vulnerabilities
- Updated Pillow from 10.0.0 to 10.1.0 to fix security issues
- Updated Celery from 5.3.1 to 5.3.6
- Updated Redis from 4.6.0 to 5.0.1
- Updated other dependencies to latest secure versions

## v0.1.0 (May 1, 2025) - Initial Release

This is the first release of JP2Forge Web Application, a Django-based web interface for the JP2Forge JPEG2000 conversion library.

### Features

- Interactive dashboard with conversion statistics, storage metrics, and job monitoring
- JPEG2000 conversion with multiple compression modes:
  - Lossless: No data loss, larger file size
  - Lossy: Higher compression with data loss
  - Supervised: Quality-controlled compression with analysis
  - BnF Compliant: Follows Bibliothèque nationale de France standards
- Support for various document types:
  - Photograph: Standard photographic images
  - Heritage Document: Historical documents with high-quality settings
  - Color: General color images
  - Grayscale: Grayscale images
- Quality analysis with metrics:
  - PSNR (Peak Signal-to-Noise Ratio) calculation
  - SSIM (Structural Similarity Index) analysis
  - Compression ratio reporting
- Parallel processing of conversion jobs with Celery
- User authentication and job management
- Real-time job progress tracking
- Multi-page TIFF support
- Docker support for easy deployment
- Comprehensive documentation

### Technical Improvements

- Environment variable support for secure configuration
- Docker Compose setup for production deployment
- Mock mode for testing without JP2Forge dependencies
- Responsive UI with dark/light mode support
- Celery integration for background processing
- Comprehensive logging system
- Accessibility improvements

### Known Issues

- Mock mode simulates conversions but doesn't produce actual JPEG2000 files
- Some advanced JP2Forge library features are not yet exposed in the web interface

### Future Plans

- Integration with more JP2Forge advanced features
- Batch upload capabilities
- Enhanced reporting and analytics
- API for programmatic access
- User role management

---

For support or to report issues, please visit the [GitHub repository](https://github.com/xy-liao/jp2forge_web).