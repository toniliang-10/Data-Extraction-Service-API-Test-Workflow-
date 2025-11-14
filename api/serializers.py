"""
Serializers for the Data Extraction Service API.

These serializers handle the conversion between Django models and JSON
representations for API requests and responses.
"""
from rest_framework import serializers
from .models import Job, ExtractionResult


class ExtractionResultSerializer(serializers.ModelSerializer):
    """Serializer for extraction result data."""
    
    id_from_service = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ExtractionResult
        fields = ['id', 'data', 'created_at', 'id_from_service', 'email', 'first_name', 'last_name']
    
    def get_id_from_service(self, obj):
        """Extract id_from_service from data field."""
        return obj.data.get('id_from_service')
    
    def get_email(self, obj):
        """Extract email from data field."""
        return obj.data.get('email')
    
    def get_first_name(self, obj):
        """Extract first_name from data field."""
        return obj.data.get('first_name')
    
    def get_last_name(self, obj):
        """Extract last_name from data field."""
        return obj.data.get('last_name')


class JobSerializer(serializers.ModelSerializer):
    """Serializer for job data."""
    
    class Meta:
        model = Job
        fields = [
            'id',
            'name',
            'status',
            'config',
            'record_count',
            'error_message',
            'created_at',
            'updated_at',
            'start_time',
            'end_time',
        ]
        read_only_fields = [
            'id',
            'status',
            'record_count',
            'error_message',
            'created_at',
            'updated_at',
            'start_time',
            'end_time',
        ]


class JobListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for job lists."""
    
    class Meta:
        model = Job
        fields = [
            'id',
            'name',
            'status',
            'record_count',
            'created_at',
            'updated_at',
        ]


class JobStatusSerializer(serializers.ModelSerializer):
    """Serializer for job status endpoint."""
    
    class Meta:
        model = Job
        fields = [
            'id',
            'status',
            'record_count',
            'created_at',
            'updated_at',
            'start_time',
            'end_time',
            'error_message',
        ]


class JobStartSerializer(serializers.Serializer):
    """Serializer for starting a new extraction job."""
    
    api_token = serializers.CharField(
        required=True,
        help_text='API token for the third-party service'
    )
    record_type = serializers.ChoiceField(
        choices=['contacts', 'users'],
        default='contacts',
        required=False,
        help_text='Type of records to extract'
    )
    name = serializers.CharField(
        required=False,
        max_length=255,
        help_text='Optional name for the job'
    )
    
    def validate_api_token(self, value):
        """Validate the API token."""
        if not value or not value.strip():
            raise serializers.ValidationError("API token cannot be empty")
        return value.strip()


class JobResultSerializer(serializers.Serializer):
    """Serializer for job result endpoint response."""
    
    data = ExtractionResultSerializer(many=True, read_only=True)
    pagination = serializers.DictField(read_only=True, required=False)


class JobStatisticsSerializer(serializers.Serializer):
    """Serializer for job statistics."""
    
    total_jobs = serializers.IntegerField(read_only=True)
    completed_jobs = serializers.IntegerField(read_only=True)
    pending_jobs = serializers.IntegerField(read_only=True)
    in_progress_jobs = serializers.IntegerField(read_only=True)
    failed_jobs = serializers.IntegerField(read_only=True)
    cancelled_jobs = serializers.IntegerField(read_only=True)
    jobs_by_status = serializers.DictField(read_only=True)
    average_processing_time = serializers.FloatField(read_only=True, allow_null=True)


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check endpoint."""
    
    status = serializers.CharField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    service = serializers.CharField(read_only=True)
    version = serializers.CharField(read_only=True)
    checks = serializers.DictField(read_only=True, required=False)


class ErrorResponseSerializer(serializers.Serializer):
    """Serializer for error responses."""
    
    error = serializers.CharField(read_only=True)
    message = serializers.CharField(read_only=True, required=False)
    detail = serializers.CharField(read_only=True, required=False)
    details = serializers.DictField(read_only=True, required=False)


class SuccessResponseSerializer(serializers.Serializer):
    """Serializer for success responses."""
    
    message = serializers.CharField(read_only=True)
    job_id = serializers.UUIDField(read_only=True, required=False)

