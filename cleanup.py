#!/usr/bin/env python
"""
JP2Forge Web Cleanup Script

This script cleans up the JP2Forge Web application by:
1. Clearing conversion job records from the database
2. Removing job media files
3. Clearing log files
4. Removing temporary files and caches
5. Resetting Celery tasks
6. Cleaning SQLite journal files
7. Managing static file collections
8. Handling Django sessions

Usage:
    python cleanup.py [options]

Options:
    --all               Clean everything (jobs, logs, media, temp files, celery tasks, sqlite, static)
    --jobs              Clean only job records and their media files
    --logs              Clean only log files
    --temp              Clean only temporary files and caches
    --celery            Reset only Celery tasks
    --sqlite            Clean SQLite journal files and optimize database
    --static            Remove collected static files (will require running collectstatic again)
    --sessions          Clean Django session files
    --keep-users        Keep user accounts when cleaning jobs (default: True)
    --dry-run           Show what would be deleted without actually deleting anything
"""

import os
import sys
import glob
import shutil
import argparse
import sqlite3
import logging
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('jp2forge-cleanup')

# Find project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Set up paths
DATABASE_PATH = os.path.join(PROJECT_ROOT, 'db.sqlite3')
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')
JOBS_DIR = os.path.join(MEDIA_ROOT, 'jobs')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'staticfiles')
SESSION_DIR = os.path.join(PROJECT_ROOT, 'tmp', 'sessions')
TEMP_DIRS = [
    os.path.join(PROJECT_ROOT, '__pycache__'),
    os.path.join(PROJECT_ROOT, '.pytest_cache'),
]

def clean_database(keep_users=True, dry_run=False):
    """Clean database tables related to conversion jobs"""
    logger.info("Cleaning database records...")
    
    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"Database file not found: {DATABASE_PATH}")
        return
    
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        tables = [table[0] for table in tables]
        
        # Tables related to conversion jobs
        job_tables = [
            'converter_conversionjob',  # Main job table
        ]
        
        # Filter existing tables
        job_tables = [table for table in job_tables if table in tables]
        
        if dry_run:
            for table in job_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                logger.info(f"Would delete {count} records from {table}")
        else:
            for table in job_tables:
                cursor.execute(f"DELETE FROM {table}")
                logger.info(f"Deleted all records from {table}")
            
            # Commit changes
            conn.commit()
        
        conn.close()
        logger.info("Database cleaning completed.")
        
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
    except Exception as e:
        logger.error(f"Error cleaning database: {e}")

def clean_media_files(dry_run=False):
    """Remove all job media files"""
    logger.info("Cleaning media files...")
    
    if not os.path.exists(JOBS_DIR):
        logger.warning(f"Jobs directory not found: {JOBS_DIR}")
        return
    
    job_dirs = os.listdir(JOBS_DIR)
    logger.info(f"Found {len(job_dirs)} job directories")
    
    if dry_run:
        logger.info(f"Would delete {len(job_dirs)} job directories from {JOBS_DIR}")
    else:
        for job_dir in job_dirs:
            job_path = os.path.join(JOBS_DIR, job_dir)
            if os.path.isdir(job_path):
                try:
                    shutil.rmtree(job_path)
                except Exception as e:
                    logger.error(f"Error removing job directory {job_path}: {e}")
        
        logger.info(f"Removed {len(job_dirs)} job directories")

def clean_log_files(dry_run=False):
    """Clear log files but don't delete them"""
    logger.info("Cleaning log files...")
    
    if not os.path.exists(LOGS_DIR):
        logger.warning(f"Logs directory not found: {LOGS_DIR}")
        return
    
    log_files = glob.glob(os.path.join(LOGS_DIR, "*.log"))
    logger.info(f"Found {len(log_files)} log files")
    
    if dry_run:
        for log_file in log_files:
            logger.info(f"Would clear log file: {os.path.basename(log_file)}")
    else:
        for log_file in log_files:
            try:
                # Create a backup of the log with timestamp
                backup_name = f"{log_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                shutil.copy2(log_file, backup_name)
                
                # Clear the log file
                with open(log_file, 'w') as f:
                    f.write(f"# Log cleared by cleanup script at {datetime.now().isoformat()}\n")
                
                logger.info(f"Cleared log file: {os.path.basename(log_file)}")
            except Exception as e:
                logger.error(f"Error clearing log file {log_file}: {e}")

def clean_temp_files(dry_run=False):
    """Remove temporary files and caches"""
    logger.info("Cleaning temporary files and caches...")
    
    # Find all __pycache__ directories recursively
    pycache_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for dir in dirs:
            if dir == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir))
    
    # Add any other temporary directories
    temp_dirs = pycache_dirs + TEMP_DIRS
    
    if dry_run:
        for dir_path in temp_dirs:
            if os.path.exists(dir_path):
                logger.info(f"Would remove directory: {dir_path}")
    else:
        for dir_path in temp_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed directory: {dir_path}")
                except Exception as e:
                    logger.error(f"Error removing directory {dir_path}: {e}")
    
    # Find and remove .pyc files
    pyc_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    if dry_run:
        logger.info(f"Would remove {len(pyc_files)} .pyc files")
    else:
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
            except Exception as e:
                logger.error(f"Error removing file {pyc_file}: {e}")
        
        logger.info(f"Removed {len(pyc_files)} .pyc files")

