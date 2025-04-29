# JP2Forge Web Application Documentation

This directory contains documentation for the **JP2Forge Web** application, which provides a web-based interface for the JP2Forge JPEG2000 conversion tool.

## About JP2Forge Web

JP2Forge Web is a Django-based web application that provides a user-friendly interface for converting various image formats to JPEG2000. It serves as a promotional demonstration for the JP2Forge script, focusing particularly on BnF (Bibliothèque nationale de France) compliance standards. This application showcases a subset of JP2Forge's capabilities rather than leveraging all available arguments of the underlying script. It's intended as a case study implementation that demonstrates how the JP2Forge script can be integrated into a web-based workflow.

Key aspects of this demonstration implementation include:
- User authentication and job management
- Batch image conversion
- Selected compression modes including BnF compliance
- Job status tracking and notifications
- Downloadable converted files

## Documentation Contents

1. [User Guide](user_guide.md) - How to use the web application
2. [Installation](installation.md) - Setup instructions for the web application
3. [Administration](administration.md) - Managing the application (for administrators)
4. [API Reference](api_reference.md) - If you want to interact with the web application programmatically

## Relationship to JP2Forge Core

This documentation covers only the web application interface. For documentation on the underlying JP2Forge core conversion scripts and their parameters, please refer to the separate JP2Forge documentation.

## Screenshots

![JP2Forge Web Dashboard](../static/images/dashboard-screenshot.png)