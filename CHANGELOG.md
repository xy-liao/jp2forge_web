# Release Notes

## v0.1.4 (May 7, 2025) - HTTP Method Handling & Documentation Improvements

This release focuses on improving HTTP method handling for increased security and aligning documentation across the system for a better user experience.

### Security Improvements

- Enhanced HTTP method handling with proper method decorators to enforce GET/POST restrictions
- Implemented explicit method validation for all view functions in converter app
- Fixed potential CSRF vulnerabilities by requiring POST method for state-changing actions
- Added @require_GET decorator to read-only views for better security
- Improved logout security by enforcing POST method requirement and proper CSRF protection

### Documentation Improvements

- Aligned HTML templates in templates/docs/ with their corresponding Markdown files in docs/
- Added missing "Mock Mode Information" section to user guide template
- Added "Important Note" about JP2Forge Web being a demonstration tool to documentation
- Added detailed BnF compliance information with reference documentation
- Added "What's New in v0.1.3" section to documentation home page
- Created unified documentation navigation system between static HTML and Markdown-based pages
- Fixed inconsistencies between documentation systems with a generic view function

### Technical Improvements

- Added view_documentation function to docs/views.py for improved navigation
- Updated URL patterns in docs/urls.py to support direct viewing of any documentation page by key
- Fixed navigation links between documentation pages for consistency
- Improved dark mode support in documentation templates

## v0.1.3 (May 6, 2025) - Docker Improvements & Security Updates

This release significantly improves the Docker setup with a more reliable and robust configuration, fixes the PostgreSQL driver detection, and includes critical security updates to multiple dependencies.

### Security Updates

- Updated Django from 4.2.10 to 4.2.20 to address:
  - SQL injection vulnerabilities in JSONField and QuerySet methods
  - Denial-of-service vulnerability in django.utils.text.wrap()
  - Multiple other security issues (CVE-2024-53908, CVE-2024-27351, CVE-2024-53907)
- Updated Pillow from 10.1.0 to 10.3.0 to address critical vulnerabilities (CVE-2023-50447, CVE-2024-28219)
- Updated Gunicorn from 21.2.0 to 23.0.0 to address HTTP Request/Response Smuggling vulnerability

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
- Fixed PostgreSQL driver detection in system information page to correctly identify psycopg2-binary package

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