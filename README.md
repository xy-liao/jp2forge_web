# JP2Forge Web Application v0.1.2

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 
[![Project Status: Active](https://img.shields.io/badge/Project%20Status-Active-green.svg)](https://github.com/xy-liao/jp2forge_web) 
[![Version: 0.1.2](https://img.shields.io/badge/Version-0.1.2-blue.svg)](https://github.com/xy-liao/jp2forge_web/releases/tag/v0.1.2)

A web interface for the JP2Forge JPEG2000 conversion library, providing an easy-to-use system for converting and managing image files in the JPEG2000 format.

**Important Note**: This application serves primarily as a promotional demonstration for the [JP2Forge script](https://github.com/xy-liao/jp2forge) and its BnF (Bibliothèque nationale de France) compliance capabilities. JP2Forge Web doesn't leverage all available arguments and features of the underlying JP2Forge script - it's a case study implementation showcasing selected functionality of the more comprehensive JP2Forge tool.

**Documentation**: All documentation is located in the [docs folder](docs/). For an overview of available documentation, see the [docs/README.md](docs/README.md) file.

## Quick Links

- [User Guide](docs/user_guide.md) - How to use the application
- [Docker Setup](docs/docker_setup.md) - Docker installation instructions
- [BnF Compliance Information](docs/bnf_compliance_improvements.md) - Details on BnF standards implementation
- [Troubleshooting](docs/troubleshooting.md) - Solutions for common issues
- [Last Update: May 6, 2025] - This is a test update to verify GitHub push functionality

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

## Supported File Formats

### Input Formats
- **JPEG/JPG**: Standard photographic format
- **TIFF/TIF**: Both single-page and multi-page TIFF files are supported
- **PNG**: Lossless raster graphics format
- **BMP**: Bitmap image format

### Output Format
- **JPEG2000/JP2**: Converted files follow the JP2 format specification
- Compliant with ISO/IEC 15444-1 (when using BnF compliance mode)

## Quick Start Installation

### Prerequisites

Before installing JP2Forge Web, ensure you have the following prerequisites installed:

- Python 3.8 or higher
- Redis (required for Celery task queue)
- ExifTool (for metadata functionality)

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/xy-liao/jp2forge_web.git
cd jp2forge_web

# Run the Docker setup script
chmod +x docker_setup.sh
./docker_setup.sh
```

For detailed Docker instructions, see the [Docker Setup Guide](docs/docker_setup.md).

### Manual Installation

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

For complete installation instructions and configuration options, see the [Installation Guide](docs/installation.md).

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [JP2Forge](https://github.com/xy-liao/jp2forge) - The core JPEG2000 conversion library
- [Django](https://www.djangoproject.com/) - The web framework used
- [Celery](https://docs.celeryq.dev/) - Distributed task queue
- [Bootstrap](https://getbootstrap.com/) - Frontend framework
