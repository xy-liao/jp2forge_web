#!/usr/bin/env python
"""
Log Analyzer for JP2Forge Web

This script analyzes log files to identify conversion job failures and their causes.
It parses logs from celery.log, converter.log, and error.log to provide a comprehensive
view of why processing jobs might be failing.

Usage:
    python analyze_logs.py [--job JOB_ID] [--days DAYS] [--verbose]

Options:
    --job JOB_ID    Focus analysis on a specific job ID
    --days DAYS     Analyze logs from the last N days (default: 7)
    --verbose       Show more detailed output including stack traces
"""

import os
import re
import sys
import argparse
import datetime
import glob
from collections import defaultdict, namedtuple

# Define log entry structure
LogEntry = namedtuple('LogEntry', ['timestamp', 'level', 'task_name', 'task_id', 'message'])
ErrorInfo = namedtuple('ErrorInfo', ['job_id', 'timestamp', 'error', 'details', 'stack_trace'])

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Analyze JP2Forge logs for errors')
    parser.add_argument('--job', help='Focus analysis on a specific job ID')
    parser.add_argument('--days', type=int, default=7, help='Analyze logs from the last N days')
    parser.add_argument('--verbose', action='store_true', help='Show more detailed output')
    return parser.parse_args()

def parse_timestamp(timestamp_str):
    """Parse log timestamp string into datetime object"""
    try:
        return datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
    except ValueError:
        try:
            return datetime.datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None

def parse_celery_log_line(line):
    """Parse a line from celery.log into structured data"""
    # Example: [2025-04-28 13:32:12,244: ERROR/ForkPoolWorker-7] converter.tasks.process_conversion_job[c22abd74-43e0-4d24-8b11-27f270cba451]: Error processing job 412e214b-7564-4808-80ce-77cb40f94115: WorkflowConfig.__init__() got an unexpected keyword argument 'temp_dir'
    pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+): ([A-Z]+)/[^]]*\] ([^[]*)\[([^]]*)\]: (.*)'
    match = re.match(pattern, line)
    
    if match:
        timestamp = parse_timestamp(match.group(1))
        level = match.group(2)
        task_name = match.group(3).strip()
        task_id = match.group(4)
        message = match.group(5)
        return LogEntry(timestamp, level, task_name, task_id, message)
    return None

def parse_converter_log_line(line):
    """Parse a line from converter.log into structured data"""
    # Different format without task_name and task_id
    pattern = r'([A-Z]+) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d+) (.*)'
    match = re.match(pattern, line)
    
    if match:
        level = match.group(1)
        timestamp = parse_timestamp(match.group(2))
        message = match.group(3)
        return LogEntry(timestamp, level, None, None, message)
    return None

def extract_job_id(message):
    """Extract job UUID from a log message if present"""
    job_id_pattern = r'job ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'
    match = re.search(job_id_pattern, message, re.IGNORECASE)
    if match:
        return match.group(1)
    return None

def collect_errors(log_files, cutoff_date, target_job_id=None):
    """
    Collect errors from log files
    
    Args:
        log_files: List of log file paths
        cutoff_date: Ignore entries before this date
        target_job_id: If specified, only collect errors for this job ID
        
    Returns:
        List of ErrorInfo objects
    """
    errors = []
    current_error = None
    stack_trace = []
    collecting_trace = False
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    # Check if this is a stack trace line from a previous error
                    if collecting_trace:
                        if line.strip().startswith('['):  # New log entry
                            collecting_trace = False
                            if current_error:
                                errors.append(
                                    ErrorInfo(current_error[0], current_error[1], current_error[2], 
                                              current_error[3], '\n'.join(stack_trace))
                                )
                                current_error = None
                                stack_trace = []
                        else:
                            stack_trace.append(line.strip())
                            continue
                    
                    # Try to parse as celery log format first
                    entry = parse_celery_log_line(line)
                    if not entry and 'celery' not in log_file:
                        # If not celery log, try converter log format
                        entry = parse_converter_log_line(line)
                    
                    if not entry:
                        continue
                        
                    if entry.timestamp and entry.timestamp < cutoff_date:
                        continue
                        
                    if entry.level in ('ERROR', 'CRITICAL'):
                        job_id = extract_job_id(entry.message)
                        
                        if target_job_id and job_id != target_job_id:
                            continue
                            
                        # Identify error type
                        error_type = 'Unknown Error'
                        error_details = entry.message
                        
                        # Extract specific error types
                        if 'unexpected keyword argument' in entry.message:
                            error_type = 'Configuration Parameter Error'
                        elif 'No module named' in entry.message:
                            error_type = 'Import Error'
                        elif 'file not found' in entry.message.lower():
                            error_type = 'File Not Found Error'
                        elif 'permission' in entry.message.lower():
                            error_type = 'Permission Error'
                        
                        # Start collecting stack trace if this line indicates a traceback follows
                        if 'Traceback' in entry.message:
                            collecting_trace = True
                            current_error = (job_id, entry.timestamp, error_type, error_details)
                            continue
                            
                        errors.append(ErrorInfo(job_id, entry.timestamp, error_type, error_details, ''))
            
            # Handle any remaining error at end of file
            if collecting_trace and current_error:
                errors.append(
                    ErrorInfo(current_error[0], current_error[1], current_error[2], 
                              current_error[3], '\n'.join(stack_trace))
                )
                
        except Exception as e:
            print(f"Error processing log file {log_file}: {e}", file=sys.stderr)
    
    return errors

