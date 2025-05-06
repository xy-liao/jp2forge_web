#!/bin/bash
set -e

# Function to check if Postgres is available
postgres_ready() {
    python << END
import sys
import psycopg2
import os
import time
import socket

# Give Postgres time to initialize on first run
time.sleep(3)

try:
    dbname = os.environ.get("POSTGRES_DB", "jp2forge")
    user = os.environ.get("POSTGRES_USER", "jp2forge")
    password = os.environ.get("POSTGRES_PASSWORD", "jp2forge_password")
    host = os.environ.get("DB_HOST", "db")
    port = os.environ.get("DB_PORT", "5432")
    
    # Check if host is reachable first
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, int(port)))
    if result != 0:
        sys.exit(-1)
    sock.close()
    
    # Now try to connect to Postgres
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
except Exception as e:
    print(f"Database connection error: {e}")
    sys.exit(-1)
sys.exit(0)
END
}

# Function to check if Redis is available
redis_ready() {
    python << END
import sys
import os
import socket
import time

# Give Redis time to initialize
time.sleep(2)

try:
    host = "redis"
    port = 6379
    
    # Check if Redis is reachable
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    if result != 0:
        sys.exit(-1)
    sock.close()
except Exception as e:
    print(f"Redis connection error: {e}")
    sys.exit(-1)
sys.exit(0)
END
}

# Security enhancements for Docker environment
echo "Setting up enhanced security for Docker environment..."
export SECURE_DOCKER_ENVIRONMENT=true

echo "Checking PostgreSQL connectivity..."
# Wait for PostgreSQL to become available (up to 60 seconds)
max_attempts=20
attempt=0
until postgres_ready || [ $attempt -ge $max_attempts ]; do
  attempt=$((attempt+1))
  >&2 echo "PostgreSQL is unavailable - attempt $attempt/$max_attempts - waiting 3s..."
  sleep 3
done

if [ $attempt -ge $max_attempts ]; then
  >&2 echo "PostgreSQL did not become ready in time. Continuing anyway..."
else
  >&2 echo "PostgreSQL is up - continuing..."
fi

echo "Checking Redis connectivity..."
# Wait for Redis to become available (up to 30 seconds)
max_attempts=10
attempt=0
until redis_ready || [ $attempt -ge $max_attempts ]; do
  attempt=$((attempt+1))
  >&2 echo "Redis is unavailable - attempt $attempt/$max_attempts - waiting 3s..."
  sleep 3
done

if [ $attempt -ge $max_attempts ]; then
  >&2 echo "Redis did not become ready in time. Continuing anyway..."
else
  >&2 echo "Redis is up - continuing..."
fi

# Create necessary directories if they don't exist
echo "Creating necessary directories..."
mkdir -p /app/media/jobs /app/media/reports /app/staticfiles /app/logs

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate || echo "Migration failed, but continuing..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Static file collection failed, but continuing..."

# Create superuser if requested
if [ "$CREATE_SUPERUSER" = "true" ]; then
  echo "Creating admin superuser..."
  python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
django.setup()
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Default superuser created successfully')
else:
    print('Superuser already exists')
" || echo "Superuser creation failed, but continuing..."
fi

echo "Entrypoint script completed, executing command: $@"
# Execute the command passed to docker run
exec "$@"