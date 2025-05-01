#!/usr/bin/env python
"""
Initialization script for JP2Forge Web Application.
This script performs initial setup tasks:
1. Checks dependencies
2. Creates database tables
3. Creates a superuser (if needed)
4. Sets up directory structure
"""

import os
import sys
import subprocess
import getpass
import django
from pathlib import Path

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jp2forge_web.settings')
BASE_DIR = Path(__file__).resolve().parent

def print_header(message):
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def check_dependencies():
    print_header("Checking Dependencies")
    
    # Check Python version
    python_version = sys.version.split()[0]
    print(f"Python version: {python_version}")
    
    # Check if ExifTool is installed
    exiftool_check = subprocess.run(
        ["which", "exiftool"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    if exiftool_check.returncode == 0:
        print("ExifTool: Installed")
    else:
        print("ExifTool: NOT FOUND")
        print("Please install ExifTool:")
        print("  - macOS: brew install exiftool")
        print("  - Ubuntu/Debian: sudo apt install libimage-exiftool-perl")
        print("  - Windows: Download from https://exiftool.org")
    
    # Check if Redis is running
    redis_check = subprocess.run(
        ["redis-cli", "ping"], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE,
        text=True
    )
    
    if redis_check.returncode == 0 and redis_check.stdout.strip() == "PONG":
        print("Redis: Running")
    else:
        print("Redis: NOT RUNNING")
        print("Please start Redis:")
        print("  - macOS: brew services start redis")
        print("  - Ubuntu/Debian: sudo service redis-server start")
        print("  - Windows: start Redis server")
    
    # Check if JP2Forge is installed - try multiple import strategies
    jp2forge_installed = False
    jp2forge_version = None
    
    # First, check standard package
    try:
        import jp2forge
        jp2forge_installed = True
        jp2forge_version = getattr(jp2forge, '__version__', 'unknown')
    except ImportError:
        # Package not installed in standard way, but might be available as modules
        try:
            # Try direct module import strategy (used by the adapter)
            from core.types import WorkflowConfig
            jp2forge_installed = True
            jp2forge_version = "module version"
        except ImportError:
            pass
    
    if jp2forge_installed:
        print(f"JP2Forge: Installed (version {jp2forge_version})")
    else:
        print("JP2Forge: NOT INSTALLED")
        print("Please install JP2Forge: pip install jp2forge")
    
    # Check Django
    print(f"Django: Installed (version {django.get_version()})")
    
    # Check Celery
    try:
        import celery
        print(f"Celery: Installed (version {celery.__version__})")
    except ImportError:
        print("Celery: NOT INSTALLED")
        print("Please install Celery: pip install celery")

def setup_database():
    print_header("Setting Up Database")
    
    # Run migrations
    try:
        django.setup()
        subprocess.run(
            [sys.executable, "manage.py", "makemigrations", "converter", "accounts"],
            check=True
        )
        subprocess.run(
            [sys.executable, "manage.py", "migrate"],
            check=True
        )
        print("Database setup completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up database: {e}")
        return False
    
    return True

def create_superuser():
    print_header("Creating Superuser")
    
    try:
        from django.contrib.auth.models import User
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("A superuser already exists. Skipping superuser creation.")
            return True
        
        # Get superuser credentials
        username = input("Enter superuser username: ")
        email = input("Enter superuser email: ")
        password = getpass.getpass("Enter superuser password: ")
        password_confirm = getpass.getpass("Confirm superuser password: ")
        
        if password != password_confirm:
            print("Error: Passwords do not match.")
            return False
        
        # Create superuser
        User.objects.create_superuser(username, email, password)
        print(f"Superuser '{username}' created successfully.")
        
    except Exception as e:
        print(f"Error creating superuser: {e}")
        return False
    
    return True

def setup_directories():
    print_header("Setting Up Directory Structure")
    
    # Create media directories
    media_dir = os.path.join(BASE_DIR, "media")
    jobs_dir = os.path.join(media_dir, "jobs")
    
    os.makedirs(media_dir, exist_ok=True)
    os.makedirs(jobs_dir, exist_ok=True)
    
    print(f"Created media directory: {media_dir}")
    print(f"Created jobs directory: {jobs_dir}")
    
    # Create static directories
    static_dir = os.path.join(BASE_DIR, "static")
    static_js_dir = os.path.join(static_dir, "js")
    static_css_dir = os.path.join(static_dir, "css")
    
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(static_js_dir, exist_ok=True)
    os.makedirs(static_css_dir, exist_ok=True)
    
    print(f"Created static directory: {static_dir}")
    
    # Collect static files
    try:
        subprocess.run(
            [sys.executable, "manage.py", "collectstatic", "--noinput"],
            check=True
        )
        print("Static files collected successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error collecting static files: {e}")
    
    return True

def main():
    print_header("JP2Forge Web Application Initialization")
    
    check_dependencies()
    
    # Set up database
    if not setup_database():
        print("Database setup failed. Exiting.")
        return
    
    # Create superuser
    if not create_superuser():
        print("Superuser creation failed. Exiting.")
        return
    
    # Set up directories
    if not setup_directories():
        print("Directory setup failed. Exiting.")
        return
    
    print_header("Initialization Complete")
    print("\nYou can now start the application:")
    print("1. Start the Django development server:")
    print("   python manage.py runserver")
    print("\n2. Start the Celery worker (in a separate terminal):")
    print("   celery -A jp2forge_web worker -l INFO")
    print("\n3. Access the application at http://localhost:8000")

if __name__ == "__main__":
    main()
