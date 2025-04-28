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

# Setup dedicated logger for tasks
logger = get_task_logger(__name__)

def prepare_for_json(data):
    """
    Prepare data to be serialized to JSON by converting non-serializable types.
    
    Args:
        data: Data structure (dict, list, etc.) that may contain non-serializable values
        
    Returns:
        A JSON-serializable version of the data
    """
    if isinstance(data, bool):
        # Convert boolean values to strings
        return str(data).lower()  # Returns "true" or "false"
    elif isinstance(data, (int, float, str, type(None))):
        # These types are already JSON serializable
        return data
    elif isinstance(data, dict):
        # Process each item in the dictionary
        return {k: prepare_for_json(v) for k, v in data.items()}
    elif isinstance(data, (list, tuple)):
        # Process each item in the list/tuple
        return [prepare_for_json(item) for item in data]
    else:
        # For any other type, convert to string
        return str(data)

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
        # Retrieve the job and update its status
        job = ConversionJob.objects.get(id=job_id)
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
        
        # Progress callback for real-time updates
        def update_progress(progress_data):
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
            
            try:
                # Re-fetch the job from the database to avoid stale data
                from django.db import transaction
                with transaction.atomic():
                    # Get a fresh instance to ensure we're working with most recent data
                    from .models import ConversionJob
                    job_instance = ConversionJob.objects.select_for_update().get(id=job_id)
                    
                    # Update job record with current progress and step
                    job_instance.progress = percent_complete
                    
                    # Initialize metrics if empty
                    if not job_instance.metrics:
                        job_instance.metrics = {}
                    
                    # Store current step in job metrics
                    job_instance.metrics['current_step'] = current_step
                    
                    # Save the update immediately 
                    job_instance.save(update_fields=['progress', 'metrics', 'updated_at'])
                    
                    # Force commit by ending transaction
                
                # Log progress updates
                if int(percent_complete) % 5 == 0 or percent_complete >= 99:
                    logger.info(f"Job {job_id} progress: {percent_complete:.1f}% (Step: {current_step})")
            except Exception as e:
                logger.error(f"Error updating job progress: {str(e)}")
            
            # Simulate some work for testing if needed
            if settings.DEBUG and hasattr(settings, 'SIMULATED_CONVERSION_DELAY'):
                time.sleep(settings.SIMULATED_CONVERSION_DELAY)
        
        # Create configuration directly - avoid the adapter for this specific step
        try:
            # Import directly to ensure we're using the correct types
            from core.types import WorkflowConfig, CompressionMode, DocumentType
            
            # Map string values to enum values
            compression_mode_enum = getattr(CompressionMode, job.compression_mode.upper())
            document_type_enum = getattr(DocumentType, job.document_type.upper())
            
            # Create minimal config with only the essential parameters
            # that are guaranteed to be supported
            config = WorkflowConfig(
                output_dir=output_dir,
                report_dir=report_dir,
                compression_mode=compression_mode_enum,
                document_type=document_type_enum,
                quality_threshold=job.quality,
                bnf_compliant=job.bnf_compliant,
            )
            
            logger.info(f"Job {job_id} configuration: mode={job.compression_mode}, "
                      f"type={job.document_type}, quality={job.quality}")
        except Exception as e:
            raise ValueError(f"Invalid configuration parameters: {str(e)}")
        
        # Process the file using the adapter
        try:
            # The adapter handles progress callback compatibility
            result = jp2forge_adapter.process_file(config, input_path, update_progress)
            
            if not result.success:
                raise ValueError(result.error or "Unknown conversion error")
                
            logger.info(f"Job {job_id} processing completed successfully")
        except Exception as e:
            logger.error(f"Error during workflow processing for job {job_id}: {str(e)}")
            raise
        
        # Update job with results
        job.status = 'completed'
        job.progress = 100
        # Clear any previous error messages since the job is now completed successfully
        job.error_message = ''
        
        # Handle single file output or multipage output
        if isinstance(result.output_file, list):
            # Multi-page result - use the first file for the job record
            job.output_filename = os.path.basename(result.output_file[0])
            job.result_file = f'jobs/{job.id}/output/{os.path.basename(result.output_file[0])}'
            
            logger.info(f"Job {job_id} produced multiple output files: {len(result.output_file)}")
        else:
            # Single file result
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
            
            # Log the compression results
            logger.info(f"Job {job_id} - Original: {job.original_size} bytes, "
                      f"Converted: {job.converted_size} bytes, "
                      f"Ratio: {job.compression_ratio}:1")
        
        # Store quality metrics - make sure to prepare them for JSON serialization
        if result.metrics:
            # Process metrics to make them JSON serializable
            job.metrics = prepare_for_json(result.metrics)
            
            # Format common metrics for easier display
            if 'psnr' in result.metrics and isinstance(result.metrics['psnr'], (int, float)):
                logger.info(f"Job {job_id} - PSNR: {result.metrics['psnr']:.2f} dB")
                
            if 'ssim' in result.metrics and isinstance(result.metrics['ssim'], (int, float)):
                logger.info(f"Job {job_id} - SSIM: {result.metrics['ssim']:.4f}")
        else:
            job.metrics = {}
        
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
    
    try:
        job = ConversionJob.objects.get(id=job_id)
        job.status = status
        job.error_message = error_message
        
        # Only set completion time if the job is permanently failed
        if status == 'failed':
            job.completed_at = timezone.now()
            
        job.save()
        logger.info(f"Updated job {job_id} status to {status} with error: {error_message}")
    except Exception as e:
        logger.error(f"Error updating job status for {job_id}: {e}")
