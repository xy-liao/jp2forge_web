# JP2Forge Web Application User Guide

This guide explains how to use the JP2Forge Web application for converting images to JPEG2000 format.

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