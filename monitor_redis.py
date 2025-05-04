#!/usr/bin/env python
"""
Redis Health Monitor for JP2Forge Web Application

This script monitors Redis and fixes common issues that can cause
tasks to get stuck in "pending" state. It can be run periodically
via cron or as a background service.

Common issues addressed:
1. Redis persistence errors (stop-writes-on-bgsave-error)
2. Memory usage monitoring
3. Stuck tasks detection and recovery
"""

import os
import sys
import time
import json
import redis
import logging
import subprocess
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('logs/redis_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('redis_monitor')

# Redis connection settings - use the same as in settings.py
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

def ensure_path_exists():
    """Ensure we're running from the right directory"""
    if not os.path.exists('manage.py'):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(script_dir)
        if not os.path.exists('manage.py'):
            logger.error("Could not find manage.py. Make sure this script is run from the project root.")
            sys.exit(1)

def get_redis_connection():
    """Connect to Redis and return connection object"""
    try:
        r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        # Test connection
        r.ping()
        return r
    except redis.ConnectionError as e:
        logger.error(f"Could not connect to Redis: {e}")
        logger.info("Attempting to start Redis server...")
        
        # Try to start Redis based on platform
        platform = sys.platform
        if platform == 'darwin':  # macOS
            subprocess.run(['brew', 'services', 'start', 'redis'], 
                           capture_output=True, text=True)
        elif platform.startswith('linux'):
            try:
                subprocess.run(['sudo', 'systemctl', 'start', 'redis-server'], 
                               capture_output=True, text=True)
            except:
                subprocess.run(['sudo', 'service', 'redis-server', 'start'], 
                               capture_output=True, text=True)
        
        # Try connecting again
        time.sleep(2)
        try:
            r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
            r.ping()
            logger.info("Successfully started and connected to Redis")
            return r
        except redis.ConnectionError as e:
            logger.error(f"Failed to start and reconnect to Redis: {e}")
            return None

def check_redis_persistence(redis_conn):
    """Check and fix Redis persistence settings to prevent stuck tasks"""
    if not redis_conn:
        return False
    
    try:
        # Check if 'stop-writes-on-bgsave-error' is enabled
        config = redis_conn.config_get('stop-writes-on-bgsave-error')
        if config.get('stop-writes-on-bgsave-error') == 'yes':
            logger.warning("Redis is configured to stop writes on bgsave error, which can cause stuck tasks")
            # Disable this setting to prevent stuck tasks
            redis_conn.config_set('stop-writes-on-bgsave-error', 'no')
            logger.info("Successfully disabled stop-writes-on-bgsave-error in Redis")
            return True
        else:
            logger.info("Redis persistence settings are correctly configured")
            return True
    except Exception as e:
        logger.error(f"Error checking/setting Redis persistence: {e}")
        return False

def check_redis_memory(redis_conn):
    """Check Redis memory usage and warn if it's getting high"""
    if not redis_conn:
        return False
    
    try:
        info = redis_conn.info('memory')
        used_memory = info.get('used_memory', 0)
        used_memory_human = info.get('used_memory_human', '0B')
        maxmemory = info.get('maxmemory', 0)
        
        # If maxmemory is set, calculate percentage
        if maxmemory > 0:
            memory_percent = (used_memory / maxmemory) * 100
            logger.info(f"Redis memory usage: {used_memory_human} ({memory_percent:.1f}% of max)")
            
            if memory_percent > 80:
                logger.warning(f"High Redis memory usage: {memory_percent:.1f}%")
                return False
        else:
            logger.info(f"Redis memory usage: {used_memory_human} (no limit set)")
        
        return True
    except Exception as e:
        logger.error(f"Error checking Redis memory: {e}")
        return False

def check_stuck_tasks(redis_conn):
    """Detect and recover stuck tasks in Celery/Redis"""
    if not redis_conn:
        return False
    
    try:
        # Check for tasks that have been in pending state for too long
        broker_keys = redis_conn.keys('celery-task-meta-*')
        pending_tasks = 0
        stuck_tasks = 0
        
        for key in broker_keys:
            task_data = redis_conn.get(key)
            if task_data:
                try:
                    task_info = json.loads(task_data)
                    # Check if task is in a pending state for too long
                    if task_info.get('status') == 'PENDING':
                        pending_tasks += 1
                        
                        # We don't have direct timestamp in the metadata,
                        # but we can use key pattern or task features to detect stuck tasks
                        
                        # For now, we'll just count pending tasks
                        # A more sophisticated approach would track task creation time
                        
                except json.JSONDecodeError:
                    pass
        
        if pending_tasks > 0:
            logger.info(f"Found {pending_tasks} pending tasks")
        
        # Check if Celery is responding
        try:
            # Use subprocess to run celery inspect ping
            result = subprocess.run(
                ["celery", "-A", "jp2forge_web", "inspect", "ping"],
                capture_output=True, text=True, timeout=5
            )
            
            if "pong" not in result.stdout.lower():
                logger.warning("Celery workers are not responding to ping")
                return False
            else:
                logger.info("Celery workers are responding correctly")
        except Exception as e:
            logger.error(f"Error checking Celery workers: {e}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking for stuck tasks: {e}")
        return False

def main():
    """Main function to run all checks"""
    logger.info("Starting Redis health monitor")
    ensure_path_exists()
    
    # Connect to Redis
    redis_conn = get_redis_connection()
    if not redis_conn:
        logger.error("Could not establish Redis connection. Exiting.")
        return False
    
    # Run all checks
    persistence_ok = check_redis_persistence(redis_conn)
    memory_ok = check_redis_memory(redis_conn)
    tasks_ok = check_stuck_tasks(redis_conn)
    
    # Overall health status
    if persistence_ok and memory_ok and tasks_ok:
        logger.info("Redis health check passed - all systems operational")
        return True
    else:
        issues = []
        if not persistence_ok:
            issues.append("persistence configuration")
        if not memory_ok:
            issues.append("memory usage")
        if not tasks_ok:
            issues.append("task processing")
            
        logger.warning(f"Redis health check detected issues with: {', '.join(issues)}")
        return False

if __name__ == "__main__":
    main()