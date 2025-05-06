"""
Version information context processor for JP2Forge Web.

This module provides a context processor that adds version information 
for key dependencies to all templates, making it available in the UI.
"""

import django
import platform
import sys
import importlib.metadata


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
        'jp2forge_web': '0.2.0',  # Application version
    }
    
    # Try to get versions of other key dependencies
    dependencies = [
        'celery',
        'redis',
        'pillow',
        'jp2forge',
        'psycopg2',
        'gunicorn',
        'markdown',
    ]
    
    for package in dependencies:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = 'not installed'
    
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