"""
Django admin configuration for the Data Extraction Service.

Provides admin interface for managing extraction jobs and results.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Job, ExtractionResult


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for extraction jobs."""
    
    list_display = [
        'id',
        'name',
        'colored_status',
        'record_count',
        'created_at',
        'duration',
    ]
    
    list_filter = [
        'status',
        'created_at',
    ]
    
    search_fields = [
        'id',
        'name',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'start_time',
        'end_time',
        'duration',
    ]
    
    fieldsets = [
        ('Basic Information', {
            'fields': ['id', 'name', 'status']
        }),
        ('Configuration', {
            'fields': ['config']
        }),
        ('Results', {
            'fields': ['record_count', 'error_message']
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at', 'start_time', 'end_time', 'duration']
        }),
    ]
    
    def colored_status(self, obj):
        """Display status with color coding."""
        colors = {
            'pending': '#FFA500',
            'in_progress': '#2196F3',
            'completed': '#4CAF50',
            'failed': '#F44336',
            'cancelled': '#9E9E9E',
        }
        color = colors.get(obj.status, '#000000')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    colored_status.short_description = 'Status'
    
    def duration(self, obj):
        """Calculate and display job duration."""
        if obj.start_time and obj.end_time:
            duration = obj.end_time - obj.start_time
            seconds = duration.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                return f"{seconds/60:.1f}m"
            else:
                return f"{seconds/3600:.1f}h"
        return "-"
    duration.short_description = 'Duration'


@admin.register(ExtractionResult)
class ExtractionResultAdmin(admin.ModelAdmin):
    """Admin interface for extraction results."""
    
    list_display = [
        'id',
        'job',
        'created_at',
        'record_preview',
    ]
    
    list_filter = [
        'created_at',
    ]
    
    search_fields = [
        'id',
        'job__name',
    ]
    
    readonly_fields = [
        'id',
        'job',
        'data',
        'created_at',
    ]
    
    def record_preview(self, obj):
        """Display a preview of the extracted data."""
        data = obj.data
        if isinstance(data, dict):
            email = data.get('email', '')
            name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
            if email or name:
                return f"{name} ({email})" if name and email else (name or email)
        return str(data)[:50]
    record_preview.short_description = 'Data Preview'

