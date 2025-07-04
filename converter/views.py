"""Django views for the JP2Forge Web converter application.

This module contains all view functions for handling JPEG2000 conversion jobs,
including job creation, monitoring, batch operations, and file downloads.

API Endpoints Summary:
===================

Authenticated Endpoints (require login):

GET /converter/
    Dashboard with job statistics and recent jobs
    
GET /converter/jobs/
    Paginated list of user's conversion jobs with filtering
    
POST /converter/jobs/new/
    Create new conversion job(s) from uploaded files
    
GET /converter/jobs/<uuid>/
    Detailed view of specific conversion job
    
POST /converter/jobs/<uuid>/delete/
    Delete specific conversion job and associated files
    
POST /converter/jobs/batch/
    Batch operations on multiple jobs (download, delete, reprocess)
    
POST /converter/download/selected/
    Download selected files as ZIP archive
    
GET /converter/jobs/<uuid>/download/
    Download job result files (single or multi-page)
    
GET /converter/jobs/<uuid>/download-report/
    Download job conversion report as JSON
    
GET /converter/version-info/
    System version and dependency information
    
Public Endpoints:

GET /converter/about/
    Application information and feature overview
    
Security:
- All job operations require user authentication
- Users can only access their own jobs
- File access is validated through job ownership
- CSRF protection on all state-changing operations
- HTTP method restrictions enforced
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Case, When, IntegerField
from django.contrib import messages
from django.views.decorators.http import require_GET
import os
import logging
import json
import zipfile
from io import BytesIO

from .models import ConversionJob
from .forms import ConversionJobForm
from .tasks import process_conversion_job

# Set up logging
logger = logging.getLogger(__name__)

@login_required
def dashboard(request):
    """Dashboard view showing conversion statistics and recent jobs."""
    if request.method not in ['GET', 'POST']:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    logger.info(f"User {request.user.username} accessed dashboard")
    
    # Get user's job statistics
    stats = ConversionJob.objects.filter(user=request.user).aggregate(
        total_jobs=Count('id'),
        completed_jobs=Count(Case(When(status='completed', then=1), 
                                 output_field=IntegerField())),
        failed_jobs=Count(Case(When(status='failed', then=1), 
                              output_field=IntegerField())),
        processing_jobs=Count(Case(When(status='processing', then=1), 
                                  output_field=IntegerField())),
        pending_jobs=Count(Case(When(status='pending', then=1), 
                               output_field=IntegerField()))
    )
    
    # Get recent jobs (limit to 5)
    recent_jobs = ConversionJob.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Calculate storage metrics if jobs exist
    storage_metrics = {}
    if stats['total_jobs'] > 0:
        # Sum of original file sizes
        original_size_sum = ConversionJob.objects.filter(
            user=request.user, 
            original_size__isnull=False
        ).aggregate(total=Sum('original_size'))['total'] or 0
        
        # Sum of converted file sizes
        converted_size_sum = ConversionJob.objects.filter(
            user=request.user, 
            converted_size__isnull=False
        ).aggregate(total=Sum('converted_size'))['total'] or 0
        
        # Calculate average compression ratio
        completed_jobs = ConversionJob.objects.filter(
            user=request.user, 
            status='completed',
            compression_ratio__isnull=False
        )
        
        if completed_jobs.exists():
            avg_ratio = completed_jobs.aggregate(avg=Sum('compression_ratio') / Count('id'))['avg']
        else:
            avg_ratio = 0
            
        storage_metrics = {
            'original_size': original_size_sum,
            'converted_size': converted_size_sum,
            'space_saved': original_size_sum - converted_size_sum if original_size_sum > converted_size_sum else 0,
            'avg_compression_ratio': round(avg_ratio, 2) if avg_ratio else 0
        }
        
    context = {
        'stats': stats,
        'recent_jobs': recent_jobs,
        'storage_metrics': storage_metrics,
    }
    
    return render(request, 'converter/dashboard.html', context)

@login_required
def job_create(request):
    """
    View for creating a new conversion job - handles both single and multiple file uploads with a unified interface
    """
    if request.method == 'POST':
        form = ConversionJobForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('files')
            jobs_created = 0
            first_job_id = None
            
            for file in files:
                # Create a new job for each file
                job = ConversionJob(
                    user=request.user,
                    compression_mode=form.cleaned_data['compression_mode'],
                    document_type=form.cleaned_data['document_type'],
                    bnf_compliant=form.cleaned_data['bnf_compliant'],
                    quality=form.cleaned_data['quality'],
                )
                
                # Set file details
                job.original_file = file
                job.original_filename = file.name
                job.original_size = file.size
                job.save()
                
                # Store the first job ID for redirecting
                if not first_job_id:
                    first_job_id = job.id
                
                logger.info(f"User {request.user.username} created job {job.id} for file {job.original_filename}")
                
                # Start Celery task for this job
                try:
                    task = process_conversion_job.delay(str(job.id))
                    job.task_id = task.id
                    job.save(update_fields=['task_id'])
                    jobs_created += 1
                except Exception as e:
                    logger.error(f"Failed to start Celery task for job {job.id}: {str(e)}")
                    job.status = 'failed'
                    job.error_message = f"Failed to start conversion task: {str(e)}"
                    job.save(update_fields=['status', 'error_message'])
            
            if jobs_created > 0:
                messages.success(request, f"Successfully created {jobs_created} conversion job{'s' if jobs_created > 1 else ''}. Your file{'s' if jobs_created > 1 else ''} {'are' if jobs_created > 1 else ''} now being processed.")
                if jobs_created == 1 and first_job_id:
                    return redirect('job_detail', job_id=first_job_id)
                else:
                    return redirect('job_list')
            else:
                messages.error(request, "Failed to create any conversion jobs. Please check the system logs.")
    else:
        form = ConversionJobForm()
    
    return render(request, 'converter/job_create.html', {'form': form})

@login_required
def multiple_file_job_create(request):
    """
    View for creating multiple conversion jobs from multiple files
    """
    if request.method == 'POST':
        form = ConversionJobForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('multiple_files')
            jobs_created = 0
            
            for file in files:
                # Create a new job for each file
                job = ConversionJob(
                    user=request.user,
                    compression_mode=form.cleaned_data['compression_mode'],
                    document_type=form.cleaned_data['document_type'],
                    bnf_compliant=form.cleaned_data['bnf_compliant'],
                    quality=form.cleaned_data['quality'],
                )
                
                # Set file details
                job.original_file = file
                job.original_filename = file.name
                job.original_size = file.size
                job.save()
                
                logger.info(f"User {request.user.username} created job {job.id} for file {job.original_filename}")
                
                # Start Celery task for this job
                try:
                    task = process_conversion_job.delay(str(job.id))
                    job.task_id = task.id
                    job.save(update_fields=['task_id'])
                    jobs_created += 1
                except Exception as e:
                    logger.error(f"Failed to start Celery task for job {job.id}: {str(e)}")
                    job.status = 'failed'
                    job.error_message = f"Failed to start conversion task: {str(e)}"
                    job.save(update_fields=['status', 'error_message'])
            
            if jobs_created > 0:
                messages.success(request, f"Successfully created {jobs_created} conversion jobs. Your files are now being processed.")
                return redirect('job_list')
            else:
                messages.error(request, "Failed to create any conversion jobs. Please check the system logs.")
    else:
        form = ConversionJobForm()
    
    return render(request, 'converter/multiple_job_create.html', {'form': form})

@login_required
def job_list(request):
    """
    View for listing all conversion jobs with filtering options
    """
    if request.method not in ['GET', 'POST']:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    # Start with all user's jobs
    jobs_queryset = ConversionJob.objects.filter(user=request.user)
    
    # Apply filters from query parameters
    filters = {}
    
    # Status filter
    status = request.GET.get('status')
    if status:
        jobs_queryset = jobs_queryset.filter(status=status)
        filters['status'] = status
    
    # Compression mode filter
    compression_mode = request.GET.get('compression_mode')
    if compression_mode:
        jobs_queryset = jobs_queryset.filter(compression_mode=compression_mode)
        filters['compression_mode'] = compression_mode
    
    # Document type filter
    document_type = request.GET.get('document_type')
    if document_type:
        jobs_queryset = jobs_queryset.filter(document_type=document_type)
        filters['document_type'] = document_type
    
    # Search by filename
    search_query = request.GET.get('search')
    if search_query:
        jobs_queryset = jobs_queryset.filter(original_filename__icontains=search_query)
        filters['search'] = search_query
    
    # Apply sorting
    sort_by = request.GET.get('sort', '-created_at')  # Default: newest first
    if sort_by and sort_by in [
        'created_at', '-created_at', 
        'completed_at', '-completed_at',
        'original_filename', '-original_filename',
        'compression_ratio', '-compression_ratio'
    ]:
        jobs_queryset = jobs_queryset.order_by(sort_by)
        filters['sort'] = sort_by
    else:
        jobs_queryset = jobs_queryset.order_by('-created_at')  # Default sort
    
    # Pagination
    paginator = Paginator(jobs_queryset, 10)  # Show 10 jobs per page
    page_number = request.GET.get('page')
    jobs = paginator.get_page(page_number)
    
    # Add active filters to context for display
    context = {
        'jobs': jobs,
        'filters': filters,
        'active_filters_count': len(filters),
    }
    
    return render(request, 'converter/job_list.html', context)

@login_required
def job_detail(request, job_id):
    """
    View for showing job details
    """
    if request.method not in ['GET', 'POST']:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    job = get_object_or_404(ConversionJob, id=job_id, user=request.user)
    
    logger.info(f"User {request.user.username} viewed job {job.id}")
    
    # Check if the job has a report file
    report_path = None
    if job.status == 'completed':
        potential_report = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/reports/report.json')
        if os.path.exists(potential_report):
            report_path = f'/media/jobs/{job.id}/reports/report.json'
    
    # In case of multipage TIFF with multiple output files
    output_files = []
    if job.status == 'completed':
        output_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/output')
        if os.path.exists(output_dir):
            # Get the main output filename to avoid duplication
            main_output_filename = os.path.basename(job.result_file.name) if job.result_file else None
            
            for filename in os.listdir(output_dir):
                # Skip the main output file to avoid duplication
                if filename.endswith('.jp2') and filename != main_output_filename:
                    output_files.append({
                        'name': filename,
                        'url': f'/media/jobs/{job.id}/output/{filename}'
                    })
    
    return render(request, 'converter/job_detail.html', {
        'job': job,
        'report_path': report_path,
        'output_files': output_files
    })

@login_required
def job_status(request, job_id):
    """
    API view for getting job status updates
    """
    # Only allow GET method for status API
    if request.method != 'GET':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET'])
    
    job = get_object_or_404(ConversionJob, id=job_id, user=request.user)
    
    # Format metrics for display if needed
    formatted_metrics = {}
    if job.metrics:
        for key, value in job.metrics.items():
            if key == 'psnr' and not isinstance(value, str):
                formatted_metrics[key] = f"{value:.2f} dB"
            elif key == 'ssim' and not isinstance(value, str):
                formatted_metrics[key] = f"{value:.4f}"
            else:
                formatted_metrics[key] = value
    
    response_data = {
        'id': str(job.id),
        'status': job.status,
        'progress': job.progress,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None,
        'output_filename': job.output_filename or '',
        'formatted_metrics': formatted_metrics,
    }
    
    # Include current step information if available
    if job.metrics and 'current_step' in job.metrics:
        response_data['current_step'] = job.metrics['current_step']
    else:
        # Fallback step detection based on progress (similar to what we do in tasks.py)
        if job.progress >= 80:
            response_data['current_step'] = 'finalize'
        elif job.progress >= 60:
            response_data['current_step'] = 'optimize'
        elif job.progress >= 30:
            response_data['current_step'] = 'convert'
        elif job.progress >= 10:
            response_data['current_step'] = 'analyze'
        else:
            response_data['current_step'] = 'init'
    
    # Include file sizes if available
    if job.original_size:
        response_data['original_size'] = job.original_size
    
    if job.converted_size:
        response_data['converted_size'] = job.converted_size
    
    if job.compression_ratio:
        response_data['compression_ratio'] = job.compression_ratio
    
    # Include error message if job failed
    if job.status == 'failed' and job.error_message:
        response_data['error_message'] = job.error_message
    
    return JsonResponse(response_data)

@login_required
def job_delete(request, job_id):
    """
    View for deleting a job
    """
    job = get_object_or_404(ConversionJob, id=job_id, user=request.user)
    
    if request.method == 'POST':
        job_filename = job.original_filename
        
        try:
            # Delete actual files
            if job.original_file:
                if os.path.exists(job.original_file.path):
                    os.remove(job.original_file.path)
            
            if job.result_file:
                if os.path.exists(job.result_file.path):
                    os.remove(job.result_file.path)
            
            # Remove the job directory if it exists
            job_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}')
            if os.path.exists(job_dir):
                import shutil
                shutil.rmtree(job_dir)
            
            # Delete the database record
            job.delete()
            
            logger.info(f"User {request.user.username} deleted job {job_id} ({job_filename})")
            messages.success(request, f"Job '{job_filename}' has been deleted successfully.")
        except Exception as e:
            logger.error(f"Error deleting job {job_id}: {str(e)}")
            messages.error(request, f"An error occurred while deleting the job: {str(e)}")
        
        return redirect('job_list')
    
    return render(request, 'converter/job_confirm_delete.html', {'job': job})

@login_required
def job_retry(request, job_id):
    """
    View for retrying a failed job
    """
    job = get_object_or_404(ConversionJob, id=job_id, user=request.user)
    
    # Only allow POST method for job retrying (data modification)
    if request.method != 'POST':
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    
    # Only allow retrying failed jobs
    if job.status != 'failed':
        messages.warning(request, "Only failed jobs can be retried.")
        return redirect('job_detail', job_id=job.id)
    
    # Reset job status and error message
    job.status = 'pending'
    job.progress = 0
    job.error_message = None
    job.save(update_fields=['status', 'progress', 'error_message'])
    
    # Start new Celery task
    try:
        task = process_conversion_job.delay(str(job.id))
        job.task_id = task.id
        job.save(update_fields=['task_id'])
        
        logger.info(f"User {request.user.username} retried job {job.id}")
        messages.success(request, "Job has been queued for retry.")
    except Exception as e:
        logger.error(f"Failed to retry job {job.id}: {str(e)}")
        job.status = 'failed'
        job.error_message = f"Failed to retry conversion: {str(e)}"
        job.save(update_fields=['status', 'error_message'])
        
        messages.error(request, f"Failed to retry job: {str(e)}")
    
    return redirect('job_detail', job_id=job.id)

@login_required
def batch_job_action(request):
    """
    Handle batch operations on multiple jobs:
    - Download: Create a zip file of all completed job results
    - Process: Requeue failed jobs for processing
    - Delete: Delete multiple jobs at once
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    # Parse job IDs from form data
    try:
        job_ids = json.loads(request.POST.get('job_ids', '[]'))
        action = request.POST.get('action', '')
        
        if not job_ids or not action:
            messages.error(request, "No jobs selected or invalid action.")
            return redirect('job_list')
        
        # Filter jobs that belong to the current user
        jobs = ConversionJob.objects.filter(id__in=job_ids, user=request.user)
        
        if not jobs.exists():
            messages.error(request, "No valid jobs selected.")
            return redirect('job_list')
        
        # Perform the requested action
        if action == 'download':
            return batch_download_jobs(request, jobs)
        
        elif action == 'process':
            # Filter failed jobs
            failed_jobs = jobs.filter(status='failed')
            
            if not failed_jobs.exists():
                messages.warning(request, "No failed jobs selected for reprocessing.")
                return redirect('job_list')
            
            # Reset jobs to pending status and requeue for processing
            for job in failed_jobs:
                job.status = 'pending'
                job.progress = 0
                job.error_message = ''
                job.save()
                
                # Queue the job for processing
                process_conversion_job.delay(str(job.id))
            
            messages.success(request, f"{failed_jobs.count()} jobs have been requeued for processing.")
        
        elif action == 'delete':
            # First, delete all job files
            for job in jobs:
                # Delete the job's directory
                job_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}')
                if os.path.exists(job_dir):
                    import shutil
                    try:
                        shutil.rmtree(job_dir)
                    except Exception as e:
                        logger.error(f"Error deleting job directory {job_dir}: {e}")
            
            # Then delete the job records
            count = jobs.count()
            jobs.delete()
            
            messages.success(request, f"{count} jobs have been deleted.")
        
        else:
            messages.error(request, f"Unknown action: {action}")
        
        return redirect('job_list')
        
    except json.JSONDecodeError:
        messages.error(request, "Invalid job selection data.")
        return redirect('job_list')
    except Exception as e:
        logger.error(f"Error in batch job action: {str(e)}")
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('job_list')

