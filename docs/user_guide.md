# JP2Forge Web Application User Guide

This guide explains how to use the JP2Forge Web application for converting images to JPEG2000 format.

## Important Note

JP2Forge Web serves primarily as a promotional demonstration for the JP2Forge script and its BnF (Bibliothèque nationale de France) compliance capabilities. This web interface implements a curated subset of JP2Forge's full functionality, focusing on showcasing key features in an accessible way. For access to all JP2Forge capabilities, users are encouraged to work directly with the [JP2Forge script](https://github.com/xy-liao/jp2forge).

## BnF Compliance Information

The JP2Forge Web application includes options for creating JPEG2000 files that comply with Bibliothèque nationale de France (BnF) digitization standards. These compliance settings are based on the following official BnF documents:

1. **BnF Referential (2015)**: [Référentiel de format de fichier image v2](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)

2. **BnF Documentation (2021)**: [Formats de données pour la préservation à long terme](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

The BnF compliance mode ensures that your JPEG2000 files meet the technical specifications required for submission to the BnF or similar cultural heritage institutions that follow these standards.

## Table of Contents

1. [Creating a New Conversion Job](#creating-a-new-conversion-job)
2. [Understanding Compression Options](#understanding-compression-options)
3. [Document Types](#document-types)
4. [BnF Compliance Options](#bnf-compliance-options)
5. [Mock Mode Information](#mock-mode-information)
6. [Viewing and Managing Jobs](#viewing-and-managing-jobs)
7. [Downloading Converted Files](#downloading-converted-files)

## Creating a New Conversion Job

To create a new conversion job:

1. Log in to your account
2. Navigate to the "New Job" page
3. Click "Choose Files" to select one or more image files to convert
4. Configure the conversion settings (explained below)
5. Click "Upload and Convert" to start the conversion process

The system supports batch conversion of multiple files in one job.

**File Size Limit:** The maximum allowed file size for uploads is 100MB per file. Larger files will need to be reduced before uploading.

## Understanding Compression Options

JP2Forge offers four compression modes, each suited to different needs:

### Lossless
- Preserves all image data perfectly
- Results in larger file sizes
- Ideal for archival purposes where no quality loss is acceptable
- No quality setting is needed (automatically hidden)

### Lossy
- Achieves smaller files by allowing controlled quality reduction
- Quality level is adjustable (20-100)
- Good for web access copies or when storage space is limited

### Supervised
- Expert-level settings with fine-tuned parameters
- Allows detailed control of the compression process
- Quality level is adjustable (20-100)
- Best for specialized needs or when precise control is required

### BnF Compliant
- Follows Bibliothèque nationale de France digitization standards
- Specialized preservation settings for cultural heritage materials
- No quality setting is needed (automatically configured)
- When selected, the BnF Compliant checkbox is automatically checked and disabled

## Document Types

Select the document type that best matches your source material:

### Photograph
- Optimized for detailed photos and continuous-tone images
- Special handling for detail preservation in high frequencies

### Heritage Document
- Best for historical manuscripts, documents, and maps
- Emphasizes text clarity and detail preservation

### Color
- Optimized for vibrant color content and general graphics
- Enhanced color fidelity

### Grayscale
- Best for black & white or grayscale content
- Focuses on contrast preservation

## BnF Compliance Options

The application provides a checkbox option to enable BnF (Bibliothèque nationale de France) compliance standards:

1. **BnF Compliant Compression Mode**: Select "BnF Compliant" from the compression mode dropdown. This applies BnF standards as a preset and automatically checks the BnF Compliant checkbox.

2. **BnF Compliant Checkbox**: When using other compression modes (Lossless, Lossy, or Supervised), you can enable this checkbox to apply BnF standards while maintaining your selected compression approach.

### BnF Compliance Implementation

When you enable BnF compliance (either through the dedicated compression mode or via the checkbox), the application passes this parameter to the underlying JP2Forge library. The library then applies the appropriate technical parameters required by BnF standards.

### Understanding BnF Compliance Reports

BnF compliance reports contain two main sections that may appear to provide contradictory information:

- **bnf_validation**: Evaluates if the file meets overall BnF format specifications (wavelet transform, resolution levels, etc.)
- **bnf_compliance**: Specifically checks if the target compression ratio was achieved

If your report shows `"is_compliant": true` in the bnf_validation section but `"is_compliant": false` in the bnf_compliance section, this is normal and expected behavior for certain types of images. According to BnF standards:

1. The system first attempts to achieve the target compression ratio using lossy compression
2. If the target ratio cannot be achieved (which happens with certain image types), the system automatically falls back to lossless compression
3. This fallback is considered fully compliant with BnF standards, which is why the overall validation passes

This automatic fallback mechanism is specifically mentioned in the BnF documentation to prevent excessive information loss for images that don't compress well with lossy methods.

### BnF Reference Documentation

For reference, the implementation follows standards defined in these official BnF documents:

1. **BnF Referential (2015)**: [Référentiel de format de fichier image v2](https://www.bnf.fr/sites/default/files/2018-11/ref_num_fichier_image_v2.pdf)

2. **BnF Documentation (2021)**: [Formats de données pour la préservation à long terme](https://www.bnf.fr/sites/default/files/2021-04/politiqueFormatsDePreservationBNF_20210408.pdf)

According to these documents, BnF recommended compression ratios for different document types are:

| Document Type | BnF Notation | Standard Notation | Option |
|---------------|--------------|-------------------|--------|
| Photograph | 1:4 | 4:1 | `document_type=photograph` |
| Heritage Document | 1:4 | 4:1 | `document_type=heritage_document` |
| Color | 1:6 | 6:1 | `document_type=color` |
| Grayscale | 1:16 | 16:1 | `document_type=grayscale` |

## Mock Mode Information

JP2Forge Web includes a testing/development feature called "Mock Mode" which can be enabled by setting `JP2FORGE_MOCK_MODE=True` in your `.env` file. This feature is important to understand:

### What Mock Mode Does

When mock mode is enabled, JP2Forge Web simulates the conversion process without requiring the actual JP2Forge library:

1. Files are **not** truly converted to JPEG2000 format - they are merely copied or small placeholder files are created
2. The resulting files with `.jp2` extension are **not valid JPEG2000 files** and lack the expected compression benefits
3. The system generates fictitious quality metrics (PSNR, SSIM) and compression ratios for display purposes
4. All the web interface functionality can be tested without the actual conversion engine

### When to Use Mock Mode

Mock mode is appropriate for:
- UI development work on JP2Forge Web
- Testing the application flow without installing the JP2Forge library
- Demonstration purposes when actual conversion functionality is not needed

### Limitations of Mock Mode

Important limitations to be aware of:
- Files are not actually compressed - they remain their original size or become small placeholders
- Image information is not preserved in any meaningful way
- The output files cannot be viewed as JPEG2000 images by other software
- Reported statistics are simulated, not real measurements

### Identifying Mock Mode

When mock mode is active, the following indicators appear:
- A notice appears on the status page indicating mock mode
- Job history shows mock conversions labeled as such
- Log files record that mock mode is being used

For actual JPEG2000 conversion, you must disable mock mode and ensure the JP2Forge library is properly installed and configured.

## Viewing and Managing Jobs

After submitting a conversion job:

1. You'll be redirected to the job detail page
2. The status will initially show as "Pending" or "Processing"
3. Refresh the page or wait for automatic updates to see progress
4. Once completed, the status will change to "Completed" and download links will appear

From the "My Jobs" page, you can:
- View all your conversion jobs
- Filter jobs by status
- Sort by different criteria
- Delete completed jobs you no longer need

## Downloading Converted Files

After a job completes successfully:

1. Go to the job detail page
2. Click the "Download" button next to each converted file
3. For multi-page documents, you'll see individual download links for each page

Converted files are kept available for download for 30 days by default.