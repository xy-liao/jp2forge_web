import os
import socket
from celery import Celery

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')

# Create a unique worker name using hostname and process ID
hostname = socket.gethostname()
worker_name = f'jp2forge_web@{hostname}-{os.getpid()}'

app = Celery('jp2forge_web')

# Use CELERY_ prefix for all celery configurations in settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Add explicit configuration to address deprecation warnings
app.conf.broker_connection_retry_on_startup = True

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()
