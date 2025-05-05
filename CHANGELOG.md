# Release Notes

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