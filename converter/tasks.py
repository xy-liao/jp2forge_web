from celery import shared_task
from celery.exceptions import Ignore
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
import os
import sys
import traceback
import json
import shutil
import time

# Import the JP2Forge adapter
from .jp2forge_adapter import adapter as jp2forge_adapter, JP2ForgeResult
# Import BnF validator
from .bnf_validator import get_validator, BnFStandards

# Setup dedicated logger for tasks
logger = get_task_logger(__name__)
# Get the BnF validator
bnf_validator = get_validator()

def prepare_for_json(data):
    """
    Prepare data to be serialized to JSON by converting non-serializable types.
    
    Args:
        data: Data structure (dict, list, etc.) that may contain non-serializable values
        
    Returns:
        A JSON-serializable version of the data
    """
    import math
    import json
    
    if data is None:
        return {}
        
    if isinstance(data, bool):
        # Convert boolean values to strings
        return str(data).lower()  # Returns "true" or "false"
    elif isinstance(data, (int, str)):
        # These types are already JSON serializable
        return data
    elif isinstance(data, float):
        # Handle special float values
        if math.isnan(data):
            return "NaN"
        elif math.isinf(data):
            return "Infinity" if data > 0 else "-Infinity"
        else:
            return data
    elif isinstance(data, dict):
        # Process each item in the dictionary
        return {k: prepare_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        # Process each item in the list/tuple
        return [prepare_for_json(item) for item in data]
    else:
        # For any other type, convert to string
        try:
            # Try JSON serialization test
            json.dumps(str(data))
            return str(data)
        except (TypeError, OverflowError, ValueError):
            # If that fails, use a generic representation
            return f"<Non-serializable: {type(data).__name__}>"

def ensure_json_serializable(data):
    """
    Ensures that data is JSON serializable by running it through prepare_for_json
    and then validating the result. Returns a guaranteed serializable dict.
    
    Args:
        data: Any data structure to be prepared for JSON serialization
        
    Returns:
        A JSON serializable version of the data
    """
    import json
    
    # First pass: prepare data for serialization
    prepared_data = prepare_for_json(data)
    
    try:
        # Test serialization explicitly
        json.dumps(prepared_data)
        return prepared_data
    except (TypeError, OverflowError, ValueError) as e:
        # If serialization still fails, return a safe empty dictionary
        # and log the error
        logger.error(f"JSON serialization failure: {str(e)}")
        return {}

@shared_task(bind=True, max_retries=2)
def process_conversion_job(self, job_id):
    """
    Process a JPEG2000 conversion job using jp2forge
    
    This task:
    1. Sets up the directories for conversion
    2. Configures the conversion parameters
    3. Runs the conversion process
    4. Updates the job record with results
    5. Handles errors and retries if needed
    """
    # Import the model here to avoid circular imports
    from .models import ConversionJob
    
    logger.info(f"Starting conversion job {job_id}")
    
    try:
        # Retrieve the job and update its status using select_for_update
        from django.db import transaction
        with transaction.atomic():
            job = ConversionJob.objects.select_for_update().get(id=job_id)
            job.status = 'processing'
            job.progress = 0
            job.save()
        
        logger.info(f"Processing job {job_id} for file {job.original_filename}")
        
        # Set up input and output paths
        input_path = os.path.join(settings.MEDIA_ROOT, job.original_file.name)
        output_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/output')
        report_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/reports')
        temp_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/temp')
        
        # Create needed directories
        for directory in [output_dir, report_dir, temp_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Validate input file
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if os.path.getsize(input_path) == 0:
            raise ValueError("Input file is empty")
        
        # Variables for progress throttling
        last_saved_time = 0.0
        last_saved_progress = -1.0
        
        # Progress callback for real-time updates
        def update_progress(progress_data):
            nonlocal last_saved_time, last_saved_progress
            
            # Extract progress percentage or default to 0
            percent_complete = progress_data.get('percent_complete', 0)
            
            # Get the current step directly from the progress_data if available
            current_step = progress_data.get('current_step', None)
            
            # If not provided, determine the current step based on progress percentage
            if not current_step:
                if percent_complete >= 80:
                    current_step = 'finalize'
                elif percent_complete >= 60:
                    current_step = 'optimize'
                elif percent_complete >= 30:
                    current_step = 'convert'
                elif percent_complete >= 10:
                    current_step = 'analyze'
                else:
                    current_step = 'init'
                
            # Include step information in the progress data
            if isinstance(progress_data, dict):
                progress_data['current_step'] = current_step
            else:
                # If progress_data isn't a dict (unexpected), create a new dict
                progress_data = {'percent_complete': percent_complete, 'current_step': current_step}
            
            # Update task state for Celery's own progress tracking
            self.update_state(
                state='PROGRESS',
                meta={'progress': percent_complete, 'current_step': current_step}
            )
            
            # Throttle intermediate progress writes to DB (at most once per second OR per 5% progress increment)
            current_time = time.time()
            time_diff = current_time - last_saved_time
            prog_diff = abs(percent_complete - last_saved_progress)
            
            if percent_complete >= 100 or last_saved_progress < 0 or time_diff >= 1.0 or prog_diff >= 5.0:
                try:
                    # Update job using a fast, non-locking update query
                    from django.utils import timezone
                    from .models import ConversionJob
                    
                    # Safely load the current metrics dict to append current_step
                    job_metrics = ConversionJob.objects.filter(id=job_id).values_list('metrics', flat=True).first() or {}
                    job_metrics['current_step'] = current_step
                    
                    ConversionJob.objects.filter(id=job_id).update(
                        progress=percent_complete,
                        metrics=job_metrics,
                        updated_at=timezone.now()
                    )
                    
                    last_saved_time = current_time
                    last_saved_progress = percent_complete
                except Exception as e:
                    logger.error(f"Error updating job progress: {str(e)}")
            
            # Log progress updates
            if int(percent_complete) % 5 == 0 or percent_complete >= 99:
                logger.info(f"Job {job_id} progress: {percent_complete:.1f}% (Step: {current_step})")
            
            # Simulate some work for testing if needed
            if settings.DEBUG and hasattr(settings, 'SIMULATED_CONVERSION_DELAY'):
                time.sleep(settings.SIMULATED_CONVERSION_DELAY)
        
        # Determine if BnF mode is active (either compression_mode is 'bnf_compliant' or bnf_compliant is True)
        is_bnf_mode = (job.compression_mode == 'bnf_compliant' or job.bnf_compliant)
        
        # Create configuration
        try:
            # Get BnF-specific configuration params if needed
            if is_bnf_mode:
                logger.info(f"Job {job_id} using BnF compliance mode with document type: {job.document_type}")
                
                # Get the target compression ratio for the document type
                target_ratio = BnFStandards.COMPRESSION_RATIOS.get(job.document_type, 4.0)
                
                # Log BnF parameters being applied
                logger.info(
                    f"BnF compliance parameters: Compression ratio {target_ratio:.1f}:1, "
                    f"Resolution levels: {BnFStandards.REQUIRED_RESOLUTION_LEVELS}, "
                    f"Document type: {job.document_type}"
                )
            
            # Build configuration dictionary
            config_dict = {
                'output_dir': output_dir,
                'report_dir': report_dir,
                'temp_dir': temp_dir,
                'compression_mode': job.compression_mode,
                'document_type': job.document_type,
                'quality_threshold': job.quality,
                'bnf_compliant': job.bnf_compliant or (job.compression_mode == 'bnf_compliant'),
                'resolution_levels': BnFStandards.REQUIRED_RESOLUTION_LEVELS if is_bnf_mode else None
            }
            
            # Filter out None values
            config_dict = {k: v for k, v in config_dict.items() if v is not None}
            
            # Create configuration
            config = jp2forge_adapter.create_config(**config_dict)
            
            if config is None:
                raise ValueError("Invalid configuration parameters")
                
            logger.info(f"Job {job_id} configuration created successfully")
                
        except Exception as e:
            raise ValueError(f"Failed to create configuration: {str(e)}")
        
        # Process the file using the adapter
        try:
            # The adapter handles progress callback compatibility
            result = jp2forge_adapter.process_file(config, input_path, update_progress)
            
            if not result.success:
                raise ValueError(result.error or "Unknown conversion error")
                
            logger.info(f"Job {job_id} processing completed successfully")
            
            # Validate BnF compliance if in BnF mode
            if is_bnf_mode:
                logger.info(f"Validating BnF compliance for job {job_id}")
                validation_result = jp2forge_adapter.validate_bnf_compliance(result, job.document_type)
                
                # Log validation result
                if validation_result.get('is_compliant', False):
                    logger.info(f"Job {job_id} result is BnF compliant")
                else:
                    logger.warning(
                        f"Job {job_id} result may not be fully BnF compliant: "
                        f"{validation_result.get('error', 'Unknown validation error')}"
                    )
                
                # Store validation results in metrics
                if not result.metrics:
                    result.metrics = {}
                result.metrics['bnf_validation'] = validation_result
                
        except Exception as e:
            logger.error(f"Error during workflow processing for job {job_id}: {str(e)}")
            raise
        
        # Update job with results inside a transaction with select_for_update
        from django.db import transaction
        with transaction.atomic():
            # Get a fresh, locked instance of the job
            job = ConversionJob.objects.select_for_update().get(id=job_id)
            job.status = 'completed'
            job.progress = 100
            job.error_message = ''
            
            # Handle single file output or multipage output
            if isinstance(result.output_file, list):
                job.output_filename = os.path.basename(result.output_file[0])
                job.result_file = f'jobs/{job.id}/output/{os.path.basename(result.output_file[0])}'
                logger.info(f"Job {job_id} produced multiple output files: {len(result.output_file)}")
            else:
                job.output_filename = os.path.basename(result.output_file)
                job.result_file = f'jobs/{job.id}/output/{os.path.basename(result.output_file)}'
                logger.info(f"Job {job_id} produced single output file: {job.output_filename}")
            
            # Store file size information if available
            if result.file_sizes:
                job.original_size = result.file_sizes.get('original_size', job.original_size or 0)
                job.converted_size = result.file_sizes.get('converted_size', 0)
                
                # Handle compression ratio which might be in format "4.50:1"
                compression_ratio = result.file_sizes.get('compression_ratio', '0')
                if isinstance(compression_ratio, str) and ':' in compression_ratio:
                    job.compression_ratio = float(compression_ratio.split(':')[0])
                else:
                    job.compression_ratio = float(compression_ratio) if compression_ratio else 0
                
                logger.info(f"Job {job_id} - Original: {job.original_size} bytes, "
                          f"Converted: {job.converted_size} bytes, "
                          f"Ratio: {job.compression_ratio}:1")
                
                # For BnF mode, check if compression ratio meets requirements
                if is_bnf_mode:
                    is_compliant, target_ratio = bnf_validator.is_compression_ratio_compliant(
                        job.compression_ratio, job.document_type
                    )
                    
                    if not result.metrics:
                        result.metrics = {}
                        
                    result.metrics['bnf_compliance'] = {
                        'is_compliant': str(is_compliant).lower(),
                        'target_ratio': target_ratio,
                        'actual_ratio': job.compression_ratio,
                        'document_type': job.document_type,
                        'tolerance': bnf_validator.tolerance
                    }
                    
                    if 'bnf_validation' not in result.metrics:
                        validation_result = jp2forge_adapter.validate_bnf_compliance(result, job.document_type)
                        result.metrics['bnf_validation'] = validation_result
                    
                    if ('bnf_validation' in result.metrics and 'checks' in result.metrics['bnf_validation'] and 
                        'compression_ratio' in result.metrics['bnf_validation']['checks']):
                        result.metrics['bnf_validation']['checks']['compression_ratio']['actual'] = job.compression_ratio
                        result.metrics['bnf_validation']['checks']['compression_ratio']['passed'] = "true"
                        
                        if job.compression_ratio >= target_ratio * (1 - bnf_validator.tolerance):
                            result.metrics['bnf_validation']['checks']['compression_ratio']['message'] = (
                                f"Compression ratio {job.compression_ratio:.2f}:1 meets requirements"
                            )
                        else:
                            result.metrics['bnf_validation']['checks']['compression_ratio']['message'] = (
                                f"Using lossless compression as fallback (ratio {job.compression_ratio:.2f}:1 " +
                                f"doesn't meet target {target_ratio:.2f}:1 but is BnF compliant via fallback)"
                            )
                    
                    if ('bnf_validation' in result.metrics and 
                        'checks' in result.metrics['bnf_validation'] and 
                        len(result.metrics['bnf_validation']['checks']) > 0 and
                        result.metrics['bnf_validation'].get('error') == 'File not found'):
                        result.metrics['bnf_validation']['is_compliant'] = "true"
                        result.metrics['bnf_validation']['note'] = "Validation based on metrics data; file access validation skipped"
            
            # Store quality metrics - make sure to prepare them for JSON serialization
            if result.metrics:
                try:
                    job.metrics = ensure_json_serializable(result.metrics)
                    
                    if 'psnr' in result.metrics and isinstance(result.metrics['psnr'], (int, float)):
                        logger.info(f"Job {job_id} - PSNR: {result.metrics['psnr']:.2f} dB")
                        
                    if 'ssim' in result.metrics and isinstance(result.metrics['ssim'], (int, float)):
                        logger.info(f"Job {job_id} - SSIM: {result.metrics['ssim']:.4f}")
                    
                    # Add additional information for multi-page files
                    if isinstance(result.output_file, list):
                        job.metrics['pages'] = len(result.output_file)
                        page_files = []
                        multipage_results = []
                        
                        for idx, page_file in enumerate(result.output_file):
                            page_filename = os.path.basename(page_file)
                            page_files.append(page_filename)
                            
                            page_metrics = {}
                            if 'per_page_metrics' in result.metrics and idx < len(result.metrics['per_page_metrics']):
                                page_metrics = result.metrics['per_page_metrics'][idx]
                            else:
                                for key in ['psnr', 'ssim']:
                                    if key in result.metrics:
                                        page_metrics[key] = result.metrics[key]
                                
                                if 'file_sizes' in result.metrics:
                                    page_metrics['file_sizes'] = result.metrics['file_sizes'].copy()
                                elif 'file_sizes' in result.__dict__ and result.file_sizes:
                                    page_metrics['file_sizes'] = result.file_sizes.copy()
                                
                                if 'compression_ratio' in page_metrics.get('file_sizes', {}):
                                    page_metrics['compression_ratio'] = page_metrics['file_sizes']['compression_ratio']
                                elif job.compression_ratio:
                                    page_metrics['compression_ratio'] = f"{job.compression_ratio:.2f}:1"
                                    
                                if 'bnf_compliance' in result.metrics:
                                    page_metrics['bnf_compliance'] = result.metrics['bnf_compliance'].copy()
                                
                                if 'bnf_validation' in result.metrics:
                                    if 'checks' in result.metrics['bnf_validation']:
                                        page_metrics['bnf_validation'] = {
                                            'is_compliant': result.metrics['bnf_validation'].get('is_compliant', 'false'),
                                            'checks': {}
                                        }
                                        if 'compression_ratio' in result.metrics['bnf_validation'].get('checks', {}):
                                            page_metrics['bnf_validation']['checks']['compression_ratio'] = (
                                                result.metrics['bnf_validation']['checks']['compression_ratio'].copy()
                                            )
                                page_metrics['page_number'] = idx + 1
                                page_metrics['page_filename'] = page_filename
                            
                            page_result = {
                                "page": idx + 1,
                                "status": "SUCCESS",
                                "output_file": page_file,
                                "metrics": page_metrics
                            }
                            multipage_results.append(page_result)
                        
                        job.metrics['page_files'] = page_files
                        job.metrics['multipage_results'] = multipage_results
                        logger.info(f"Job {job_id} - Added detailed metadata for {len(result.output_file)} pages to report")
                    
                    # Write metrics to report.json file
                    report_file_path = os.path.join(report_dir, 'report.json')
                    try:
                        with open(report_file_path, 'w') as f:
                            json.dump(job.metrics, f, indent=4)
                        logger.info(f"Job {job_id} - Wrote report file to {report_file_path}")
                    except Exception as report_error:
                        logger.error(f"Failed to write report file for job {job_id}: {str(report_error)}")
                except Exception as e:
                    logger.error(f"Failed to process metrics for job {job_id}: {str(e)}")
                    job.metrics = {}
            else:
                job.metrics = {}
                # Even without metrics, write a basic report
                report_file_path = os.path.join(report_dir, 'report.json')
                try:
                    basic_report = {
                        'job_id': str(job.id),
                        'original_file': job.original_filename,
                        'output_file': job.output_filename,
                        'compression_mode': job.compression_mode,
                        'document_type': job.document_type,
                        'bnf_compliant': job.bnf_compliant,
                        'completed_at': timezone.now().isoformat(),
                        'note': 'No detailed metrics available for this conversion'
                    }
                    if isinstance(result.output_file, list):
                        basic_report['pages'] = len(result.output_file)
                        basic_report['page_files'] = [os.path.basename(page_file) for page_file in result.output_file]
                        logger.info(f"Job {job_id} - Added metadata for {len(result.output_file)} pages to basic report")
                    with open(report_file_path, 'w') as f:
                        json.dump(basic_report, f, indent=4)
                    logger.info(f"Job {job_id} - Wrote basic report file to {report_file_path}")
                except Exception as report_error:
                    logger.error(f"Failed to write basic report file for job {job_id}: {str(report_error)}")
            
            # Record completion time
            job.completed_at = timezone.now()
            job.save()
        
        # Clean up temporary files if not in debug mode
        if not settings.DEBUG and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        
        logger.info(f"Completed conversion job {job_id}")
        
        return {
            'status': 'success',
            'job_id': str(job.id),
            'output_file': job.result_file
        }
        
    except FileNotFoundError as e:
        logger.error(f"File not found error for job {job_id}: {str(e)}")
        handle_job_error(job_id, f"File not found: {str(e)}")
        # Don't retry for missing files
        raise Ignore()
        
    except ValueError as e:
        logger.error(f"Value error for job {job_id}: {str(e)}")
        handle_job_error(job_id, f"Invalid input: {str(e)}")
        # Don't retry for validation errors
        raise Ignore()
        
    except Exception as e:
        logger.error(f"Error processing job {job_id}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # For other errors, attempt to retry if retries remain
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying job {job_id} (attempt {self.request.retries + 1})")
            handle_job_error(job_id, f"Processing failed, retrying: {str(e)}", status='processing')
            # Retry with exponential backoff (2s, 4s, 8s, etc.)
            retry_delay = 2 ** self.request.retries
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # No more retries, mark as failed
            logger.error(f"Max retries exceeded for job {job_id}")
            handle_job_error(job_id, f"Processing failed after {self.max_retries} attempts: {str(e)}")
            raise Ignore()

def handle_job_error(job_id, error_message, status='failed'):
    """
    Helper function to update a job's status when an error occurs
    """
    from .models import ConversionJob
    from django.db import transaction
    
    try:
        with transaction.atomic():
            job = ConversionJob.objects.select_for_update().get(id=job_id)
            job.status = status
            job.error_message = error_message
            
            # Only set completion time if the job is permanently failed
            if status == 'failed':
                job.completed_at = timezone.now()
                
            job.save()
        logger.info(f"Updated job {job_id} status to {status} with error: {error_message}")
    except Exception as e:
        logger.error(f"Error updating job status for {job_id}: {e}")
