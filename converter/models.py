"""Django models for the JP2Forge Web converter application.

This module defines the data models used to manage JPEG2000 conversion jobs,
including job metadata, file handling, and BnF compliance tracking.
"""

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
import os

def job_directory_path(instance, filename):
    """Generate unique file upload path for conversion job files.
    
    Creates a directory structure: MEDIA_ROOT/jobs/<job_id>/<filename>
    This ensures each job has its own isolated directory for file management.
    
    Args:
        instance (ConversionJob): The ConversionJob model instance
        filename (str): Original filename being uploaded
        
    Returns:
        str: Relative path for file storage
    """
    return f'jobs/{instance.id}/{filename}'

class ConversionJob(models.Model):
    """Model representing a JPEG2000 conversion job.
    
    This model tracks all aspects of a conversion job from initial file upload
    through processing to completion. It supports various compression modes
    including BnF (Bibliothèque nationale de France) compliance for cultural
    heritage digitization standards.
    
    The model handles both single-page and multi-page document conversions,
    tracks quality metrics (PSNR, SSIM), and maintains detailed job history
    for auditing and analysis purposes.
    
    Attributes:
        id (UUIDField): Unique identifier for the job
        user (ForeignKey): User who created the job
        original_file (FileField): Uploaded source file
        original_filename (str): Original name of uploaded file
        output_filename (str): Generated output filename
        result_file (FileField): Primary conversion result file
        compression_mode (str): Type of compression applied
        document_type (str): Category of document being processed
        bnf_compliant (bool): Whether BnF standards are enforced
        quality (float): Quality setting for compression
        status (str): Current processing status
        progress (float): Completion percentage (0-100)
        task_id (str): Celery task identifier
        original_size (int): Size of input file in bytes
        converted_size (int): Size of output file in bytes
        compression_ratio (float): Ratio of compression achieved
        created_at (datetime): Job creation timestamp
        updated_at (datetime): Last modification timestamp
        completed_at (datetime): Job completion timestamp
        metrics (dict): Quality metrics and conversion statistics
        error_message (str): Error details if job failed
        enable_expert_mode (bool): Whether advanced options are enabled
    """
    # Compression mode choices with detailed descriptions
    COMPRESSION_CHOICES = [
        ('lossless', 'Lossless'),        # No quality loss, larger files
        ('lossy', 'Lossy'),              # Higher compression, some quality loss
        ('supervised', 'Supervised'),     # Quality-controlled with metrics
        ('bnf_compliant', 'BnF Compliant'),  # Meets BnF digitization standards
    ]
    
    # Document type choices for optimization
    DOCUMENT_TYPE_CHOICES = [
        ('photograph', 'Photograph'),              # Standard photographic images
        ('heritage_document', 'Heritage Document'),  # Historical documents
        ('color', 'Color'),                        # General color images
        ('grayscale', 'Grayscale'),               # Black and white images
    ]
    
    # Job processing status tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),        # Waiting to be processed
        ('processing', 'Processing'),  # Currently being converted
        ('completed', 'Completed'),    # Successfully finished
        ('failed', 'Failed'),         # Conversion failed with error
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversion_jobs')
    original_file = models.FileField(upload_to=job_directory_path)
    original_filename = models.CharField(max_length=255)
    output_filename = models.CharField(max_length=255, blank=True, null=True)
    result_file = models.FileField(upload_to=job_directory_path, blank=True, null=True)
    
    compression_mode = models.CharField(max_length=20, choices=COMPRESSION_CHOICES, default='supervised')
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='photograph')
    bnf_compliant = models.BooleanField(default=False)
    quality = models.FloatField(default=40.0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    progress = models.FloatField(default=0)
    task_id = models.CharField(max_length=255, blank=True, null=True)
    
    original_size = models.BigIntegerField(blank=True, null=True)
    converted_size = models.BigIntegerField(blank=True, null=True)
    compression_ratio = models.FloatField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    metrics = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, null=True)
    enable_expert_mode = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.original_filename} - {self.status}"
    
    def get_absolute_url(self):
        return reverse('job_detail', args=[str(self.id)])
    
    @property
    def has_multiple_outputs(self):
        """Check if this job has multiple output JP2 files (like from a multi-page TIFF)"""
        from django.conf import settings
        import os
        
        # Path to the job's output directory
        output_dir = os.path.join(settings.MEDIA_ROOT, f'jobs/{self.id}/output')
        
        # If output directory doesn't exist, return False
        if not os.path.exists(output_dir):
            return False
        
        # Count JP2 files in the directory
        jp2_files = [f for f in os.listdir(output_dir) if f.endswith('.jp2')]
        
        # If there are more than one JP2 file, it's a multi-page document
        return len(jp2_files) > 1
    
    def save(self, *args, **kwargs):
        """Override save method to automatically set original_filename.
        
        Ensures that the original_filename field is populated with the
        basename of the uploaded file if not already set. This provides
        a clean filename reference independent of the file storage path.
        
        Args:
            *args: Variable positional arguments passed to parent save
            **kwargs: Variable keyword arguments passed to parent save
        """
        if not self.original_filename and self.original_file:
            self.original_filename = os.path.basename(self.original_file.name)
        super().save(*args, **kwargs)
