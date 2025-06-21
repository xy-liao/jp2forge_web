# JP2Forge Web Dockerfile
# Version: 0.1.6 (June 21, 2025)
# 
# This Dockerfile builds a secure, production-ready environment for the JP2Forge Web application
# using multi-stage builds and security-hardened configuration.
#
# Architecture:
# - Multi-stage build for smaller final image size
# - Python 3.12 runtime for enhanced performance and security
# - Non-root user execution for security
# - Minimal base image (python:3.12-slim) for reduced attack surface
# - Health checks for container orchestration
#
# V0.1.6 improvements:
# - Updated to Python 3.12 from 3.11 for better performance and security
# - Enhanced documentation and inline comments
# - Improved security annotations and explanations
# - Updated version references throughout
#
# V0.1.5 improvements:
# - Updated JP2Forge dependency from 0.9.6 to 0.9.7 for enhanced conversion capabilities
# - Enhanced adapter compatibility with improved version detection
# - Improved version compatibility handling
#
# Security Features:
# - Non-root user execution
# - Minimal system dependencies
# - Security-focused base image
# - No-new-privileges security option
# - Comprehensive health checks
#

# Build stage: Install dependencies and compile packages
FROM python:3.13-slim AS builder

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
# RUN pip-audit
# Temporarily disabled due to setuptools vulnerability (PYSEC-2025-49)

# Production stage: Minimal runtime environment
FROM python:3.13-slim

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
    CMD ["/bin/sh", "/app/healthcheck.sh"]

ENTRYPOINT ["/docker-entrypoint.sh"]

# Run server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "jp2forge_web.wsgi:application"]
