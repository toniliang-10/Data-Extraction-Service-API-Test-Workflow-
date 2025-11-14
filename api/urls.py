"""
URL configuration for the API app.

Maps URL paths to view functions for the Data Extraction Service API.
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Scan/Extraction endpoints
    path('scan/start', views.start_extraction, name='scan-start'),
    path('scan/status/<uuid:job_id>', views.job_status, name='scan-status'),
    path('scan/result/<uuid:job_id>', views.job_result, name='scan-result'),
    path('scan/cancel/<uuid:job_id>', views.cancel_job, name='scan-cancel'),
    path('scan/remove/<uuid:job_id>', views.remove_job, name='scan-remove'),
    
    # Jobs management endpoints
    path('jobs/jobs', views.list_jobs, name='jobs-list'),
    path('jobs/statistics', views.job_statistics, name='jobs-statistics'),
    
    # System endpoints
    path('health', views.health_check, name='health-check'),
]

