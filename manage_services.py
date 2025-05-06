#!/usr/bin/env python
"""
JP2Forge Web Service Manager

This script provides an easy way to manage all JP2Forge Web services:
- Django development server
- Celery workers
- Redis server
- PostgreSQL database (if configured)

It prevents the common issue of having multiple instances running after repeated tests.

Usage:
    python manage_services.py [command]

Commands:
    stop        Stop all services
    start       Start all services
    restart     Restart all services
    status      Check status of all services
    clean       Stop all services and clean up temporary files
"""

import os
import sys
import subprocess
import time
import signal
import psutil
import logging
import argparse
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('jp2forge-service-manager')

# Find project root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_ROOT)

# Define configuration
SERVICES = {
    'django': {
        'process_patterns': ['manage.py runserver'],
        'start_cmd': ['python', 'manage.py', 'runserver'],
        'start_script': './start_dev.sh',
        'name': 'Django server'
    },
    'celery': {
        'process_patterns': ['celery -A jp2forge_web worker'],
        'start_cmd': ['celery', '-A', 'jp2forge_web', 'worker', '-l', 'INFO'],
        'start_script': './start_celery.sh',
        'name': 'Celery workers'
    },
    'redis': {
        'process_patterns': ['redis-server'],
        'start_cmd': ['redis-server'],  # May not work directly, system-specific
        'name': 'Redis server'
    },
    'postgres': {
        'process_patterns': ['postgres'],
        'name': 'PostgreSQL server'
    }
}

def find_processes(pattern):
    """Find processes matching the given pattern"""
    matching_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.cmdline())
            if pattern in cmdline:
                matching_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return matching_processes

def stop_process(proc, force=False):
    """Stop a process, force kill if necessary"""
    try:
        if not force:
            proc.terminate()
            try:
                proc.wait(timeout=5)  # Wait up to 5 seconds for graceful termination
                return True
            except psutil.TimeoutExpired:
                # If process didn't terminate gracefully, force kill
                proc.kill()
                return True
        else:
            # Force kill immediately
            proc.kill()
            return True
    except psutil.NoSuchProcess:
        # Process already gone
        return True
    except Exception as e:
        logger.error(f"Error stopping process {proc.pid}: {e}")
        return False

def stop_services(services=None, force=False):
    """Stop specified services or all if None provided"""
    services_to_stop = services or SERVICES.keys()
    
    for service_name in services_to_stop:
        if service_name not in SERVICES:
            logger.warning(f"Unknown service: {service_name}")
            continue
            
        service = SERVICES[service_name]
        logger.info(f"Stopping {service['name']}...")
        
        stopped_count = 0
        for pattern in service['process_patterns']:
            processes = find_processes(pattern)
            if not processes:
                continue
                
            for proc in processes:
                try:
                    pid = proc.pid
                    cmdline = ' '.join(proc.cmdline())
                    
                    # Skip if the process is this script
                    if 'manage_services.py' in cmdline:
                        continue
                        
                    if stop_process(proc, force):
                        logger.info(f"Stopped process {pid}: {cmdline[:60]}{'...' if len(cmdline) > 60 else ''}")
                        stopped_count += 1
                except Exception as e:
                    logger.error(f"Error processing {service_name} process: {e}")
        
        if stopped_count:
            logger.info(f"Stopped {stopped_count} {service['name']} processes")
        else:
            logger.info(f"No running {service['name']} processes found")
    
    return True

