# Release Notes

## v0.1.6 (June 21, 2025) - Documentation and UI Improvements

This release focuses on comprehensive documentation updates, UI consistency improvements, and Docker modernization in preparation for publication.

### Documentation Enhancements

- **Comprehensive docstring updates** across all Python modules (models, views, forms, tasks)
- **Enhanced README.md** with updated version requirements and security features
- **Improved code documentation** with detailed function and class descriptions
- **Better inline documentation** for complex business logic and batch operations
- **Consistent docstring format** following Google/Sphinx standards throughout the codebase

### User Interface Improvements

- **Consistent badge colors** in system information page - badges now use unified colors within each category
- **Updated version information** to reflect current Python and dependency versions
- **Enhanced visual consistency** across dependency information displays

### Infrastructure Updates

- **Docker modernization** - Updated from Python 3.11 to Python 3.12 for better performance and security
- **Updated base images** in Dockerfile to use latest Python 3.12-slim
- **Consistent version requirements** between documentation and Docker configuration
- **Enhanced security baseline** with latest Python runtime

### Code Quality Improvements

- **Comprehensive model documentation** for ConversionJob with detailed field descriptions
- **Enhanced form documentation** including JavaScript behavior and validation rules
- **Detailed view function documentation** especially for batch operations and file handling
- **Better error handling documentation** and security consideration notes
- **Improved inline comments** for complex algorithms and business logic

### Technical Improvements

- **Enhanced type hints** and parameter documentation throughout the codebase
- **Better documentation of BnF compliance features** and their implementation
- **Clearer explanation of multi-page TIFF handling** and ZIP file organization
- **Improved documentation of Celery task processing** and error recovery

### Breaking Changes

- **Docker images now use Python 3.12** (backward compatible, but rebuilds required)
- **Version badges updated** to reflect v0.1.6 release

## v0.1.5 (June 20, 2025) - JP2Forge 0.9.7 Compatibility Update

This release updates JP2Forge Web to support JP2Forge 0.9.7, the latest version of the underlying JPEG2000 conversion library with enhanced capabilities and improved reporting.

### JP2Forge Library Updates

- Updated JP2Forge dependency from 0.9.6 to 0.9.7 for enhanced conversion capabilities
- Enhanced JP2Forge adapter to correctly detect and support JP2Forge 0.9.7
- Improved version compatibility handling to support both 0.9.6 and 0.9.7
- Updated Docker containers to automatically install JP2Forge 0.9.7

### Documentation Updates

- Updated all documentation to reflect JP2Forge 0.9.7 compatibility
- Enhanced installation guides with version-specific information
- Revised README with updated dependency requirements and compatibility notes

### Technical Improvements

- Enhanced JP2Forge adapter version detection for better compatibility
- Updated container builds to ensure JP2Forge 0.9.7 installation
- Improved error handling for version compatibility issues
- Updated requirements.txt with clear version specifications

### Breaking Changes

- JP2Forge 0.9.7 is now the recommended version (backward compatible with 0.9.6)
- Docker containers now default to JP2Forge 0.9.7 installation

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
- Created unified documentation navigation system between static HTML and Markdown-based pages
- Fixed inconsistencies between documentation systems with a generic view function

### Technical Improvements

- Added view_documentation function to docs/views.py for improved navigation
- Updated URL patterns in docs/urls.py to support direct viewing of any documentation page by key
- Fixed navigation links between documentation pages for consistency
- Improved dark mode support in documentation templates


---

For support or to report issues, please visit the [GitHub repository](https://github.com/xy-liao/jp2forge_web).