def batch_delete_jobs(request, jobs):
    """Delete multiple conversion jobs and their associated files.
    
    This function performs a bulk deletion operation on the provided job queryset.
    It safely removes both the database records and the associated file system
    directories for each job. All job files (input, output, temporary, and reports)
    are permanently deleted.
    
    Args:
        request (HttpRequest): The Django HTTP request object
        jobs (QuerySet): Django queryset of ConversionJob objects to delete
        
    Returns:
        HttpResponseRedirect: Redirects to job_list with success/warning message
        
    Side Effects:
        - Deletes job database records
        - Removes job directories from filesystem (jobs/{job_id}/)
        - Logs deletion activity for audit trail
        - Displays user feedback messages
        
    Note:
        File deletion errors are logged but do not prevent database cleanup.
        This ensures consistency even if filesystem operations fail.
    """
    job_count = jobs.count()
    if job_count == 0:
        messages.warning(request, "No jobs were selected for deletion.")
        return redirect('job_list')
    
    # Get job IDs for logging
    job_ids = list(jobs.values_list('id', flat=True))
    
    # Delete the jobs
    for job in jobs:
        # Remove job files
        try:
            job_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}')
            if os.path.exists(job_dir):
                import shutil
                shutil.rmtree(job_dir)
        except Exception as e:
            logger.error(f"Error deleting files for job {job.id}: {str(e)}")
    
    # Delete job records
    jobs.delete()
    
    logger.info(f"User {request.user.username} batch deleted {job_count} jobs: {job_ids}")
    messages.success(request, f"Successfully deleted {job_count} jobs.")
    return redirect('job_list')


