# JP2Forge Web Dockerfile
# Version: 0.1.4 (May 7, 2025)
# 
# This Dockerfile builds an environment for running the JP2Forge Web application.
# V0.1.4 improvements and fixes:
# - Enhanced HTTP method handling with proper GET/POST restrictions
# - Fixed potential CSRF vulnerabilities by requiring POST method for state-changing actions
# - Aligned documentation templates with their Markdown counterparts
# - Unified documentation navigation between systems
# - Improved logout security by enforcing POST method requirement
#
# V0.1.3 improvements and fixes:
# - Fixed context processor import issue with stats_processor
# - Improved logout functionality with custom view handler
# - Added Git dependency for properly installing requirements from Git repositories
# - Improved entrypoint handling and error recovery
# - Added necessary system dependencies for proper functionality
# - Optimized image layer structure for better caching
# - Enhanced startup process with proper health checks

FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /build

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install pip-audit

# Run security audit on dependencies
RUN pip-audit

# Final stage
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    DOCKER_ENVIRONMENT=true

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    netcat-traditional \
    libexif-dev \
    libheif-dev \
    exiftool \
    pkg-config \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Create a non-root user to run the app
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy project files selectively rather than recursively copying everything
# Copy Python application code
COPY *.py ./
COPY jp2forge_web/ ./jp2forge_web/
COPY converter/ ./converter/
COPY accounts/ ./accounts/
COPY docs/ ./docs/
COPY templates/ ./templates/
COPY static/ ./static/

# Copy scripts and config files
COPY *.sh ./
COPY docker-compose.yml ./

# Create necessary directories
RUN mkdir -p /app/media/jobs /app/media/reports /app/staticfiles /app/logs

# Ensure script permissions
RUN chmod +x /app/*.sh

# Set up entrypoint
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

# Set proper ownership for application files
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]

# Run server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "jp2forge_web.wsgi:application"]
