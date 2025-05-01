#!/usr/bin/env python
"""
JP2Forge Web Cleanup Script

This script cleans up the JP2Forge Web application by:
1. Clearing conversion job records from the database
2. Removing job media files
3. Managing log files (clearing or removing)
4. Removing temporary files and caches
5. Resetting Celery tasks
6. Cleaning SQLite journal files and database backups
7. Managing static file collections
8. Handling Django sessions
9. Reinitializing the entire project

Usage:
    python cleanup.py [options]

Options:
    --all                   Clean everything using standard (safe) options
    --complete              Complete cleanup (removes all logs, database backups, preserves only essential files)
    --jobs                  Clean only job records and their media files
    --logs                  Clear log file contents (preserves files, but empties them)
    --remove-all-logs       Remove all log files completely (instead of just clearing them)
    --temp                  Clean only temporary files and caches
    --celery                Reset only Celery tasks
    --sqlite                Clean SQLite journal files and optimize database
    --sqlite-backups        Remove SQLite database backup files
    --static                Remove collected static files (will require running collectstatic again)
    --sessions              Clean Django session files
    --keep-users            Keep user accounts when cleaning jobs (default: True)
    --no-keep-users         Remove user accounts when cleaning (overrides --keep-users)
    --reinit                Full project reinitialization (recreates database, removes all data including users)
    --dry-run               Show what would be deleted without actually deleting anything
    --no-backup             Skip creating backups before clearing files
"""

import os
import sys
import glob
import shutil
import argparse
import sqlite3
import logging
import subprocess
import traceback
import time
from datetime import datetime
from functools import wraps

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

# Define essential directories that should be kept with .gitkeep files
ESSENTIAL_DIRS = [
    LOGS_DIR,
    JOBS_DIR,
    STATIC_ROOT
]

# Multiple potential session directories
SESSION_DIRS = [
    os.path.join(PROJECT_ROOT, 'tmp', 'sessions'),
    os.path.join('/tmp', 'django_sessions'),
    os.path.join(PROJECT_ROOT, '.sessions'),
]

# Temporary directories to clean
TEMP_DIRS = [
    os.path.join(PROJECT_ROOT, '__pycache__'),
    os.path.join(PROJECT_ROOT, '.pytest_cache'),
]

