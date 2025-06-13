# JP2Forge Web Troubleshooting Guide

This guide provides solutions for common issues you might encounter when using the JP2Forge Web application.

## Installation and Setup Issues

### JP2Forge Dependency Problems

The most common installation issue is related to the JP2Forge core library dependency.

#### Error: JP2Forge Installation Failed
```bash
ERROR: Could not find a version that satisfies the requirement jp2forge==0.9.6
```

**Root Cause:** The JP2Forge installation from PyPI may fail due to:
- Network connectivity issues with PyPI
- Python version incompatibility (requires Python >=3.8)
- Package index synchronization delays

**Solutions:**

1. **Use Mock Mode (Recommended for Testing)**
   ```bash
   echo "JP2FORGE_MOCK_MODE=True" >> .env
   ./setup.sh
   ```
   This allows full UI testing without actual JPEG2000 conversion.

2. **Retry JP2Forge 0.9.6 Installation**
   ```bash
   # Ensure you're installing the exact required version
   pip install jp2forge==0.9.6
   
   # Check Python version compatibility
   python --version  # Should be 3.8 or higher
   
   # Check PyPI connectivity
   pip index versions jp2forge
   ```

3. **Temporarily Skip JP2Forge (Development Only)**
   ```bash
   # Comment out JP2Forge in requirements.txt for testing
   sed -i 's/^jp2forge/#jp2forge/' requirements.txt
   ./setup.sh
   ```
   ⚠️ **Warning:** This is only for development/testing. Production requires JP2Forge 0.9.6.

#### Verification Commands

Check if JP2Forge 0.9.6 is working:
```bash
python -c "
try:
    import core.types
    # Additional check to verify it's the right version
    import core
    print('✅ JP2Forge 0.9.6 installed and working')
    print('Full JPEG2000 conversion functionality available')
except ImportError as e:
    print('❌ JP2Forge 0.9.6 not available:', e)
    print('⚠️  Application will run in mock mode')
"
```

### Docker Setup Issues

#### Missing Docker Entrypoint Files
```bash
ERROR: failed to calculate checksum of ref: "/docker-entrypoint.sh": not found
```

**Solution:** Ensure these files exist in your project root:
- `docker-entrypoint.sh`
- `healthcheck.sh`

If missing, they should be created automatically by the setup script.

#### Build Fails Due to JP2Forge
```bash
ERROR: Could not find a version that satisfies the requirement jp2forge==0.9.6
```

**Solution:** Temporarily comment out JP2Forge in requirements.txt:
```bash
sed -i 's/^jp2forge/#jp2forge/' requirements.txt
./docker_setup.sh
```

### Environment Configuration Issues

#### Secret Key Not Set
```bash
django.core.exceptions.ImproperlyConfigured: The SECRET_KEY setting must not be empty
```

**Solution:** Create or update your `.env` file:
```bash
echo "SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" > .env
echo "DEBUG=True" >> .env
echo "ALLOWED_HOSTS=localhost,127.0.0.1" >> .env
```

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