def start_services(services=None):
    """Start specified services or all if None provided"""
    services_to_start = services or ['django', 'celery', 'redis']
    
    # Check if redis is running first, as it's required for Celery
    if 'redis' in services_to_start:
        redis_running = bool(find_processes('redis-server'))
        if not redis_running:
            logger.warning("Redis not running - you may need to start it manually with:")
            logger.warning("  - On macOS: brew services start redis")
            logger.warning("  - On Ubuntu: sudo service redis-server start")
    
    # Start each service
    for service_name in services_to_start:
        if service_name not in SERVICES:
            logger.warning(f"Unknown service: {service_name}")
            continue
            
        service = SERVICES[service_name]
        
        # Skip PostgreSQL - should be started via system service
        if service_name == 'postgres':
            logger.info("PostgreSQL should be managed through your system's service manager")
            continue
            
        # Skip Redis - use system service/homebrew instead
        if service_name == 'redis':
            # Redis is special case, check if it's already running
            if find_processes('redis-server'):
                logger.info("Redis server is already running")
            else:
                logger.info("Please start Redis server using your system's service manager:")
                logger.info("  - On macOS: brew services start redis")
                logger.info("  - On Ubuntu: sudo service redis-server start")
                logger.info("  - On Windows: Start Redis service")
            continue
        
        # Start service using script if available
        if 'start_script' in service and os.path.exists(service['start_script']):
            logger.info(f"Starting {service['name']} using {service['start_script']}...")
            try:
                # Make sure script is executable
                os.chmod(service['start_script'], os.stat(service['start_script']).st_mode | 0o111)
                
                # Start the script detached from our process
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        [service['start_script']], 
                        stdout=devnull, 
                        stderr=devnull,
                        start_new_session=True  # Detach from our process group
                    )
                logger.info(f"Started {service['name']} with script")
            except Exception as e:
                logger.error(f"Error starting {service['name']} with script: {e}")
                
        # Fall back to command if script fails or doesn't exist
        elif 'start_cmd' in service:
            logger.info(f"Starting {service['name']} using direct command...")
            try:
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        service['start_cmd'], 
                        stdout=devnull, 
                        stderr=devnull,
                        start_new_session=True  # Detach from our process group
                    )
                logger.info(f"Started {service['name']} with command")
            except Exception as e:
                logger.error(f"Error starting {service['name']} with command: {e}")
        else:
            logger.warning(f"No start command defined for {service['name']}")
    
    return True

def restart_services(services=None, force=False):
    """Restart specified services"""
    success = stop_services(services, force)
    if success:
        # Wait a moment for processes to fully stop
        time.sleep(2)
        return start_services(services)
    return False

def check_status():
    """Check and display status of all services"""
    logger.info("Checking status of JP2Forge Web services:")
    
    all_running = True
    
    for service_name, service in SERVICES.items():
        running_processes = []
        for pattern in service['process_patterns']:
            processes = find_processes(pattern)
            # Filter out this checking process itself
            processes = [p for p in processes if 'manage_services.py' not in ' '.join(p.cmdline())]
            running_processes.extend(processes)
        
        if running_processes:
            logger.info(f"✅ {service['name']}: {len(running_processes)} process(es) running")
            for proc in running_processes[:3]:  # Show max 3 processes
                cmdline = ' '.join(proc.cmdline())
                logger.info(f"   - PID {proc.pid}: {cmdline[:60]}{'...' if len(cmdline) > 60 else ''}")
            
            if len(running_processes) > 3:
                logger.info(f"   - ... and {len(running_processes) - 3} more")
        else:
            logger.info(f"❌ {service['name']}: not running")
            all_running = False
    
    if all_running:
        logger.info("All services are running")
    else:
        logger.info("Some services are not running")
    
    return all_running

def clean_environment():
    """Stop all services and clean up temporary files"""
    logger.info("Cleaning JP2Forge Web environment...")
    
    # First stop all services
    stop_services(force=True)
    
    # Try to import cleanup module
    try:
        logger.info("Running cleanup tasks...")
        
        # We'll use the existing cleanup.py script directly
        if os.path.exists('cleanup.py'):
            # Make sure it's executable
            os.chmod('cleanup.py', os.stat('cleanup.py').st_mode | 0o111)
            
            # Run cleanup with --temp to clean temporary files and __pycache__
            subprocess.run(['python', 'cleanup.py', '--temp'], 
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            logger.info("Cleanup completed")
        else:
            logger.warning("cleanup.py not found, skipping additional cleanup tasks")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    logger.info("Environment clean-up complete")

def main():
    """Main function handling command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Manage JP2Forge Web services',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('command', choices=['stop', 'start', 'restart', 'status', 'clean'],
                        help='The command to execute')
    parser.add_argument('--services', type=str, help='Comma-separated list of services to manage (django,celery,redis,postgres)')
    parser.add_argument('--force', action='store_true', help='Force kill processes instead of graceful termination')
    
    args = parser.parse_args()
    
    # Parse services list if provided
    services = None
    if args.services:
        services = [s.strip() for s in args.services.split(',')]
        unknown_services = [s for s in services if s not in SERVICES]
        if unknown_services:
            logger.warning(f"Unknown services: {', '.join(unknown_services)}")
    
    # Run the requested command
    if args.command == 'stop':
        stop_services(services, args.force)
    elif args.command == 'start':
        start_services(services)
    elif args.command == 'restart':
        restart_services(services, args.force)
    elif args.command == 'status':
        check_status()
    elif args.command == 'clean':
        clean_environment()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)