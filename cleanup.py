#!/usr/bin/env python
"""
JP2Forge Web Environment Cleanup Script

This script performs a comprehensive cleanup of the JP2Forge Web application environment:
1. Stops running Django and Celery processes
2. Removes Python cache files and directories
3. Removes virtual environment directories
4. Removes compiled static files
5. Removes media files (uploaded images and conversion results)
6. Resets the database (by removing db.sqlite3)
7. Removes log files
8. Verifies that no processes are left running

Usage:
    python cleanup.py [--keep-db] [--keep-media] [--keep-logs] [--skip-kill]
                      [--quick-setup]

Options:
    --keep-db      Keep the database file (db.sqlite3)
    --keep-media   Keep the media files (uploaded images and results)
    --keep-logs    Keep the log files
    --skip-kill    Skip terminating running processes
    --quick-setup  Run quick_reset.sh after cleanup to set up the environment
"""

import os
import shutil
import argparse
import re
import signal
import subprocess
import time
import sys
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description="Clean up JP2Forge Web environment.")
    parser.add_argument('--keep-db', action='store_true', help="Keep the database file")
    parser.add_argument('--keep-media', action='store_true', help="Keep the media files")
    parser.add_argument('--keep-logs', action='store_true', help="Keep the log files")
    parser.add_argument('--skip-kill', action='store_true', help="Skip terminating running processes")
    parser.add_argument('--quick-setup', action='store_true', help="Run quick_reset.sh after cleanup")
    return parser.parse_args()

def stop_running_processes():
    """Stop any running Django and Celery processes related to the project."""
    print("\nStopping running processes...")
    
    # Find all Django and Celery processes
    try:
        # Find processes that contain "runserver" (Django) or "celery -A jp2forge_web" (Celery)
        cmd = "ps aux | grep -E 'runserver|celery -A jp2forge_web' | grep -v grep"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        lines = result.stdout.strip().split('\n')
        
        if not lines or lines[0] == '':
            print("  No Django or Celery processes found.")
            return True
        
        killed_count = 0
        for line in lines:
            if not line:
                continue
            
            parts = line.split()
            if len(parts) < 2:
                continue
                
            pid = parts[1]
            try:
                # Validate that this is our own process before sending a signal
                pid_int = int(pid)
                cmd_check = f"ps -p {pid_int} -o command="
                proc_cmd = subprocess.run(cmd_check, shell=True, capture_output=True, text=True).stdout.strip()
                
                # Only kill processes that are related to our application
                if 'python' in proc_cmd and ('runserver' in proc_cmd or 'jp2forge_web' in proc_cmd):
                    os.kill(pid_int, signal.SIGTERM)
                    killed_count += 1
                    print(f"  Terminated process with PID {pid}")
                else:
                    print(f"  Skipped process {pid} (not related to our application)")
            except ProcessLookupError:
                print(f"  Process {pid} not found")
            except PermissionError:
                print(f"  Permission denied to kill process {pid}")
            except Exception as e:
                print(f"  Error killing process {pid}: {e}")
        
        print(f"  Terminated {killed_count} processes")
        
        # Give processes a moment to terminate
        if killed_count > 0:
            print("  Waiting for processes to terminate...")
            time.sleep(2)
            
            # Verify that processes were actually terminated
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            lines = result.stdout.strip().split('\n')
            if lines and lines[0] != '':
                print("  WARNING: Some processes are still running. They might need to be terminated manually.")
                return False
                
        return True
            
    except Exception as e:
        print(f"  Error stopping processes: {e}")
        return False

