# JP2Forge Test Kit

This directory contains test sc## Directory Structure

- `test_kit/` - Contains all test scripts and fixtures
  - `*.json` - Test fixture files for various combinations of document types and parameters
  - `conversion_test.py`, `test_reports.py`, etc. - Test script files
  - `test_output/` - Directory containing test outputs, reports, and temporary files
  
## Usage Notes

1. All test scripts are designed to be run from the project root directory.
2. The scripts will automatically create test images if none are found in the project.
3. Test outputs are stored in the `test_kit/test_output` directory. and test fixtures for the JP2Forge web application. It provides a comprehensive set of tools for testing different aspects of the JP2Forge functionality.

## Test Scripts

### Conversion Testing
- `conversion_test.py` - Performs a quick test conversion using image files that exist in the project. Use for simple testing without needing to specify an image path.
  ```
  python test_kit/conversion_test.py                            # Default settings
  python test_kit/conversion_test.py --mode lossy               # Test lossy compression
  python test_kit/conversion_test.py --mode bnf_compliant --document-type heritage_document  # Test BnF compliance
  ```

### Import Testing
- `jp2forge_import_test.py` - Tests the different import paths for JP2Forge modules. Use to troubleshoot import path issues and check JP2Forge installation.
  ```
  python test_kit/jp2forge_import_test.py
  ```

- `check_jp2forge.py` - Simple script to check if JP2Forge is installed and verify its version.
  ```
  python test_kit/check_jp2forge.py
  ```

### Report Testing
- `test_reports.py` - Systematically tests report generation for all possible combinations of document types, compression modes, and BnF compliance settings.
  ```
  python test_kit/test_reports.py [--verbose] [--save-reports] [--force-mock]
  ```

### BnF Interpretation Testing
- `test_bnf_interpretation.py` - Tests the interpretation of BnF validation results, verifying that the interpretation logic correctly handles the relationship between format and compression ratio compliance.
  ```
  python test_kit/test_bnf_interpretation.py [--verbose]
  ```

### Report Download Testing
- `test_report_downloads.py` - Tests the ability to download reports for all compression modes and document types through the API endpoint.
  ```
  python test_kit/test_report_downloads.py [--verbose] [--server-url SERVER_URL] [--username USERNAME] [--password PASSWORD]
  ```

## Test Fixtures

This directory also contains JSON files that serve as test fixtures for various test scenarios. These files represent expected output for different conversion scenarios with combinations of:

- Document types: photograph, heritage_document, color, grayscale
- Compression modes: lossless, lossy, supervised, bnf_compliant
- BnF compliance settings: true/false
- Page structure: single-page and multi-page documents

## Usage Notes

1. All test scripts are designed to be run from the project root directory.
2. The scripts will automatically create test images if none are found in the project.
3. Test outputs are stored in the \`test_output\` directory.

## Recent Changes

- The \`conversion_test.py\` and \`jp2forge_import_test.py\` scripts were moved from the root directory to the test_kit directory for better organization.
