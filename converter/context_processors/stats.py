from django.db.models import Count, Case, When, IntegerField
from django.conf import settings
from converter.models import ConversionJob

def global_stats(request):
    """
    Context processor to add global stats to all templates
    """
    # Initialize the context dictionary with version
    context = {
        'VERSION': getattr(settings, 'VERSION', '0.1.0')
    }
    
    if not request.user.is_authenticated:
        return context
    
    # Get basic job counts for the navigation badges
    job_counts = ConversionJob.objects.filter(user=request.user).aggregate(
        processing_count=Count(Case(When(status='processing', then=1), output_field=IntegerField())),
        pending_count=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
    )
    
    # Add total in-progress count
    job_counts['in_progress_count'] = job_counts['processing_count'] + job_counts['pending_count']
    
    # Update context with job counts
    context['global_job_counts'] = job_counts
    
    return context