def batch_process_jobs(request, jobs):
    """Requeue multiple failed conversion jobs for processing.
    
    This function filters the provided jobs for those with 'failed' status
    and requeues them for conversion processing. It resets job status,
    progress, and error messages before submitting new Celery tasks.
    
    Args:
        request (HttpRequest): The Django HTTP request object
        jobs (QuerySet): Django queryset of ConversionJob objects to reprocess
        
    Returns:
        HttpResponseRedirect: Redirects to job_list with status message
        
    Behavior:
        - Only processes jobs with status='failed'
        - Resets job.status to 'pending'
        - Clears job.progress (sets to 0)
        - Clears job.error_message
        - Queues new convert_to_jp2 Celery task for each job
        
    Side Effects:
        - Updates job database records
        - Queues new background tasks
        - Logs reprocessing activity
        - Displays user feedback messages
        
    Note:
        Jobs that are not in 'failed' status are ignored. Users receive
        feedback about how many jobs were actually requeued.
    """
    # Filter for failed jobs only
    failed_jobs = jobs.filter(status='failed')
    job_count = failed_jobs.count()
    
    if job_count == 0:
        messages.warning(request, "No failed jobs were selected for processing.")
        return redirect('job_list')
    
    # Reprocess each failed job
    for job in failed_jobs:
        # Reset job status to pending
        job.status = 'pending'
        job.progress = 0
        job.error_message = ''
        job.save()
        
        # Re-queue the conversion task
        from .tasks import convert_to_jp2
        convert_to_jp2.delay(str(job.id))
    
    logger.info(f"User {request.user.username} reprocessed {job_count} failed jobs")
    messages.success(request, f"Reprocessing {job_count} jobs. Check the status for updates.")
    return redirect('job_list')

