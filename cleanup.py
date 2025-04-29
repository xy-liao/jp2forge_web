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
    job_dirs = [d for d in job_dirs if not d.startswith('.')]  # Exclude hidden files like .gitkeep
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
        
        # Create a .gitkeep file to keep the directory in git
        create_gitkeep(JOBS_DIR)
        
        logger.info(f"Removed {len(job_dirs)} job directories")

def clean_log_files(dry_run=False, keep_latest_backup=True, create_backup=True):
    """Clear log files and manage backup files"""
    logger.info("Cleaning log files...")
    
    if not os.path.exists(LOGS_DIR):
        logger.info(f"Logs directory not found: {LOGS_DIR}")
        if not dry_run:
            ensure_dir_exists(LOGS_DIR)
        return
    
    # First, handle the current log files
    log_files = glob.glob(os.path.join(LOGS_DIR, "*.log"))
    logger.info(f"Found {len(log_files)} active log files")
    
    if dry_run:
        for log_file in log_files:
            logger.info(f"Would clear log file: {os.path.basename(log_file)}")
    else:
        for log_file in log_files:
            try:
                # Create a backup of the log with timestamp if requested
                if create_backup and os.path.getsize(log_file) > 0:
                    backup_name = f"{log_file}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                    shutil.copy2(log_file, backup_name)
                
                # Clear the log file
                with open(log_file, 'w') as f:
                    f.write(f"# Log cleared by cleanup script at {datetime.now().isoformat()}\n")
                
                logger.info(f"Cleared log file: {os.path.basename(log_file)}")
            except Exception as e:
                logger.error(f"Error clearing log file {log_file}: {e}")
    
    # Now, handle backup files
    backup_files = glob.glob(os.path.join(LOGS_DIR, "*.log.*.bak"))
    logger.info(f"Found {len(backup_files)} log backup files")
    
    if keep_latest_backup and len(backup_files) > 0:
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
    else:
        # Delete all backup files
        if dry_run:
            logger.info(f"Would delete all {len(backup_files)} backup files")
            for file_path in backup_files:
                logger.info(f"Would delete: {os.path.basename(file_path)}")
        else:
            for file_path in backup_files:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted backup file: {os.path.basename(file_path)}")
                except Exception as e:
                    logger.error(f"Error deleting backup file {file_path}: {e}")
    
    logger.info("Log cleaning completed")

def remove_all_logs(dry_run=False):
    """
    Remove all log files completely, including both active logs and backups
    """
    logger.info("Removing all log files...")
    
    if not os.path.exists(LOGS_DIR):
        logger.info(f"Logs directory not found: {LOGS_DIR}")
        if not dry_run:
            ensure_dir_exists(LOGS_DIR)
        return
    
    # Find all log files and backups using various patterns
    log_patterns = [
        "*.log",                     # Regular log files
        "*.log.*",                   # All log files with extensions
        "*.log.*.bak",               # Backup files
        "*_*.log",                   # Named log files (like celery_20250429_100150.log)
        "*_*.log.*"                  # Named log files with extensions
    ]
    
    all_log_files = []
    for pattern in log_patterns:
        matching_files = glob.glob(os.path.join(LOGS_DIR, pattern))
        logger.debug(f"Pattern '{pattern}' matched {len(matching_files)} files")
        all_log_files.extend(matching_files)
    
    # Remove duplicates (a file might match multiple patterns)
    all_log_files = list(set(all_log_files))
    
    # Debug listing of found files
    for file_path in all_log_files:
        logger.debug(f"Found log file: {os.path.basename(file_path)}")
    
    logger.info(f"Found {len(all_log_files)} log files to remove")
    
    if dry_run:
        for file_path in all_log_files:
            logger.info(f"Would remove log file: {os.path.basename(file_path)}")
    else:
        removed_count = 0
        failed_count = 0
        
        for file_path in all_log_files:
            try:
                # Double-check file existence to avoid errors
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed log file: {os.path.basename(file_path)}")
                    removed_count += 1
                else:
                    logger.warning(f"Log file not found: {file_path}")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error removing log file {file_path}: {e}")
        
        # Create placeholder .gitkeep file
        create_gitkeep(LOGS_DIR)
        
        logger.info(f"Successfully removed {removed_count} log files, failed to remove {failed_count}")
    
    logger.info("Log removal completed")

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
    
    # Find and process temporary directories
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
        removed_count = 0
        for pyc_file in pyc_files:
            try:
                os.remove(pyc_file)
                removed_count += 1
            except Exception as e:
                logger.error(f"Error removing file {pyc_file}: {e}")
        
        logger.info(f"Removed {removed_count} .pyc files")

def reset_celery_tasks(dry_run=False):
    """Reset Celery tasks"""
    logger.info("Resetting Celery tasks...")
    
    if dry_run:
        logger.info("Would restart Celery workers")
        return
    
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
    
    except Exception as e:
        logger.error(f"Error resetting Celery tasks: {e}")