# Decorator for error handling
def handle_errors(task_name):
    """Decorator to standardize error handling for cleanup tasks"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                logger.debug(f"Starting {task_name} task")
                result = func(*args, **kwargs)
                logger.debug(f"Completed {task_name} task")
                return result
            except Exception as e:
                logger.error(f"Error in {task_name}: {e}")
                logger.debug(traceback.format_exc())
                return None
        return wrapper
    return decorator

# Utility functions
def ensure_dir_exists(path):
    """Ensure a directory exists, creating it if needed"""
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            logger.info(f"Created directory: {path}")
        except Exception as e:
            logger.error(f"Error creating directory {path}: {e}")
    return os.path.exists(path)

def create_gitkeep(directory):
    """Create a .gitkeep file in a directory to keep it in git"""
    if not os.path.exists(directory):
        return
    
    gitkeep_path = os.path.join(directory, '.gitkeep')
    try:
        with open(gitkeep_path, 'w') as f:
            f.write(f'# This directory is maintained by JP2Forge Web\n')
            f.write(f'# Created by cleanup.py at {datetime.now().isoformat()}\n')
        logger.debug(f"Created .gitkeep file in {directory}")
    except Exception as e:
        logger.error(f"Error creating .gitkeep file in {directory}: {e}")

def process_files(directory, file_pattern, operation_func, dry_run=False, description="files"):
    """Generic function to process files matching a pattern
    
    Args:
        directory: Directory to search in
        file_pattern: Glob pattern to match files
        operation_func: Function to call on each file if not dry run
        dry_run: Whether to actually perform operations
        description: Description of the files for logging
    
    Returns:
        count of processed files
    """
    if not os.path.exists(directory):
        logger.info(f"Directory not found: {directory}")
        return 0
        
    matching_files = glob.glob(os.path.join(directory, file_pattern))
    count = len(matching_files)
    
    if count == 0:
        logger.info(f"No {description} found in {directory}")
        return 0
        
    logger.info(f"Found {count} {description} in {directory}")
    
    if dry_run:
        for file_path in matching_files:
            logger.info(f"Would process: {os.path.basename(file_path)}")
    else:
        success_count = 0
        error_count = 0
        
        for file_path in matching_files:
            try:
                operation_func(file_path)
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {os.path.basename(file_path)}: {e}")
                
        logger.info(f"Successfully processed {success_count} {description}, errors on {error_count}")
    
    return count

def clean_directory(directory, exclude_pattern=None, dry_run=False, preserve_git=True):
    """Generic function to clean a directory
    
    Args:
        directory: Directory to clean
        exclude_pattern: Pattern of files/dirs to exclude
        dry_run: Whether to actually perform deletions
        preserve_git: Whether to keep .git* files
    """
    if not os.path.exists(directory):
        logger.info(f"Directory not found: {directory}")
        if not dry_run:
            ensure_dir_exists(directory)
        return
    
    items = os.listdir(directory)
    if exclude_pattern:
        items = [item for item in items if not glob.fnmatch.fnmatch(item, exclude_pattern)]
    if preserve_git:
        items = [item for item in items if not item.startswith('.git')]
    
    total_count = len(items)
    
    if dry_run:
        logger.info(f"Would remove {total_count} items from {directory}")
        for item in items:
            logger.info(f"Would remove: {item}")
    else:
        for item in items:
            item_path = os.path.join(directory, item)
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
            except Exception as e:
                logger.error(f"Error removing {item}: {e}")
        
        create_gitkeep(directory)
        logger.info(f"Removed {total_count} items from {directory}")

# Cleanup functions
@handle_errors("clean_database")
def clean_database(keep_users=True, dry_run=False):
    """Clean database tables related to conversion jobs"""
    logger.info("Cleaning database records...")
    
    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"Database file not found: {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Get list of tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    tables = [table[0] for table in tables]
    
    # Tables related to conversion jobs
    job_tables = [
        'converter_conversionjob',  # Main job table
        'django_celery_results_taskresult'  # Celery task results
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
    
    # Handle user accounts if requested
    if not keep_users and 'auth_user' in tables:
        if dry_run:
            cursor.execute(f"SELECT COUNT(*) FROM auth_user")
            count = cursor.fetchone()[0]
            logger.info(f"Would delete {count} user accounts")
        else:
            cursor.execute(f"DELETE FROM auth_user")
            conn.commit()
            logger.info(f"Deleted all user accounts")
    
    conn.close()
    logger.info("Database cleaning completed.")

@handle_errors("clean_media_files")
def clean_media_files(dry_run=False):
    """Remove all job media files"""
    logger.info("Cleaning media files...")
    clean_directory(JOBS_DIR, exclude_pattern=".*", dry_run=dry_run)

@handle_errors("clean_log_files")
def clean_log_files(dry_run=False, keep_latest_backup=True, create_backup=True):
    """Clear log files and manage backup files"""
    logger.info("Cleaning log files...")
    
    if not os.path.exists(LOGS_DIR):
        logger.info(f"Logs directory not found: {LOGS_DIR}")
        if not dry_run:
            ensure_dir_exists(LOGS_DIR)
        return
    
    # Handle active log files
    log_files = glob.glob(os.path.join(LOGS_DIR, "*.log"))
    logger.info(f"Found {len(log_files)} active log files")
    
    if not dry_run:
        for log_file in log_files:
            try:
                # Create a backup if requested
                if create_backup and os.path.getsize(log_file) > 0:
                    backup_name = f"{log_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                    shutil.copy2(log_file, backup_name)
                
                # Clear the log file
                with open(log_file, 'w') as f:
                    f.write(f"# Log cleared by cleanup script at {datetime.now().isoformat()}\n")
                
                logger.info(f"Cleared log file: {os.path.basename(log_file)}")
            except Exception as e:
                logger.error(f"Error clearing log file {log_file}: {e}")
    else:
        for log_file in log_files:
            logger.info(f"Would clear log file: {os.path.basename(log_file)}")
    
    # Handle backup files
    backup_files = glob.glob(os.path.join(LOGS_DIR, "*.log.*.bak"))
    logger.info(f"Found {len(backup_files)} log backup files")
    
    if keep_latest_backup and len(backup_files) > 0 and not dry_run:
        # Group backup files by their base log file name
        backup_groups = {}
        for backup in backup_files:
            base_name = os.path.basename(backup).split('.', 1)[0] + '.log'
            if base_name not in backup_groups:
                backup_groups[base_name] = []
            backup_groups[base_name].append(backup)
        
        # For each group, sort by timestamp and keep only the latest one
        files_to_delete = []
        for base_name, group in backup_groups.items():
            if len(group) <= 1:
                continue  # Nothing to clean if there's only one backup
            
            # Sort backups by timestamp (newest first)
            sorted_backups = sorted(group, reverse=True)
            # Keep the newest, delete the rest
            files_to_delete.extend(sorted_backups[1:])
        
        if dry_run:
            logger.info(f"Would delete {len(files_to_delete)} older backup files, keeping the latest backup for each log")
            for file_path in files_to_delete:
                logger.info(f"Would delete: {os.path.basename(file_path)}")
        else:
            for file_path in files_to_delete:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted old backup: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.error(f"Error deleting backup file {file_path}: {e}")
    elif not keep_latest_backup and not dry_run:
        # Delete all backup files
        for file_path in backup_files:
            try:
                os.remove(file_path)
                logger.info(f"Deleted backup file: {os.path.basename(file_path)}")
            except Exception as e:
                logger.error(f"Error deleting backup file {file_path}: {e}")
    elif dry_run:
        if not keep_latest_backup:
            logger.info(f"Would delete all {len(backup_files)} backup files")
        else:
            logger.info(f"Would keep the latest backup for each log file")
    
    logger.info("Log cleaning completed")

@handle_errors("remove_all_logs")
def remove_all_logs(dry_run=False):
    """Remove all log files completely, including both active logs and backups"""
    logger.info("Removing all log files...")
    
    # Use a simplified pattern-based approach to find all log files
    log_patterns = [
        "*.log",             # Regular log files
        "*.log.*",           # All log files with extensions
        "*_*.log",           # Named log files
        "*_*.log.*"          # Named log files with extensions
    ]
    
    log_count = 0
    for pattern in log_patterns:
        # Use process_files for each pattern with a file removal operation
        log_count += process_files(
            LOGS_DIR, 
            pattern, 
            os.remove, 
            dry_run=dry_run, 
            description=f"log files matching '{pattern}'"
        )
    
    # Create placeholder .gitkeep file
    if not dry_run:
        create_gitkeep(LOGS_DIR)
    
    if log_count == 0:
        logger.info("No log files found to remove")
    else:
        logger.info(f"Found {log_count} total log files to process")
    
    logger.info("Log removal completed")

@handle_errors("clean_temp_files")
def clean_temp_files(dry_run=False):
    """Remove temporary files and caches"""
    logger.info("Cleaning temporary files and caches...")
    
    # Find all __pycache__ directories recursively
    pycache_dirs = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for dir in dirs:
            if dir == '__pycache__':
                pycache_dirs.append(os.path.join(root, dir))
    
    # Add additional temporary directories to clean
    temp_dirs = pycache_dirs + TEMP_DIRS
    
    # Clean each temp directory
    removed_dirs = 0
    if dry_run:
        for dir_path in temp_dirs:
            if os.path.exists(dir_path):
                logger.info(f"Would remove directory: {dir_path}")
                removed_dirs += 1
    else:
        for dir_path in temp_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    logger.info(f"Removed directory: {dir_path}")
                    removed_dirs += 1
                except Exception as e:
                    logger.error(f"Error removing directory {dir_path}: {e}")
    
    # Find and remove .pyc files
    pyc_files = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if file.endswith('.pyc'):
                pyc_files.append(os.path.join(root, file))
    
    removed_pyc = 0
    if dry_run:
        logger.info(f"Would remove {len(pyc_files)} .pyc files")
    else:
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
                removed_pyc += 1
            except Exception as e:
                logger.error(f"Error removing file {pyc_file}: {e}")
        
        logger.info(f"Removed {removed_pyc} .pyc files")
    
    logger.info(f"Cleaned {removed_dirs} temporary directories")

@handle_errors("reset_celery_tasks")
def reset_celery_tasks(dry_run=False):
    """Reset Celery tasks"""
    logger.info("Resetting Celery tasks...")
    
    if dry_run:
        logger.info("Would restart Celery workers")
        return
    
    # Check if we're running in VS Code's integrated terminal
    in_vscode = os.environ.get('TERM_PROGRAM') == 'vscode' or 'VSCODE_PID' in os.environ
    if in_vscode:
        logger.info("Detected VS Code integrated terminal - using safer Celery restart method")
        logger.info("Skipping Celery process operations in VS Code integrated terminal")
        logger.info("Please restart Celery manually if needed")
        return
        
    # First try to gracefully stop Celery
    logger.info("Attempting to stop Celery workers gracefully...")
    subprocess.run(["pkill", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Small delay to allow Celery to stop
    time.sleep(2)
    
    # Check if Celery is still running
    result = subprocess.run(["pgrep", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode == 0:
        # Force kill if still running
        logger.info("Force stopping Celery workers...")
        subprocess.run(["pkill", "-9", "-f", "celery"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Celery workers stopped forcefully.")
    else:
        logger.info("Celery workers stopped gracefully.")
    
    # Optionally restart Celery using the project's start script
    if os.path.exists('./start_celery.sh'):
        logger.info("Restarting Celery workers...")
        subprocess.Popen(["./start_celery.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info("Celery workers restarted.")
    else:
        logger.warning("Celery start script not found. You may need to restart Celery manually.")
        
    logger.info("Please restart Celery manually if needed")

@handle_errors("clean_sqlite_files")
def clean_sqlite_files(dry_run=False, clean_backups=False):
    """Clean SQLite journal files and optionally database backups"""
    logger.info("Cleaning SQLite database files...")
    
    # Clean temporary SQLite files
    sqlite_temp_files = glob.glob(os.path.join(PROJECT_ROOT, "*.sqlite3-*"))
    
    if sqlite_temp_files:
        if dry_run:
            logger.info(f"Would remove {len(sqlite_temp_files)} SQLite temporary files")
            for file_path in sqlite_temp_files:
                logger.info(f"Would remove: {os.path.basename(file_path)}")
        else:
            removed = 0
            for file_path in sqlite_temp_files:
                try:
                    os.remove(file_path)
                    logger.info(f"Removed SQLite temporary file: {os.path.basename(file_path)}")
                    removed += 1
                except Exception as e:
                    logger.error(f"Error removing SQLite temporary file {file_path}: {e}")
            logger.info(f"Removed {removed} SQLite temporary files")
    else:
        logger.info("No SQLite temporary files found")
    
    # Handle database backup files if requested
    if clean_backups:
        backup_files = glob.glob(os.path.join(PROJECT_ROOT, "*.sqlite3.*.bak"))
        if backup_files:
            if dry_run:
                logger.info(f"Would remove {len(backup_files)} SQLite database backups")
                for file_path in backup_files:
                    logger.info(f"Would remove: {os.path.basename(file_path)}")
            else:
                removed = 0
                for file_path in backup_files:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed SQLite backup file: {os.path.basename(file_path)}")
                        removed += 1
                    except Exception as e:
                        logger.error(f"Error removing SQLite backup file {file_path}: {e}")
                logger.info(f"Removed {removed} SQLite database backups")
        else:
            logger.info("No SQLite database backups found")
    
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

@handle_errors("clean_static_files")
def clean_static_files(dry_run=False):
    """Remove collected static files"""
    logger.info("Cleaning collected static files...")
    
    if not os.path.exists(STATIC_ROOT):
        logger.info(f"Static files directory not found: {STATIC_ROOT}")
        if not dry_run:
            ensure_dir_exists(STATIC_ROOT)
        return
    
    # Count static files for reporting
    static_file_count = 0
    for root, dirs, files in os.walk(STATIC_ROOT):
        static_file_count += len(files)
    
    # Use the clean_directory function
    clean_directory(STATIC_ROOT, exclude_pattern=".*", dry_run=dry_run)
    
    if not dry_run:
        logger.info("Remember to run 'python manage.py collectstatic' before serving the application")

@handle_errors("clean_session_files")
def clean_session_files(dry_run=False):
    """Clean Django session files"""
    logger.info("Cleaning Django session files...")
    
    session_dir_found = False
    
    for session_dir in SESSION_DIRS:
        if os.path.exists(session_dir):
            session_dir_found = True
            process_files(
                session_dir, 
                "session*", 
                os.remove, 
                dry_run=dry_run, 
                description="session files"
            )
            if not dry_run:
                create_gitkeep(session_dir)
    
    if not session_dir_found:
        logger.info("No Django session directories found - skipping session cleanup")

@handle_errors("recreate_database")
def recreate_database(dry_run=False, create_backup=True):
    """Completely recreate the database from scratch"""
    logger.info("Recreating database...")
    
    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"Database file not found: {DATABASE_PATH}")
        return
    
    if dry_run:
        logger.info(f"Would delete and recreate database file: {DATABASE_PATH}")
        return
    
    # Backup the current database if requested
    if create_backup:
        backup_name = f"{DATABASE_PATH}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        shutil.copy2(DATABASE_PATH, backup_name)
        logger.info(f"Created database backup: {os.path.basename(backup_name)}")
    
    # Remove the database file
    os.remove(DATABASE_PATH)
    logger.info("Removed existing database file")
    
    # Run Django migrations to recreate the database
    logger.info("Running Django migrations to recreate database...")
    result = subprocess.run(
        ["python", "manage.py", "migrate"],
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        text=True
    )
    
    if result.returncode == 0:
        logger.info("Successfully recreated database with migrations")
    else:
        logger.error(f"Error running migrations: {result.stderr}")
        # Restore the backup if migration fails and backup exists
        if create_backup and os.path.exists(backup_name):
            shutil.copy2(backup_name, DATABASE_PATH)
            logger.info(f"Restored database from backup due to migration error")

def perform_comprehensive_cleanup(dry_run=False, create_backup=True, keep_users=True, 
                                remove_backups=False, include_celery=False, include_sessions=False):
    """Shared cleanup function used by both reinitialize and complete_cleanup
    
    Args:
        dry_run: Whether to perform actual operations
        create_backup: Whether to backup the database first
        keep_users: Whether to keep user accounts
        remove_backups: Whether to remove database backups
        include_celery: Whether to include Celery operations
        include_sessions: Whether to clean sessions
    """
    # First stop Celery workers if requested
    if include_celery:
        reset_celery_tasks(dry_run=dry_run)
    
    # Backup the database if requested
    if create_backup and os.path.exists(DATABASE_PATH):
        backup_name = f"{DATABASE_PATH}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        if not dry_run:
            shutil.copy2(DATABASE_PATH, backup_name)
            logger.info(f"Created database backup: {os.path.basename(backup_name)}")
        else:
            logger.info(f"Would create database backup: {os.path.basename(backup_name)}")
    
    # Clean all components in a structured manner
    clean_media_files(dry_run=dry_run)
    remove_all_logs(dry_run=dry_run)
    clean_temp_files(dry_run=dry_run)
    clean_sqlite_files(dry_run=dry_run, clean_backups=remove_backups)
    clean_static_files(dry_run=dry_run)
    
    if include_sessions:
        clean_session_files(dry_run=dry_run)
    
    # Clean database with user preference
    clean_database(keep_users=keep_users, dry_run=dry_run)
    
    # Create .gitkeep files in key directories
    if not dry_run:
        for directory in ESSENTIAL_DIRS:
            create_gitkeep(directory)

@handle_errors("reinitialize_project")
def reinitialize_project(dry_run=False, create_backup=True):
    """Perform a full project reinitialization"""
    logger.info("Reinitializing the entire project...")
    
    if dry_run:
        logger.info("Would perform the following reinitialization steps:")
        logger.info("1. Stop Celery workers")
        logger.info("2. Backup the database (if create_backup=True)")
        logger.info("3. Remove all job media files")
        logger.info("4. Remove all log files")
        logger.info("5. Clean temporary files and caches")
        logger.info("6. Clean SQLite journal files")
        logger.info("7. Clean static files")
        logger.info("8. Clean session files")
        logger.info("9. Recreate the database from scratch")
        return
    
    # Perform comprehensive cleanup first
    perform_comprehensive_cleanup(
        dry_run=dry_run, 
        create_backup=create_backup, 
        keep_users=True,  # Keep users by default in reinit
        remove_backups=False,  # Preserve backups
        include_celery=True,
        include_sessions=True
    )
    
    # Recreate the database from scratch
    recreate_database(dry_run=dry_run, create_backup=False)  # Backup already created above
    
    logger.info("Project reinitialization completed!")
    logger.info("Remember to create a superuser with: python manage.py createsuperuser")

@handle_errors("complete_cleanup")
def complete_cleanup(dry_run=False, create_backup=True):
    """Perform a complete cleanup of all files while maintaining project structure"""
    logger.info("Performing complete cleanup...")
    
    if dry_run:
        logger.info("Would perform complete cleanup (removing all non-essential files)")
        return
    
    # Use the shared cleanup function with more aggressive settings
    perform_comprehensive_cleanup(
        dry_run=dry_run,
        create_backup=create_backup,
        keep_users=False,  # Remove all users
        remove_backups=True,  # Remove all backups
        include_celery=True,
        include_sessions=True
    )
    
    logger.info("Complete cleanup finished.")
    logger.info("Project is now in a clean state with minimal files.")

def main():
    """Main function to coordinate cleanup tasks"""
    parser = argparse.ArgumentParser(description='Clean up JP2Forge Web application data')
    parser.add_argument('--all', action='store_true', help='Clean everything using standard (safe) options')
    parser.add_argument('--complete', action='store_true', help='Complete cleanup (removes all logs, database backups, preserves only essential files)')
    parser.add_argument('--jobs', action='store_true', help='Clean only job records and their media files')
    parser.add_argument('--logs', action='store_true', help='Clear log file contents (preserves files, but empties them)')
    parser.add_argument('--remove-all-logs', action='store_true', help='Remove all log files completely')
    parser.add_argument('--temp', action='store_true', help='Clean only temporary files and caches')
    parser.add_argument('--celery', action='store_true', help='Reset only Celery tasks')
    parser.add_argument('--sqlite', action='store_true', help='Clean SQLite journal files and optimize database')
    parser.add_argument('--sqlite-backups', action='store_true', help='Remove SQLite database backup files')
    parser.add_argument('--static', action='store_true', help='Remove collected static files')
    parser.add_argument('--sessions', action='store_true', help='Clean Django session files')
    parser.add_argument('--keep-users', action='store_true', help='Keep user accounts when cleaning jobs (default: True)')
    parser.add_argument('--no-keep-users', action='store_true', help='Remove user accounts when cleaning (overrides --keep-users)')
    parser.add_argument('--reinit', action='store_true', help='Full project reinitialization (recreates database, removes all data)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without actually cleaning')
    parser.add_argument('--no-backup', action='store_true', help='Skip creating backups before clearing files')
    parser.add_argument('--debug', action='store_true', help='Enable more verbose debug output')
    parser.add_argument('--safe-all', action='store_true', help='Like --all but excludes operations that might cause errors')
    
    args = parser.parse_args()
    
    # If debug flag is set, increase logging level
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    # Handle special case for --all
    if args.all:
        logger.info("--all option detected. Using safer --safe-all instead to avoid potential errors.")
        args.all = False
        args.safe_all = True
    
    # If no specific tasks are selected, show help instead of treating as --all
    if not any([args.all, args.safe_all, args.complete, args.jobs, args.logs, args.remove_all_logs, args.temp, 
                args.celery, args.sqlite, args.sqlite_backups, args.static, args.sessions, 
                args.reinit]):
        logger.info("No specific cleanup options selected. Please specify what to clean up.")
        logger.info("For safer options, try: --temp, --logs, or --sqlite")
        logger.info("Use --help to see all available options")
        return 0
    
    # Handle conflicting arguments
    create_backup = not args.no_backup
    keep_users = True if args.keep_users else not args.no_keep_users
    
    logger.info("Starting JP2Forge Web cleanup...")
    
    if args.dry_run:
        logger.info("DRY RUN MODE: No files will actually be deleted")
    
    # Handle special modes first
    if args.reinit:
        reinitialize_project(dry_run=args.dry_run, create_backup=create_backup)
        return 0
    
    if args.complete:
        complete_cleanup(dry_run=args.dry_run, create_backup=create_backup)
        return 0
    
    # Handle individual cleanup tasks
    if args.remove_all_logs:
        remove_all_logs(dry_run=args.dry_run)
    
    if args.all or args.safe_all or args.jobs:
        clean_database(keep_users=keep_users, dry_run=args.dry_run)
        clean_media_files(dry_run=args.dry_run)
    
    if args.all or args.safe_all or args.logs:
        # Skip log cleaning if remove_all_logs was specified
        if not args.remove_all_logs:
            clean_log_files(dry_run=args.dry_run, create_backup=create_backup)
    
    if args.all or args.safe_all or args.temp:
        clean_temp_files(dry_run=args.dry_run)
    
    if args.all or args.celery:
        # The celery task is excluded from --safe-all
        reset_celery_tasks(dry_run=args.dry_run)
    
    if args.all or args.safe_all or args.sqlite:
        clean_sqlite_files(dry_run=args.dry_run, clean_backups=False)
    
    if args.sqlite_backups:
        clean_sqlite_files(dry_run=args.dry_run, clean_backups=True)
    
    if args.all or args.safe_all or args.static:
        clean_static_files(dry_run=args.dry_run)
    
    if args.all or args.sessions:
        # The sessions task is excluded from --safe-all
        clean_session_files(dry_run=args.dry_run)
    
    logger.info("JP2Forge Web cleanup completed successfully!")
    return 0

if __name__ == '__main__':
    sys.exit(main())