def summarize_errors(errors):
    """Group errors by type and summarize"""
    if not errors:
        print("No errors found in the logs for the specified criteria.")
        return
    
    print(f"\nFound {len(errors)} errors in the logs.")
    
    # Group by error type
    error_types = defaultdict(list)
    for error in errors:
        error_types[error.error].append(error)
    
    print("\n=== Error Summary ===")
    for error_type, instances in error_types.items():
        print(f"\n{error_type}: {len(instances)} occurrences")
        
        # Show example of this error type
        example = instances[0]
        print(f"  Example from job {example.job_id} at {example.timestamp}:")
        print(f"  {example.details.strip()}")

def print_detailed_errors(errors, verbose=False):
    """Print detailed information about each error"""
    if not errors:
        return
        
    print("\n=== Detailed Error List ===")
    for i, error in enumerate(errors, 1):
        print(f"\nERROR #{i}:")
        print(f"Job ID:     {error.job_id or 'Not specified'}")
        print(f"Timestamp:  {error.timestamp}")
        print(f"Error Type: {error.error}")
        print(f"Details:    {error.details.strip()}")
        
        if verbose and error.stack_trace:
            print("\nStack Trace:")
            print(error.stack_trace)
        
        print("-" * 80)

def analyze_job_lifecycle(log_files, job_id):
    """Analyze the complete lifecycle of a specific job"""
    events = []
    
    for log_file in log_files:
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    entry = parse_celery_log_line(line) or parse_converter_log_line(line)
                    if not entry:
                        continue
                        
                    # Check if this line mentions our job
                    if job_id.lower() in line.lower():
                        events.append((entry.timestamp, entry.level, entry.message))
        except Exception as e:
            print(f"Error processing log file {log_file} for job lifecycle: {e}", file=sys.stderr)
    
    # Sort events by timestamp
    events.sort(key=lambda x: x[0] if x[0] else datetime.datetime.min)
    
    print(f"\n=== Job {job_id} Lifecycle ===")
    if not events:
        print("No events found for this job ID.")
        return
    
    print(f"Found {len(events)} events for job {job_id}")
    
    # Print events in chronological order
    for i, (timestamp, level, message) in enumerate(events, 1):
        print(f"\n[{timestamp}] {level}")
        print(f"  {message}")

def main():
    """Main function"""
    args = parse_args()
    
    # Get log files
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    log_files = glob.glob(os.path.join(log_dir, '*.log'))
    
    if not log_files:
        print("No log files found in the logs directory.")
        return
    
    # Calculate cutoff date
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=args.days)
    
    print(f"Analyzing logs from the past {args.days} days...")
    print(f"Log files: {', '.join(os.path.basename(f) for f in log_files)}")
    
    if args.job:
        print(f"Focusing analysis on job ID: {args.job}")
        analyze_job_lifecycle(log_files, args.job)
    
    # Collect errors
    errors = collect_errors(log_files, cutoff_date, args.job)
    
    # Generate reports
    summarize_errors(errors)
    print_detailed_errors(errors, args.verbose)
    
    # Provide recommendations
    if errors:
        print("\n=== Recommendations ===")
        
        # Look for common error patterns and suggest solutions
        error_types = {e.error for e in errors}
        
        if 'Configuration Parameter Error' in error_types:
            print("• Parameter mismatch detected between your code and the JP2Forge library.")
            print("  → Check the parameters passed to WorkflowConfig and remove any unsupported ones.")
            print("  → Make sure you're using the correct JP2Forge version (check requirements.txt).")
        
        if 'Import Error' in error_types:
            print("• Import errors detected when trying to load JP2Forge modules.")
            print("  → Verify JP2Forge is correctly installed: pip install -r requirements.txt")
            print("  → Check the import paths in converter/tasks.py to match the installed structure.")
        
        if 'File Not Found Error' in error_types:
            print("• File not found errors detected.")
            print("  → Ensure file paths are correctly specified and files exist.")
            print("  → Check permissions on the media directory.")
    
    print("\nDone.")

if __name__ == '__main__':
    main()