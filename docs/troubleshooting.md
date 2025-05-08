# JP2Forge Web Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the JP2Forge Web application.

## Conversion Issues

### File Upload Problems

| Issue | Solution |
|-------|----------|
| "File too large" error | Your file exceeds the 100MB limit. Try splitting large files or resizing images before uploading. |
| "Unsupported file format" error | JP2Forge Web only accepts JPG/JPEG, TIFF/TIF, PNG, and BMP formats. Convert your file to a supported format. |
| Upload appears to freeze | Check your internet connection. For very large files, uploads may take time - be patient. |

### Conversion Failures

| Issue | Solution |
|-------|----------|
| Job shows "Failed" status | Check the job details page for specific error messages. Most common causes are file corruption or memory limitations. |
| Job stuck in "Pending" | The task queue might be experiencing delays. Try refreshing the page or checking back later. |
| "JP2Forge command failed" | Your file might have special characteristics that the converter can't process. Try using different conversion settings. |

### Quality Issues

| Issue | Solution |
|-------|----------|
| Output file has visual artifacts | Try using lossless mode instead of lossy to preserve all image data. |
| Poor compression ratio | For better compression, use lossy mode with appropriate quality settings for your content type. |
| Output file is larger than expected | This can happen with lossless compression of already optimized files. Try supervised mode for better control. |

### BnF Compliance Issues

| Issue | Solution |
|-------|----------|
| "BnF Compliance: Failed" | Check if you selected the correct document type for your content. Heritage documents have different requirements than photographs. |
| "Target Ratio: No" with fallback | This is normal for some files that don't compress well. JP2Forge automatically falls back to lossless compression to maintain quality. |
| "No metrics shown" for BnF-compliant jobs | This is expected - BnF compliance is determined by parameters rather than visual metrics. |

## Account and Access Problems

### Login Issues

| Issue | Solution |
|-------|----------|
| Can't log in | Verify your username and password. Use the password reset function if needed. |
| Session expires too quickly | Your browser might be clearing cookies. Adjust your browser privacy settings. |
| "Access denied" errors | You may not have the necessary permissions for that action. Contact your administrator. |

### Job Management Problems

| Issue | Solution |
|-------|----------|
| Can't see your jobs | Make sure you're logged in with the same account that created the jobs. |
| Can't delete a job | Only completed or failed jobs can be deleted. Running jobs must finish first. |
| Jobs disappear automatically | Completed jobs are kept for 30 days by default, then automatically removed. |

## Technical Issues

### Browser Problems

| Issue | Solution |
|-------|----------|
| Interface displays incorrectly | Try clearing your browser cache or try a different browser (Chrome and Firefox are recommended). |
| Can't download files | Check your browser's download settings and ensure pop-ups are allowed for the application URL. |
| Page errors or blank screens | Try refreshing the page or clearing your browser cache. |

### Docker Environment Issues

For users running their own Docker installation:

#### Application isn't starting

1. Check container status:
   ```bash
   docker compose ps
   ```

2. Check container logs:
   ```bash
   docker compose logs web
   docker compose logs worker
   ```

3. Restart all services:
   ```bash
   docker compose restart
   ```

#### Redis and Celery Issues

If jobs stay in "Pending" state:

1. Restart the worker:
   ```bash
   docker compose restart worker
   ```

2. Check Redis status:
   ```bash
   docker compose exec redis redis-cli ping
   ```
   Should return "PONG".

## Getting More Help

If you continue to experience issues:

1. Check the [GitHub repository](https://github.com/xy-liao/jp2forge_web) for known issues or to report new ones.
2. Contact your system administrator if you're using a managed instance.
3. Try converting a simple test file (small JPG) to verify basic functionality.