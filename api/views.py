"""
API views for the Data Extraction Service.

This module contains all the API endpoints for managing extraction jobs,
retrieving results, and checking service health.
"""
import threading
from datetime import datetime
from django.utils import timezone
from django.db.models import Count, Avg, F, Q
from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from .models import Job, ExtractionResult
from .serializers import (
    JobSerializer,
    JobListSerializer,
    JobStatusSerializer,
    JobStartSerializer,
    JobResultSerializer,
    JobStatisticsSerializer,
    HealthCheckSerializer,
    ErrorResponseSerializer,
    SuccessResponseSerializer,
    ExtractionResultSerializer,
)
from .services import ExtractionService


class StandardResultsPagination(PageNumberPagination):
    """Standard pagination for API results."""
    page_size = 100
    page_size_query_param = 'per_page'
    max_page_size = 1000


# ============================================================================
# Scan Endpoints
# ============================================================================

@extend_schema(
    request=JobStartSerializer,
    responses={
        202: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        401: ErrorResponseSerializer,
    },
    description='Start a new data extraction job',
    tags=['Extraction'],
)
@api_view(['POST'])
def start_extraction(request):
    """
    Start a new data extraction job.
    
    POST /api/v1/scan/start
    
    Request body:
        - api_token: API token for the third-party service
        - record_type: Type of records to extract (contacts/users)
        - name: Optional name for the job
    
    Returns:
        202 Accepted with job_id
    """
    serializer = JobStartSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                'error': 'Validation failed',
                'details': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Extract validated data
    api_token = serializer.validated_data['api_token']
    record_type = serializer.validated_data.get('record_type', 'contacts')
    job_name = serializer.validated_data.get('name', f'Extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    
    # Create the job
    job = Job.objects.create(
        name=job_name,
        status='pending',
        config={
            'record_type': record_type,
            'api_token': api_token[:10] + '...',  # Store masked token
        }
    )
    
    # Start extraction in background
    extraction_service = ExtractionService()
    thread = threading.Thread(
        target=extraction_service.process_extraction,
        args=(job.id, api_token, record_type)
    )
    thread.daemon = True
    thread.start()
    
    return Response(
        {'job_id': str(job.id), 'message': 'Extraction job started'},
        status=status.HTTP_202_ACCEPTED
    )


@extend_schema(
    responses={
        200: JobStatusSerializer,
        404: ErrorResponseSerializer,
    },
    description='Get the status of an extraction job',
    tags=['Extraction'],
)
@api_view(['GET'])
def job_status(request, job_id):
    """
    Get the status of an extraction job.
    
    GET /api/v1/scan/status/<job_id>
    
    Returns:
        200 OK with job status information
        404 Not Found if job doesn't exist
    """
    try:
        job = Job.objects.get(id=job_id)
    except (Job.DoesNotExist, ValueError):
        return Response(
            {'error': 'Job not found', 'message': f'Job with ID {job_id} does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = JobStatusSerializer(job)
    return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    parameters=[
        OpenApiParameter(name='page', type=int, description='Page number'),
        OpenApiParameter(name='per_page', type=int, description='Results per page'),
    ],
    responses={
        200: JobResultSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
        409: ErrorResponseSerializer,
    },
    description='Get the results of a completed extraction job',
    tags=['Extraction'],
)
@api_view(['GET'])
def job_result(request, job_id):
    """
    Get the results of an extraction job.
    
    GET /api/v1/scan/result/<job_id>
    
    Returns:
        200 OK with extraction results
        400 Bad Request if pagination parameters are invalid
        404 Not Found if job doesn't exist
        409 Conflict if job is not completed
    """
    try:
        job = Job.objects.get(id=job_id)
    except (Job.DoesNotExist, ValueError):
        return Response(
            {'error': 'Job not found', 'message': f'Job with ID {job_id} does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if job is completed
    if job.status != 'completed':
        return Response(
            {
                'error': 'Job not completed',
                'message': f'Job is currently {job.status}. Results are only available for completed jobs.'
            },
            status=status.HTTP_409_CONFLICT
        )
    
    # Get results with pagination
    paginator = StandardResultsPagination()
    results = ExtractionResult.objects.filter(job=job)
    paginated_results = paginator.paginate_queryset(results, request)
    
    serializer = ExtractionResultSerializer(paginated_results, many=True)
    
    return paginator.get_paginated_response(serializer.data)


@extend_schema(
    responses={
        200: SuccessResponseSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
        409: ErrorResponseSerializer,
    },
    description='Cancel a pending or in-progress extraction job',
    tags=['Extraction'],
)
@api_view(['POST'])
def cancel_job(request, job_id):
    """
    Cancel an extraction job.
    
    POST /api/v1/scan/cancel/<job_id>
    
    Returns:
        200 OK if job was cancelled
        400 Bad Request if job cannot be cancelled
        404 Not Found if job doesn't exist
        409 Conflict if job is already in a terminal state
    """
    try:
        job = Job.objects.get(id=job_id)
    except (Job.DoesNotExist, ValueError):
        return Response(
            {'error': 'Job not found', 'message': f'Job with ID {job_id} does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if job can be cancelled
    if not job.can_be_cancelled():
        return Response(
            {
                'error': 'Cannot cancel job',
                'message': f'Job with status "{job.status}" cannot be cancelled. Only pending or in-progress jobs can be cancelled.'
            },
            status=status.HTTP_409_CONFLICT
        )
    
    # Cancel the job
    job.mark_as_cancelled()
    
    return Response(
        {'message': f'Job {job_id} has been cancelled'},
        status=status.HTTP_200_OK
    )


@extend_schema(
    responses={
        204: None,
        404: ErrorResponseSerializer,
    },
    description='Remove an extraction job and all its results',
    tags=['Extraction'],
)
@api_view(['DELETE'])
def remove_job(request, job_id):
    """
    Remove an extraction job and all its results.
    
    DELETE /api/v1/scan/remove/<job_id>
    
    Returns:
        204 No Content if job was deleted
        404 Not Found if job doesn't exist
    """
    try:
        job = Job.objects.get(id=job_id)
    except (Job.DoesNotExist, ValueError):
        return Response(
            {'error': 'Job not found', 'message': f'Job with ID {job_id} does not exist'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Delete the job (results will be cascade deleted)
    job.delete()
    
    return Response(status=status.HTTP_204_NO_CONTENT)


# ============================================================================
# Jobs Management Endpoints
# ============================================================================

@extend_schema(
    parameters=[
        OpenApiParameter(name='status', type=str, description='Filter by job status'),
        OpenApiParameter(name='page', type=int, description='Page number'),
        OpenApiParameter(name='per_page', type=int, description='Results per page'),
    ],
    responses={
        200: JobListSerializer(many=True),
    },
    description='List all extraction jobs with optional filtering',
    tags=['Jobs'],
)
@api_view(['GET'])
def list_jobs(request):
    """
    List all extraction jobs.
    
    GET /api/v1/jobs/jobs
    
    Query parameters:
        - status: Filter by job status
        - page: Page number for pagination
        - per_page: Number of results per page
    
    Returns:
        200 OK with list of jobs
    """
    jobs = Job.objects.all()
    
    # Filter by status if provided
    job_status_filter = request.query_params.get('status')
    if job_status_filter:
        jobs = jobs.filter(status=job_status_filter)
    
    # Paginate results
    paginator = StandardResultsPagination()
    paginated_jobs = paginator.paginate_queryset(jobs, request)
    
    serializer = JobListSerializer(paginated_jobs, many=True)
    
    return paginator.get_paginated_response({'jobs': serializer.data})


@extend_schema(
    responses={
        200: JobStatisticsSerializer,
    },
    description='Get statistics about all extraction jobs',
    tags=['Jobs'],
)
@api_view(['GET'])
def job_statistics(request):
    """
    Get statistics about extraction jobs.
    
    GET /api/v1/jobs/statistics
    
    Returns:
        200 OK with job statistics
    """
    # Get counts by status
    status_counts = Job.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Build statistics
    stats = {
        'total_jobs': Job.objects.count(),
        'completed_jobs': Job.objects.filter(status='completed').count(),
        'pending_jobs': Job.objects.filter(status='pending').count(),
        'in_progress_jobs': Job.objects.filter(status='in_progress').count(),
        'failed_jobs': Job.objects.filter(status='failed').count(),
        'cancelled_jobs': Job.objects.filter(status='cancelled').count(),
        'jobs_by_status': {item['status']: item['count'] for item in status_counts},
    }
    
    # Calculate average processing time for completed jobs
    completed_jobs = Job.objects.filter(
        status='completed',
        start_time__isnull=False,
        end_time__isnull=False
    )
    
    if completed_jobs.exists():
        avg_time = completed_jobs.aggregate(
            avg_time=Avg(F('end_time') - F('start_time'))
        )['avg_time']
        stats['average_processing_time'] = avg_time.total_seconds() if avg_time else None
    else:
        stats['average_processing_time'] = None
    
    serializer = JobStatisticsSerializer(data=stats)
    serializer.is_valid()
    
    return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# Health Check Endpoint
# ============================================================================

@extend_schema(
    responses={
        200: HealthCheckSerializer,
        503: HealthCheckSerializer,
    },
    description='Check the health status of the service',
    tags=['System'],
)
@api_view(['GET'])
def health_check(request):
    """
    Check the health of the service.
    
    GET /api/v1/health
    
    Returns:
        200 OK if service is healthy
        503 Service Unavailable if service is unhealthy
    """
    health_status = {
        'status': 'ok',
        'timestamp': timezone.now().isoformat(),
        'service': 'Data Extraction Service',
        'version': '1.0.0',
        'checks': {}
    }
    
    # Check database connectivity
    try:
        Job.objects.count()
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Determine HTTP status code
    http_status = status.HTTP_200_OK if health_status['status'] == 'ok' else status.HTTP_503_SERVICE_UNAVAILABLE
    
    serializer = HealthCheckSerializer(data=health_status)
    serializer.is_valid()
    
    return Response(serializer.data, status=http_status)

