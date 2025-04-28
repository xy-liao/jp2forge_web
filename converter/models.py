from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import uuid
import os

def job_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/jobs/<job_id>/<filename>
    return f'jobs/{instance.id}/{filename}'

class ConversionJob(models.Model):
    COMPRESSION_CHOICES = [
        ('lossless', 'Lossless'),
        ('lossy', 'Lossy'),
        ('supervised', 'Supervised'),
        ('bnf_compliant', 'BnF Compliant'),
    ]
    
    DOCUMENT_TYPE_CHOICES = [
        ('photograph', 'Photograph'),
        ('heritage_document', 'Heritage Document'),
        ('color', 'Color'),
        ('grayscale', 'Grayscale'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
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
        if not self.original_filename and self.original_file:
            self.original_filename = os.path.basename(self.original_file.name)
        super().save(*args, **kwargs)
