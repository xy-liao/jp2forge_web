"""
Version information context processor for JP2Forge Web.

This module provides a context processor that adds version information 
for key dependencies to all templates, making it available in the UI.
"""

import django
import platform
import sys
import importlib.metadata
from django.conf import settings


def get_version_info():
    """
    Collect version information for key dependencies.
    
    Returns:
        dict: Dictionary containing version information for various components.
    """
    versions = {
        'django': django.get_version(),
        'python': platform.python_version(),
        'system': f"{platform.system()} {platform.release()}",
        'jp2forge_web': getattr(settings, 'VERSION', '0.1.5'),  # Get version from settings
    }
    
    # Try to get versions of other key dependencies
    dependencies = [
        'celery',
        'redis',
        'pillow',
        'jp2forge',
        'gunicorn',
        'markdown',
    ]
    
    for package in dependencies:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'not installed'
    
    # Special handling for psycopg2 - check both psycopg2 and psycopg2-binary
    try:
        versions['psycopg2'] = importlib.metadata.version('psycopg2')
    except importlib.metadata.PackageNotFoundError:
        try:
            versions['psycopg2'] = importlib.metadata.version('psycopg2-binary')
        except importlib.metadata.PackageNotFoundError:
            versions['psycopg2'] = 'not installed'
    
    return versions


def versions(request):
    """
    Context processor that adds version information to template context.
    
    Args:
        request: The HTTP request object.
        
    Returns:
        dict: Dictionary containing version information.
    """
    return {
        'versions': get_version_info(),
    }