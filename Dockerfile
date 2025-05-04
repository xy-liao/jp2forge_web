FROM python:3.9

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libimage-exiftool-perl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
# Install JP2Forge from GitHub
RUN pip install --no-cache-dir git+https://github.com/xy-liao/jp2forge.git@v0.9.6

# Copy project files
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run gunicorn
CMD ["gunicorn", "jp2forge_web.wsgi:application", "--bind", "0.0.0.0:8000"]