def remove_pycache_files(base_dir):
    """Remove Python cache files and directories."""
    print("\nRemoving Python cache files and directories...")
    pycache_count = 0
    pyc_count = 0
    
    for root, dirs, files in os.walk(base_dir):
        # Remove __pycache__ directories
        for d in dirs:
            if d == '__pycache__':
                pycache_path = os.path.join(root, d)
                try:
                    shutil.rmtree(pycache_path)
                    pycache_count += 1
                    print(f"  Removed: {pycache_path}")
                except Exception as e:
                    print(f"  Error removing {pycache_path}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc'):
                pyc_path = os.path.join(root, file)
                try:
                    os.remove(pyc_path)
                    pyc_count += 1
                except Exception as e:
                    print(f"  Error removing {pyc_path}: {e}")
    
    print(f"  Removed {pycache_count} __pycache__ directories and {pyc_count} .pyc files")

def run_quick_setup():
    """Run the quick_reset.sh script to set up the environment."""
    print("\nRunning quick_reset.sh to set up the environment...")
    
    # Make sure quick_reset.sh is executable
    try:
        quick_reset_path = Path(__file__).resolve().parent / 'quick_reset.sh'
        # Use more restrictive permissions (owner execute only instead of 0o755)
        os.chmod(quick_reset_path, 0o700)  # Owner read/write/execute only
        
        # Execute the script
        print("\n" + "="*60)
        print("STARTING QUICK SETUP")
        print("="*60)
        
        # Run the script without stopping Django and Celery processes (they're already stopped)
        result = subprocess.run(['./quick_reset.sh'], shell=True, check=False)
        
        if result.returncode == 0:
            print("\nQuick setup completed successfully!")
            print("\nIf the setup failed due to missing dependencies, you may need to manually install them.")
            print("For example: pip install markdown")
            print("\nTo start the application:")
            print("1. Start Django server:   source .venv/bin/activate && python manage.py runserver")
            print("2. Start Celery worker:   source .venv/bin/activate && celery -A jp2forge_web worker -l INFO")
            return True
        else:
            print("\nQuick setup failed with exit code:", result.returncode)
            return False
            
    except Exception as e:
        print(f"\nError running quick setup: {e}")
        return False

def main():
    args = parse_args()
    base_dir = Path(__file__).resolve().parent
    
    print("Starting JP2Forge Web environment cleanup...")
    
    # 0. Stop running processes
    if not args.skip_kill:
        processes_stopped = stop_running_processes()
        if not processes_stopped:
            print("\nWARNING: Some processes could not be terminated.")
            response = input("Do you want to continue with cleanup anyway? (y/n): ")
            if response.lower() != 'y':
                print("Cleanup aborted.")
                sys.exit(1)
    
    # 1. Remove Python cache files and directories
    remove_pycache_files(base_dir)
    
    # 2. Remove virtual environment directories
    print("\nRemoving virtual environment directories...")
    venv_dirs = ['.venv', 'venv', 'env']
    for venv_dir in venv_dirs:
        venv_path = base_dir / venv_dir
        if venv_path.exists() and venv_path.is_dir():
            try:
                shutil.rmtree(venv_path)
                print(f"  Removed {venv_path}")
            except Exception as e:
                print(f"  Error removing {venv_path}: {e}")
    
    # 3. Remove compiled static files
    print("\nRemoving compiled static files...")
    static_dirs = ['staticfiles']
    for static_dir in static_dirs:
        static_path = base_dir / static_dir
        if static_path.exists() and static_path.is_dir():
            try:
                shutil.rmtree(static_path)
                print(f"  Removed {static_path}")
            except Exception as e:
                print(f"  Error removing {static_path}: {e}")
    
    # 4. Remove media files (if not --keep-media)
    if not args.keep_media:
        print("\nRemoving media files...")
        media_path = base_dir / 'media'
        if media_path.exists() and media_path.is_dir():
            try:
                shutil.rmtree(media_path)
                print(f"  Removed {media_path}")
            except Exception as e:
                print(f"  Error removing {media_path}: {e}")
        
            # Recreate empty media/jobs directory
            try:
                (base_dir / 'media' / 'jobs').mkdir(parents=True, exist_ok=True)
                print("  Created empty media/jobs directory")
            except Exception as e:
                print(f"  Error creating media/jobs directory: {e}")
    else:
        print("\nKeeping media files as requested.")

    # 5. Reset the database (if not --keep-db)
    if not args.keep_db:
        print("\nRemoving database...")
        db_file = base_dir / 'db.sqlite3'
        if db_file.exists():
            try:
                os.remove(db_file)
                print(f"  Removed {db_file}")
            except Exception as e:
                print(f"  Error removing {db_file}: {e}")
    else:
        print("\nKeeping database as requested.")
    
    # 6. Remove log files (if not --keep-logs)
    if not args.keep_logs:
        print("\nRemoving log files...")
        
        # Remove files in logs directory
        logs_dir = base_dir / 'logs'
        if logs_dir.exists() and logs_dir.is_dir():
            for log_file in logs_dir.glob('*.log'):
                try:
                    os.remove(log_file)
                    print(f"  Removed {log_file}")
                except Exception as e:
                    print(f"  Error removing {log_file}: {e}")
                    
            # Make sure logs directory exists
            logs_dir.mkdir(exist_ok=True)
        else:
            # Create logs directory if it doesn't exist
            logs_dir.mkdir(exist_ok=True)
            print("  Created logs directory")
        
        # Remove root log files
        log_pattern = re.compile(r'.*\.log$')
        for file in os.listdir(base_dir):
            if log_pattern.match(file):
                log_path = base_dir / file
                try:
                    os.remove(log_path)
                    print(f"  Removed {log_path}")
                except Exception as e:
                    print(f"  Error removing {log_path}: {e}")
    else:
        print("\nKeeping log files as requested.")
    
    print("\nCleanup completed!")
    
    # 7. Run quick setup if requested
    if args.quick_setup:
        run_quick_setup()
    else:
        print("\nTo set up the environment again, run one of these commands:")
        print("  ./setup_noninteractive.sh      # Non-interactive setup")
        print("  ./quick_reset.sh               # Quick reset (recommended)")
        print("  python cleanup.py --quick-setup # Run cleanup and quick reset together")

if __name__ == "__main__":
    main()