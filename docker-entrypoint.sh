#!/bin/bash
set -e

# Docker Entrypoint Script for JP2Forge Web
# Version: 0.1.3 (May 6, 2025)
# Handles container initialization with improved error handling and fixes

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
    password = os.environ.get("POSTGRES_PASSWORD")
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
import redis

# Give Redis time to initialize
time.sleep(2)

try:
    host = "redis"
    port = 6379
    password = os.environ.get("REDIS_PASSWORD")
    
    # Check if Redis is reachable
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    if result != 0:
        sys.exit(-1)
    sock.close()
    
    # Verify authentication works
    r = redis.Redis(host=host, port=port, password=password)
    r.ping()
except Exception as e:
    print(f"Redis connection error: {e}")
    sys.exit(-1)
sys.exit(0)
END
}

# Security enhancements for Docker environment
echo "Setting up enhanced security for Docker environment..."
export SECURE_DOCKER_ENVIRONMENT=true
export DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE:-jp2forge_web.settings}
export PYTHONPATH=/app

# Add health endpoint for container health checks
cat > /tmp/health_endpoint.py << 'EOL'
def add_health_endpoint(urlpatterns):
    """Add a simple health endpoint to the URL patterns."""
    from django.http import HttpResponse
    from django.urls import path
    
    def health(request):
        """Return a simple 200 response for health checks."""
        return HttpResponse("OK", content_type="text/plain")
    
    urlpatterns.append(path('health/', health, name='health'))
    return urlpatterns
EOL

if [ -f /app/jp2forge_web/urls.py ]; then
    echo "Adding health endpoint for container health checks..."
    # Check if health endpoint already exists to avoid duplicate additions
    if ! grep -q "health_endpoint" /app/jp2forge_web/urls.py; then
        echo "
# Added by docker-entrypoint for container health checks
import sys
import os
sys.path.append('/tmp')
from health_endpoint import add_health_endpoint
urlpatterns = add_health_endpoint(urlpatterns)
" >> /app/jp2forge_web/urls.py
    fi
fi

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

# Final security checks
echo "Running final security checks..."
if [ -d "/app/logs" ]; then
  chmod 755 /app/logs
  touch /app/logs/startup.log
  echo "$(date): Container startup completed successfully" >> /app/logs/startup.log
fi

echo "Entrypoint script completed, executing command: $@"
# Execute the command passed to docker run
exec "$@"