# Notice for AI Assistant: JP2Forge Web Evaluation Request

## Task Overview

Please evaluate the implementation of JP2Forge core functionality in JP2Forge Web, with specific focus on BnF compliance features and potential misinformation.

## Background Information

JP2Forge is a comprehensive command-line tool for converting images to JPEG2000 format with specialized support for BnF (Bibliothèque nationale de France) compliant workflows. JP2Forge Web is a web-based interface providing access to a subset of JP2Forge functionality.

## Critical Areas for Review

Based on an analysis from May 2025, please pay particular attention to these aspects:

### 1. BnF Compression Requirements

- **Document Type-Specific Compression Ratios**: JP2Forge Web likely has limited support for BnF document types (photograph/heritage: 1:4, color: 1:6, grayscale: 1:16) compared to full JP2Forge.
- **Tolerance Setting**: JP2Forge Web likely has fixed 5% tolerance without configuration options.
- **Resolution Levels**: Check if JP2Forge Web enforces the BnF requirement of 10 resolution levels.

### 2. BnF Metadata Requirements

- **XMP Metadata Structure**: JP2Forge Web likely has limited implementation compared to full JP2Forge.
- **UUID Box Implementation**: Verify if JP2Forge Web correctly implements UUID box according to BnF specifications.
- **Required BnF Metadata Fields**: Check if all required BnF metadata fields are supported.
- **Collision Detection for UUIDs**: This functionality is missing in both JP2Forge and JP2Forge Web - verify if any misleading claims exist.

### 3. BnF Robustness Markers

- **SOP/EPH/PLT Markers**: These are partially supported in JP2Forge (full with Kakadu) but likely limited or missing in JP2Forge Web. Check for any claims of full support.

### 4. Validation and Compliance Testing

- **BnF Compliance Validation**: Method exists in JP2Forge but not auto-integrated; JP2Forge Web likely has even more limited validation.
- **Compression Ratio Testing**: Methodology is incomplete in JP2Forge and likely even more limited in JP2Forge Web.

## Known Issues in JP2Forge Core

The following issues have been identified in JP2Forge core and are unlikely to be resolved in JP2Forge Web:

- Missing automatic BnF validation integration
- No UUID collision detection
- Incomplete implementation of BnF compression testing methodology
- No dedicated BnF compliance validator class
- Missing unit test infrastructure for BnF compliance

## Documentation Accuracy

Please evaluate if JP2Forge Web documentation accurately describes:
- The limitations compared to the core JP2Forge tool
- BnF compliance capabilities
- Which advanced features are unavailable

## Questions to Address

1. Does JP2Forge Web correctly implement the core BnF compliance features as described?
2. Are there any inaccurate claims about BnF compliance capabilities?
3. Is there clear communication about which features from the main JP2Forge tool are unavailable?
4. What recommendations would you make to improve BnF compliance in JP2Forge Web?

## Reference Information

JP2Forge Web is described as a "case study implementation showcasing selected functionality" of the main JP2Forge tool, with a focus on core BnF compliance features but lacking many advanced capabilities.

The evaluation should be based on BnF compliance requirements as outlined in:
- "Référentiel de format de fichier image v2" (2015)
- "Formats de données pour la préservation à long terme" (2021)

Thank you for your thorough evaluation.