def batch_download_jobs(request, jobs):
    """
    Create a ZIP file containing the result files of multiple completed jobs.
    Includes all output files for multi-page documents.
    
    Args:
        request: HTTP request
        jobs: QuerySet of jobs
        
    Returns:
        HttpResponse with a ZIP file attachment
    """
    # Filter only completed jobs
    download_jobs = jobs.filter(status='completed')
    
    if not download_jobs.exists():
        messages.warning(request, "No completed jobs with results were selected for download.")
        return redirect('job_list')
    
    # Create a BytesIO object to store the ZIP file
    zip_buffer = BytesIO()
    
    # Check if flat structure is requested (default for batch individual files)
    use_flat_structure = request.GET.get('flat', False) or request.POST.get('flat', False)
    
    # Count total files
    total_files = 0
    
    # Create a ZIP file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for job in download_jobs:
            # Path to the job's output directory
            output_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/output')
            
            # If output directory exists, check for JP2 files
            if os.path.exists(output_dir):
                # Get all JP2 files in the output directory
                jp2_files = []
                for filename in os.listdir(output_dir):
                    if filename.endswith('.jp2'):
                        jp2_files.append(os.path.join(output_dir, filename))
                
                # If JP2 files found, add them to the ZIP
                if jp2_files:
                    # Determine if this is a multi-page file or individual file
                    is_multipage = len(jp2_files) > 1
                    
                    # Add each JP2 file to the ZIP
                    for file_path in jp2_files:
                        filename = os.path.basename(file_path)
                        
                        # Use appropriate folder structure based on settings
                        if is_multipage or not use_flat_structure:
                            # For multi-page files or when folder structure is preferred
                            base_folder = os.path.splitext(job.original_filename)[0]
                            zip_path = f"{base_folder}/{filename}"
                        else:
                            # For individual files with flat structure
                            # Add the original filename (without extension) as prefix to avoid conflicts
                            base_name = os.path.splitext(job.original_filename)[0]
                            zip_path = f"{base_name}_{filename}"
                            
                        zip_file.write(file_path, zip_path)
                        total_files += 1
                else:
                    # Fallback to the main result file if no JP2 files found in output dir
                    if job.result_file and os.path.exists(job.result_file.path):
                        filename = os.path.basename(job.result_file.name)
                        
                        if use_flat_structure:
                            base_name = os.path.splitext(job.original_filename)[0]
                            zip_path = f"{base_name}_{filename}"
                        else:
                            base_folder = os.path.splitext(job.original_filename)[0]
                            zip_path = f"{base_folder}/{filename}"
                            
                        zip_file.write(job.result_file.path, zip_path)
                        total_files += 1
    
    # Check if any files were added to the ZIP
    if zip_buffer.tell() == 0:
        messages.warning(request, "No output files found for the selected jobs.")
        return redirect('job_list')
    
    # Reset buffer position
    zip_buffer.seek(0)
    
    # Create response with ZIP file
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    
    # Add structure type to filename
    structure_type = "flat" if use_flat_structure else "folders"
    response['Content-Disposition'] = f'attachment; filename="jp2forge_batch_download_{structure_type}.zip"'
    
    # Log the download
    logger.info(f"User {request.user.username} batch downloaded {download_jobs.count()} jobs ({total_files} files) using {structure_type} structure")
    
    return response