def reset_celery_tasks(dry_run=False):
    """Reset Celery tasks"""
    logger.info("Resetting Celery tasks...")
    
    if dry_run:
        logger.info("Would restart Celery workers")
    else:
        try:
            # First try to gracefully stop Celery
            logger.info("Attempting to stop Celery workers gracefully...")
            subprocess.run(["pkill", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Small delay to allow Celery to stop
            import time
            time.sleep(2)
            
            # Check if Celery is still running
            result = subprocess.run(["pgrep", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                # Force kill if still running
                logger.info("Force stopping Celery workers...")
                subprocess.run(["pkill", "-9", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info("Celery workers stopped.")
            
            # Optionally restart Celery using the project's start script
            if os.path.exists('./start_celery.sh'):
                logger.info("Restarting Celery workers...")
                subprocess.Popen(["./start_celery.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                logger.info("Celery workers restarted.")
            else:
                logger.warning("Celery start script not found. You may need to restart Celery manually.")
        
        except Exception as e:
            logger.error(f"Error resetting Celery tasks: {e}")

def clean_sqlite_files(dry_run=False):
    """Clean SQLite journal files and optimize database"""
    logger.info("Cleaning SQLite database files...")
    
    # Look for SQLite journal, WAL and SHM files
    sqlite_temp_files = glob.glob(os.path.join(PROJECT_ROOT, "*.sqlite3-*"))
    
    if sqlite_temp_files:
        logger.info(f"Found {len(sqlite_temp_files)} SQLite temporary files")
        
        if dry_run:
            for file_path in sqlite_temp_files:
                logger.info(f"Would remove SQLite temporary file: {os.path.basename(file_path)}")
        else:
            for file_path in sqlite_temp_files:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed SQLite temporary file: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.error(f"Error removing SQLite temporary file {file_path}: {e}")
    else:
        logger.info("No SQLite temporary files found")
    
    # Optimize the SQLite database if it exists
    if os.path.exists(DATABASE_PATH) and not dry_run:
        try:
            logger.info("Optimizing SQLite database...")
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute("VACUUM;")
            cursor.execute("PRAGMA optimize;")
            conn.commit()
            conn.close()
            logger.info("SQLite database optimized")
        except Exception as e:
            logger.error(f"Error optimizing SQLite database: {e}")

def clean_static_files(dry_run=False):
    """Remove collected static files"""
    logger.info("Cleaning collected static files...")
    
    if not os.path.exists(STATIC_ROOT):
        logger.warning(f"Static files directory not found: {STATIC_ROOT}")
        return
    
    if dry_run:
        logger.info(f"Would remove all files in static files directory: {STATIC_ROOT}")
    else:
        try:
            # Keep the directory but remove all contents
            for item in os.listdir(STATIC_ROOT):
                item_path = os.path.join(STATIC_ROOT, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            
            # Create a placeholder file so git doesn't remove the directory
            with open(os.path.join(STATIC_ROOT, '.gitkeep'), 'w') as f:
                f.write('# This directory is used for collected static files\n')
            
            logger.info("Removed all collected static files")
            logger.info("Remember to run 'python manage.py collectstatic' before serving the application")
        except Exception as e:
            logger.error(f"Error removing static files: {e}")

def clean_session_files(dry_run=False):
    """Clean Django session files"""
    logger.info("Cleaning Django session files...")
    
    if not os.path.exists(SESSION_DIR):
        logger.info(f"Session directory not found: {SESSION_DIR}")
        return
    
    session_files = glob.glob(os.path.join(SESSION_DIR, "session*"))
    
    if session_files:
        logger.info(f"Found {len(session_files)} session files")
        
        if dry_run:
            logger.info(f"Would remove {len(session_files)} Django session files")
        else:
            try:
                for file_path in session_files:
                    os.remove(file_path)
                logger.info(f"Removed {len(session_files)} Django session files")
            except Exception as e:
                logger.error(f"Error removing session files: {e}")
    else:
        logger.info("No Django session files found")

def main():
    """Main function to coordinate cleanup tasks"""
    parser = argparse.ArgumentParser(description='Clean up JP2Forge Web application data')
    parser.add_argument('--all', action='store_true', help='Clean everything')
    parser.add_argument('--jobs', action='store_true', help='Clean only job records')
    parser.add_argument('--logs', action='store_true', help='Clean only log files')
    parser.add_argument('--temp', action='store_true', help='Clean only temporary files')
    parser.add_argument('--celery', action='store_true', help='Reset only Celery tasks')
    parser.add_argument('--sqlite', action='store_true', help='Clean SQLite journal files')
    parser.add_argument('--static', action='store_true', help='Remove collected static files')
    parser.add_argument('--sessions', action='store_true', help='Clean Django session files')
    parser.add_argument('--keep-users', action='store_true', help='Keep user accounts when cleaning jobs')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without actually cleaning')
    
    args = parser.parse_args()
    
    # If no specific tasks are selected, treat as --all
    if not (args.all or args.jobs or args.logs or args.temp or args.celery or args.sqlite or args.static or args.sessions):
        args.all = True
    
    logger.info("Starting JP2Forge Web cleanup...")
    
    if args.dry_run:
        logger.info("DRY RUN MODE: No files will actually be deleted")
    
    try:
        if args.all or args.jobs:
            clean_database(keep_users=args.keep_users, dry_run=args.dry_run)
            clean_media_files(dry_run=args.dry_run)
        
        if args.all or args.logs:
            clean_log_files(dry_run=args.dry_run)
        
        if args.all or args.temp:
            clean_temp_files(dry_run=args.dry_run)
        
        if args.all or args.celery:
            reset_celery_tasks(dry_run=args.dry_run)
            
        if args.all or args.sqlite:
            clean_sqlite_files(dry_run=args.dry_run)
            
        if args.all or args.static:
            clean_static_files(dry_run=args.dry_run)
            
        if args.all or args.sessions:
            clean_session_files(dry_run=args.dry_run)
        
        logger.info("JP2Forge Web cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"Cleanup failed with error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())