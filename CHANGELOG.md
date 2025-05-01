# Release Notes

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