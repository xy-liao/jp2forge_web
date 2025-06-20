# JP2Forge Web Application Documentation

Welcome to the documentation for JP2Forge Web, a Django-based web interface for the JP2Forge JPEG2000 conversion library.

## What's New in v0.1.5

The v0.1.5 release updates JP2Forge Web to support JP2Forge 0.9.7, the latest version of the underlying JPEG2000 conversion library:

- **Updated JP2Forge dependency** from 0.9.6 to 0.9.7 for enhanced conversion capabilities
- **Enhanced adapter compatibility** with improved version detection for JP2Forge 0.9.7
- **Improved version compatibility handling** to support both 0.9.6 and 0.9.7
- **Updated Docker containers** to automatically install JP2Forge 0.9.7
- **Comprehensive documentation updates** reflecting JP2Forge 0.9.7 compatibility

See the [CHANGELOG.md](../CHANGELOG.md) file for complete details about this release.

## Previous Release: v0.1.4

The v0.1.4 release focused on improving HTTP method handling for increased security and aligning documentation across the system:

- **Enhanced HTTP method security** with proper GET/POST restrictions on all view functions
- **Fixed potential CSRF vulnerabilities** by adding explicit method validation
- **Aligned documentation templates** with their corresponding Markdown files for consistency

## Previous Release: v0.1.3

The v0.1.3 release included significant improvements to the Docker setup with a more reliable and robust configuration:

- **Complete Docker overhaul** with enhanced error handling and dependency management
- **Fixed critical issues** with Git-based dependency installation in Docker
- **Improved health checks** for services to prevent startup failures
- **Enhanced Docker setup script** with better error reporting and environment configuration

## Documentation Contents

1. [User Guide](user_guide.md) - How to use the web application features
2. [Docker Setup](docker_setup.md) - Docker installation and configuration instructions
3. [Troubleshooting](troubleshooting.md) - Solutions for common issues with Redis, Docker, and conversions

## About JP2Forge Web

JP2Forge Web is a Django-based web application that provides a user-friendly interface for converting various image formats to JPEG2000. It serves as a promotional demonstration for the JP2Forge script, focusing particularly on BnF (Bibliothèque nationale de France) compliance standards. This application showcases a subset of JP2Forge's capabilities rather than leveraging all available arguments of the underlying script. It's intended as a case study implementation that demonstrates how the JP2Forge script can be integrated into a web-based workflow.

Key aspects of this demonstration implementation include:
- User authentication and job management
- Batch image conversion
- Selected compression modes including BnF compliance
- Job status tracking and notifications
- Downloadable converted files

## Relationship to JP2Forge Core

This documentation covers only the web application interface. For documentation on the underlying JP2Forge core conversion scripts and their parameters, please refer to the separate [JP2Forge repository](https://github.com/xy-liao/jp2forge).

## Screenshots

![JP2Forge Web Dashboard](../static/images/docs/jp2forge_web_dashboard.png)