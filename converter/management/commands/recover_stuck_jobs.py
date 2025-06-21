#!/usr/bin/env python
"""
Management command to recover stuck jobs in the JP2Forge Web application.

This command will:
1. Find jobs stuck in "pending" state
2. Reset them to allow processing to continue
3. Verify Redis is configured correctly
4. Flush relevant queues in Redis if necessary
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from converter.models import ConversionJob
import redis
import subprocess
import time
import logging

class Command(BaseCommand):
    help = 'Recover conversion jobs stuck in pending state'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than',
            type=int,
            default=15,
            help='Only recover jobs older than this many minutes (default: 15)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--reset-redis',
            action='store_true',
            help='Reset Redis task queues (use with caution)',
        )
        parser.add_argument(
            '--fix-redis-config',
            action='store_true',
            help='Fix Redis configuration issues to prevent future problems',
        )
        
    def handle(self, *args, **options):
        older_than = options['older_than']
        dry_run = options['dry_run']
        reset_redis = options['reset_redis']
        fix_redis_config = options['fix_redis_config']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY RUN mode - no changes will be made'))
        
        # Step 1: Find stuck jobs
        cutoff_time = timezone.now() - timezone.timedelta(minutes=older_than)
        stuck_jobs = ConversionJob.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        job_count = stuck_jobs.count()
        if job_count == 0:
            self.stdout.write(self.style.SUCCESS(f'No stuck jobs found older than {older_than} minutes'))
            
            # Even if no stuck jobs, check and fix Redis if requested
            if fix_redis_config:
                self._fix_redis_config(dry_run)
                
            return
        
        self.stdout.write(self.style.WARNING(f'Found {job_count} stuck jobs older than {older_than} minutes'))
        
        # Step 2: First check and fix Redis configuration if requested
        if fix_redis_config:
            self._fix_redis_config(dry_run)
            
        # Step 3: Reset Redis task queues if requested
        if reset_redis and not dry_run:
            self._reset_redis_queues()
            
        # Step 4: Process stuck jobs
        recovered = 0
        for job in stuck_jobs:
            self.stdout.write(f'Job {job.id}: {job.original_filename} - Created: {job.created_at}')
            
            if not dry_run:
                # Update job to retry
                job.status = 'retry'
                job.progress = 0
                job.error_message = 'Recovered from stuck pending state by admin command'
                job.save()
                
                # Requeue the job in Celery
                try:
                    from converter.tasks import process_conversion_job
                    result = process_conversion_job.delay(str(job.id))
                    self.stdout.write(f'  ↳ Re-queued as task {result.id}')
                    recovered += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ↳ Failed to re-queue: {str(e)}'))
            else:
                self.stdout.write('  ↳ Would recover this job (dry run)')
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f'Successfully recovered {recovered} of {job_count} stuck jobs'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Would recover {job_count} stuck jobs (dry run)'))
    
    def _fix_redis_config(self, dry_run):
        """Fix Redis configuration to prevent jobs from getting stuck"""
        self.stdout.write('Checking Redis configuration...')
        
        try:
            # Connect to Redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()  # Test connection
            
            # Check if stop-writes-on-bgsave-error is enabled
            config = r.config_get('stop-writes-on-bgsave-error')
            if config.get('stop-writes-on-bgsave-error') == 'yes':
                self.stdout.write(self.style.WARNING(
                    'Redis is configured to stop writes on background save error - '
                    'this can cause jobs to get stuck in pending state'
                ))
                
                if not dry_run:
                    # Fix the configuration
                    r.config_set('stop-writes-on-bgsave-error', 'no')
                    self.stdout.write(self.style.SUCCESS(
                        'Fixed Redis configuration: disabled stop-writes-on-bgsave-error'
                    ))
                else:
                    self.stdout.write('Would fix Redis configuration (dry run)')
            else:
                self.stdout.write(self.style.SUCCESS(
                    'Redis configuration is correct (stop-writes-on-bgsave-error is disabled)'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking Redis configuration: {str(e)}'))
    
    def _reset_redis_queues(self):
        """Reset Redis queues related to Celery tasks"""
        self.stdout.write('Resetting Redis Celery queues...')
        
        try:
            # Connect to Redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            
            # Find all Celery task keys
            celery_keys = r.keys('celery*')
            if celery_keys:
                self.stdout.write(f'Found {len(celery_keys)} Celery-related keys in Redis')
                
                # Purge Celery queues
                result = subprocess.run(
                    ['celery', '-A', 'jp2forge_web', 'purge', '-f'], 
                    capture_output=True, 
                    text=True
                )
                
                if 'purged' in result.stdout.lower():
                    self.stdout.write(self.style.SUCCESS('Successfully purged Celery queues'))
                else:
                    self.stdout.write(self.style.WARNING(
                        f'Celery purge command returned: {result.stdout}'
                    ))
                
                # Wait for workers to pick up the purge
                time.sleep(2)
            else:
                self.stdout.write('No Celery task keys found in Redis')
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error resetting Redis queues: {str(e)}'))