def clean_sqlite_files(dry_run=False, clean_backups=False):
    """Clean SQLite journal files and optionally database backups"""
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
    
    # Handle database backup files if requested
    if clean_backups:
        backup_files = glob.glob(os.path.join(PROJECT_ROOT, "*.sqlite3.*.bak"))
        if backup_files:
            logger.info(f"Found {len(backup_files)} SQLite database backups")
            
            if dry_run:
                for file_path in backup_files:
                    logger.info(f"Would remove SQLite backup file: {os.path.basename(file_path)}")
            else:
                for file_path in backup_files:
                    try:
                        os.remove(file_path)
                        logger.info(f"Removed SQLite backup file: {os.path.basename(file_path)}")
                    except Exception as e:
                        logger.error(f"Error removing SQLite backup file {file_path}: {e}")
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
    
    if dry_run:
        logger.info(f"Would remove {static_file_count} files from static files directory: {STATIC_ROOT}")
    else:
        try:
            # Keep the directory but remove all contents
            for item in os.listdir(STATIC_ROOT):
                item_path = os.path.join(STATIC_ROOT, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                elif not item.startswith('.'):  # Preserve hidden files like .gitkeep
                    os.remove(item_path)
            
            # Create a placeholder file so git doesn't remove the directory
            create_gitkeep(STATIC_ROOT)
            
            logger.info(f"Removed {static_file_count} static files")
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
                
                # Create placeholder .gitkeep
                create_gitkeep(SESSION_DIR)
            except Exception as e:
                logger.error(f"Error removing session files: {e}")
    else:
        logger.info("No Django session files found")

def recreate_database(dry_run=False, create_backup=True):
    """Completely recreate the database from scratch"""
    logger.info("Recreating database...")
    
    if not os.path.exists(DATABASE_PATH):
        logger.warning(f"Database file not found: {DATABASE_PATH}")
        return
    
    if dry_run:
        logger.info(f"Would delete and recreate database file: {DATABASE_PATH}")
        return
    
    try:
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
    
    except Exception as e:
        logger.error(f"Error recreating database: {e}")

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
        logger.info("6. Clean SQLite journal files and backups")
        logger.info("7. Clean static files")
        logger.info("8. Clean session files")
        logger.info("9. Recreate the database from scratch")
        return
    
    # First stop Celery workers
    reset_celery_tasks(dry_run=dry_run)
    
    # Backup the database if requested
    if create_backup and os.path.exists(DATABASE_PATH):
        backup_name = f"{DATABASE_PATH}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        shutil.copy2(DATABASE_PATH, backup_name)
        logger.info(f"Created database backup: {os.path.basename(backup_name)}")
    
    # Clean all components thoroughly
    clean_media_files(dry_run=dry_run)
    remove_all_logs(dry_run=dry_run)  # Complete log removal
    clean_temp_files(dry_run=dry_run)
    clean_sqlite_files(dry_run=dry_run, clean_backups=False)  # Preserve backups by default
    clean_static_files(dry_run=dry_run)
    clean_session_files(dry_run=dry_run)
    
    # Recreate the database from scratch
    recreate_database(dry_run=dry_run, create_backup=False)  # Backup already created above
    
    # Create .gitkeep files in key directories
    for directory in [LOGS_DIR, os.path.join(MEDIA_ROOT, 'jobs'), STATIC_ROOT]:
        create_gitkeep(directory)
    
    logger.info("Project reinitialization completed!")
    logger.info("Remember to create a superuser with: python manage.py createsuperuser")

def complete_cleanup(dry_run=False, create_backup=True):
    """Perform a complete cleanup of all files while maintaining project structure"""
    logger.info("Performing complete cleanup...")
    
    if dry_run:
        logger.info("Would perform complete cleanup (removing all non-essential files)")
        return
    
    # Stop Celery
    reset_celery_tasks(dry_run=dry_run)
    
    # Backup database if requested
    if create_backup and os.path.exists(DATABASE_PATH):
        backup_name = f"{DATABASE_PATH}.{datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
        shutil.copy2(DATABASE_PATH, backup_name)
        logger.info(f"Created database backup: {os.path.basename(backup_name)}")
    
    # Clean up everything
    clean_media_files(dry_run=dry_run)
    remove_all_logs(dry_run=dry_run)
    clean_temp_files(dry_run=dry_run)
    clean_sqlite_files(dry_run=dry_run, clean_backups=True)  # Also clean database backups
    clean_static_files(dry_run=dry_run)
    clean_session_files(dry_run=dry_run)
    clean_database(keep_users=False, dry_run=dry_run)  # Remove all database content including users
    
    # Create .gitkeep files in key directories
    for directory in [LOGS_DIR, os.path.join(MEDIA_ROOT, 'jobs'), STATIC_ROOT]:
        create_gitkeep(directory)
    
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
    
    args = parser.parse_args()
    
    # If no specific tasks are selected, treat as --all
    if not any([args.all, args.complete, args.jobs, args.logs, args.remove_all_logs, args.temp, 
                args.celery, args.sqlite, args.sqlite_backups, args.static, args.sessions, 
                args.reinit]):
        args.all = True
    
    # Handle conflicting arguments
    create_backup = not args.no_backup
    keep_users = True if args.keep_users else not args.no_keep_users
    
    logger.info("Starting JP2Forge Web cleanup...")
    
    if args.dry_run:
        logger.info("DRY RUN MODE: No files will actually be deleted")
    
    try:
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
        
        if args.all or args.jobs:
            clean_database(keep_users=keep_users, dry_run=args.dry_run)
            clean_media_files(dry_run=args.dry_run)
        
        if args.all or args.logs:
            # Skip log cleaning if remove_all_logs was specified
            if not args.remove_all_logs:
                clean_log_files(dry_run=args.dry_run, create_backup=create_backup)
        
        if args.all or args.temp:
            clean_temp_files(dry_run=args.dry_run)
        
        if args.all or args.celery:
            reset_celery_tasks(dry_run=args.dry_run)
        
        if args.all or args.sqlite:
            clean_sqlite_files(dry_run=args.dry_run, clean_backups=False)
        
        if args.sqlite_backups:
            clean_sqlite_files(dry_run=args.dry_run, clean_backups=True)
        
        if args.all or args.static:
            clean_static_files(dry_run=args.dry_run)
        
        if args.all or args.sessions:
            clean_session_files(dry_run=args.dry_run)
        
        logger.info("JP2Forge Web cleanup completed successfully!")
        
    except Exception as e:
        logger.error(f"Cleanup failed with error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())