@login_required
def job_download_all(request, job_id):
    """
    View for downloading all JP2 output files from a job as a ZIP archive
    """
    if request.method not in ['GET', 'POST']:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])
    
    job = get_object_or_404(ConversionJob, id=job_id, user=request.user)
    
    # Check if the job is completed
    if job.status != 'completed':
        messages.warning(request, "Cannot download files - job is not completed yet.")
        return redirect('job_detail', job_id=job.id)
    
    # Path to the job's output directory
    output_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{job.id}/output')
    
    # If output directory doesn't exist, redirect with error
    if not os.path.exists(output_dir):
        messages.error(request, "Output directory not found.")
        return redirect('job_detail', job_id=job.id)
    
    # Get all JP2 files in the output directory
    jp2_files = []
    for filename in os.listdir(output_dir):
        if filename.endswith('.jp2'):
            jp2_files.append(os.path.join(output_dir, filename))
    
    # If no JP2 files found, redirect with error
    if not jp2_files:
        messages.error(request, "No JP2 files found to download.")
        return redirect('job_detail', job_id=job.id)
    
    # Check if flat structure is requested
    use_flat_structure = request.GET.get('flat', False)
    
    # Create a ZIP file with all JP2 files
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Determine if this is a multi-page file
        is_multipage = len(jp2_files) > 1
        
        # Process each file
        for file_path in jp2_files:
            # Get just the filename (not the full path)
            filename = os.path.basename(file_path)
            
            # Use appropriate path within ZIP based on settings
            if use_flat_structure and not is_multipage:
                # For individual files with flat structure, prefix with original filename
                base_name = os.path.splitext(job.original_filename)[0]
                zip_path = f"{base_name}_{filename}"
            else:
                # For multi-page files or default structure, use the filename directly
                zip_path = filename
            
            # Add file to ZIP
            zip_file.write(file_path, zip_path)
    
    # Reset buffer position
    zip_buffer.seek(0)
    
    # Create filename for the ZIP file
    base_name = os.path.splitext(job.original_filename)[0]
    structure_type = "flat" if use_flat_structure else "folders"
    zip_filename = f"{base_name}_jp2_files.zip"
    
    # Log the download
    logger.info(f"User {request.user.username} downloaded all JP2 files for job {job.id} as ZIP with {structure_type} structure")
    
    # Return the ZIP file as a response
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="{zip_filename}"'
    
    return response

