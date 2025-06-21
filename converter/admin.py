from django.contrib import admin
from .models import ConversionJob

@admin.register(ConversionJob)
class ConversionJobAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'user', 'compression_mode', 'document_type', 
                   'status', 'created_at', 'completed_at')
    list_filter = ('status', 'compression_mode', 'document_type', 'bnf_compliant')
    search_fields = ('original_filename', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at', 'task_id')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'original_file', 'original_filename', 'result_file', 'output_filename')
        }),
        ('Conversion Settings', {
            'fields': ('compression_mode', 'document_type', 'bnf_compliant', 'quality')
        }),
        ('Status', {
            'fields': ('status', 'progress', 'task_id', 'error_message')
        }),
        ('Results', {
            'fields': ('original_size', 'converted_size', 'compression_ratio', 'metrics')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at')
        }),
    )
