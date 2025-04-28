from django.db.models import Count, Case, When, IntegerField
from converter.models import ConversionJob

def global_stats(request):
    """
    Context processor to add global stats to all templates
    """
    if not request.user.is_authenticated:
        return {}
    
    # Get basic job counts for the navigation badges
    job_counts = ConversionJob.objects.filter(user=request.user).aggregate(
        processing_count=Count(Case(When(status='processing', then=1), output_field=IntegerField())),
        pending_count=Count(Case(When(status='pending', then=1), output_field=IntegerField())),
    )
    
    # Add total in-progress count
    job_counts['in_progress_count'] = job_counts['processing_count'] + job_counts['pending_count']
    
    return {
        'global_job_counts': job_counts,
    }
