# JP2Forge Web Application User Guide

This guide explains how to use the JP2Forge Web application for converting images to JPEG2000 format.

## Important Note

JP2Forge Web serves primarily as a promotional demonstration for the JP2Forge script and its BnF (Bibliothèque nationale de France) compliance capabilities. This web interface implements a curated subset of JP2Forge's full functionality, focusing on showcasing key features in an accessible way. For access to all JP2Forge capabilities, users are encouraged to work directly with the [JP2Forge script](https://github.com/xy-liao/jp2forge).

## BnF Compliance Information

The JP2Forge Web application includes options for creating JPEG2000 files that comply with Bibliothèque nationale de France (BnF) digitization standards. These compliance settings are based on:

1. **BnF's Technical Guidelines for Digitization**: The BnF maintains technical requirements for digital preservation of cultural heritage materials, which include specific parameters for JPEG2000 encoding.

2. **JP2 Format Implementation**: The JP2Forge implementation follows the BnF's recommendations for JPEG2000 codestream parameters, progression order, and metadata requirements.

The BnF compliance mode ensures that your JPEG2000 files meet the technical specifications required for submission to the BnF or similar cultural heritage institutions that follow these standards. For the most current and detailed BnF digitization specifications, please consult the official BnF documentation at [https://www.bnf.fr/en/digital-preservation](https://www.bnf.fr/en/digital-preservation).

## Table of Contents

1. [Creating a New Conversion Job](#creating-a-new-conversion-job)
2. [Understanding Compression Options](#understanding-compression-options)
3. [Document Types](#document-types)
4. [BnF Compliance Options](#bnf-compliance-options)
5. [Viewing and Managing Jobs](#viewing-and-managing-jobs)
6. [Downloading Converted Files](#downloading-converted-files)

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

There are two ways to apply BnF (Bibliothèque nationale de France) standards:

1. **BnF Compliant Compression Mode**: Select "BnF Compliant" from the compression mode dropdown. This applies all BnF standards as a complete preset and automatically checks the BnF Compliant checkbox.

2. **BnF Compliant Checkbox**: When using other compression modes (Lossless, Lossy, or Supervised), you can enable this checkbox to apply BnF standards while maintaining your selected compression approach.

**Key Difference:**
- The BnF Compliant mode applies a comprehensive set of BnF specifications
- The checkbox option allows you to apply BnF standards while using your preferred compression mode

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