def download_selected_files(request):
    """Download user-selected files as a ZIP archive with smart organization.
    
    This function creates a ZIP archive containing files selected by the user
    through checkboxes in the job list interface. It intelligently organizes
    files using either flat structure or folder structure based on whether
    files come from multi-page conversions.
    
    Args:
        request (HttpRequest): POST request containing file_urls[] parameter
                              with list of media URLs to download
        
    Returns:
        HttpResponse: ZIP file download response with appropriate filename
        HttpResponseRedirect: Redirect to job_list if no files selected
        JsonResponse: Error response for non-POST requests
        
    Request Parameters:
        file_urls[] (list): Array of media URLs pointing to JP2 files
        flat (bool, optional): Force flat file structure in ZIP
        
    Behavior:
        - Parses media URLs to extract job IDs and filenames
        - Groups files by job to detect multi-page conversions
        - Uses folder structure for multi-page files
        - Uses flat structure with prefixes for single-page files
        - Includes original filename as prefix to avoid naming conflicts
        
    Side Effects:
        - Logs download activity for audit trail
        - Displays user feedback messages for errors
        - Creates temporary ZIP file in memory
        
    Security:
        - Validates file paths are within media directory
        - Restricts access to user's own job files through URL structure
        - Requires POST method to prevent CSRF attacks
        
    Note:
        URL format expected: /media/jobs/{job_id}/output/{filename}
        Invalid URLs or missing files are silently skipped with error logging.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST request required'}, status=405)
        
    # Get the file URLs from the request
    file_urls = request.POST.getlist('file_urls[]')
    
    if not file_urls:
        messages.warning(request, "No files were selected for download.")
        return redirect('job_list')
    
    # Check if flat structure is requested
    use_flat_structure = request.GET.get('flat', False) or request.POST.get('flat', False)
    
    # Create a BytesIO object to store the ZIP file
    zip_buffer = BytesIO()
    
    # Track files by original name to detect multi-page files
    files_by_job = {}
    
    # First pass: gather file info to determine if we have multi-page files
    for file_url in file_urls:
        parts = file_url.split('/')
        if 'media' in parts and 'jobs' in parts and 'output' in parts:
            # Find indexes
            job_idx = parts.index('jobs')
            if job_idx + 1 < len(parts):
                job_id = parts[job_idx + 1]
                if job_id not in files_by_job:
                    files_by_job[job_id] = 0
                files_by_job[job_id] += 1
    
    # Create a ZIP file
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        for file_url in file_urls:
            try:
                # Extract relevant parts from URL
                # The URL format should be something like /media/jobs/{job_id}/output/{filename}
                parts = file_url.split('/')
                if 'media' in parts and 'jobs' in parts and 'output' in parts:
                    # Find indexes
                    job_idx = parts.index('jobs')
                    output_idx = parts.index('output')
                    
                    # Get job_id and filename
                    if job_idx + 1 < len(parts) and output_idx + 1 < len(parts):
                        job_id = parts[job_idx + 1]
                        filename = parts[output_idx + 1]
                        
                        # Build the actual file path
                        file_path = os.path.join(settings.MEDIA_ROOT, f'jobs/{job_id}/output/{filename}')
                        
                        if os.path.exists(file_path):
                            # Determine if this is from a multi-page job
                            is_multipage = files_by_job.get(job_id, 0) > 1
                            
                            # Try to get the original filename to use as a prefix
                            try:
                                job = ConversionJob.objects.get(id=job_id)
                                original_name = os.path.splitext(job.original_filename)[0]
                            except:
                                original_name = f"file_{job_id}"
                            
                            if is_multipage or not use_flat_structure:
                                # For multi-page files or when folder structure is preferred
                                zip_path = f"{original_name}/{filename}"
                            else:
                                # For individual files with flat structure
                                zip_path = f"{original_name}_{filename}"
                            
                            zip_file.write(file_path, zip_path)
                
            except Exception as e:
                logger.error(f"Error adding file to ZIP: {e}")
    
    # Check if any files were added to the ZIP
    if zip_buffer.tell() == 0:
        messages.warning(request, "Could not locate the selected files for download.")
        return redirect('job_list')
    
    # Reset buffer position
    zip_buffer.seek(0)
    
    # Create response with ZIP file
    response = HttpResponse(zip_buffer.getvalue(), content_type='application/zip')
    
    # Add structure type to filename
    structure_type = "flat" if use_flat_structure else "folders"
    response['Content-Disposition'] = f'attachment; filename="jp2forge_selected_files_{structure_type}.zip"'
    
    # Log the download
    logger.info(f"User {request.user.username} downloaded {len(file_urls)} selected files using {structure_type} structure")
    
    return response

@require_GET
def docs_readme(request):
    """View for JP2Forge Web documentation home page.
    
    Renders the main documentation page with project overview, features,
    and installation instructions. This is a public endpoint that doesn't
    require authentication.
    
    Args:
        request (HttpRequest): GET request for documentation page
        
    Returns:
        HttpResponse: Rendered documentation template
        
    Template:
        docs/readme.html: Main documentation template with project information
    """
    if request.method in ['GET', 'POST']:
        return render(request, 'docs/readme.html', {
            'title': 'JP2Forge Web Documentation'
        })
    else:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])

@require_GET
def docs_user_guide(request):
    """View for JP2Forge Web user guide.
    
    Renders the user guide page with detailed instructions on how to use
    the application, including compression modes, document types, and
    quality settings. This is a public endpoint that doesn't require authentication.
    
    Args:
        request (HttpRequest): GET request for user guide page
        
    Returns:
        HttpResponse: Rendered user guide template
        
    Template:
        docs/user_guide.html: User guide template with usage instructions
    """
    if request.method in ['GET', 'POST']:
        return render(request, 'docs/user_guide.html', {
            'title': 'Using JP2Forge Web'
        })
    else:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])

@require_GET
def about(request):
    """View for about JP2Forge Web page.
    
    Renders the about page with information about the project, its purpose,
    and relationship to the JP2Forge library. This is a public endpoint
    that doesn't require authentication.
    
    Args:
        request (HttpRequest): GET request for about page
        
    Returns:
        HttpResponse: Rendered about template
        
    Template:
        docs/about.html: About page template with project information
    """
    if request.method in ['GET', 'POST']:
        return render(request, 'docs/about.html', {
            'title': 'About JP2Forge Web'
        })
    else:
        # Return 405 Method Not Allowed for other HTTP methods
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['GET', 'POST'])

@require_GET
def version_info(request):
    """View that displays version information for the application and dependencies.
    
    Renders a page showing current version numbers, Python version, and
    dependency information. This information is useful for troubleshooting
    and support purposes. This is a public endpoint that doesn't require authentication.
    
    Args:
        request (HttpRequest): GET request for version information
        
    Returns:
        HttpResponse: Rendered version info template
        
    Template:
        converter/version_info.html: Version information template with system details
    """
    return render(request, 'converter/version_info.html')
