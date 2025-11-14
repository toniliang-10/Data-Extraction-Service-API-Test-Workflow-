"""
Database models for the Data Extraction Service.

Models:
    - Job: Tracks extraction job lifecycle and metadata
    - ExtractionResult: Stores individual extracted records
"""
import uuid
from django.db import models
from django.utils import timezone


class Job(models.Model):
    """
    Model representing an extraction job.
    
    An extraction job represents a single data extraction request from
    a third-party service. It tracks the job's progress, status, and metadata.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the job'
    )
    
    name = models.CharField(
        max_length=255,
        help_text='Human-readable name for the job'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True,
        help_text='Current status of the job'
    )
    
    config = models.JSONField(
        default=dict,
        help_text='Configuration parameters for the extraction job'
    )
    
    record_count = models.IntegerField(
        default=0,
        help_text='Number of records extracted'
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text='Error message if job failed'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the job was created'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text='When the job was last updated'
    )
    
    start_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the job started processing'
    )
    
    end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the job finished (completed, failed, or cancelled)'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Extraction Job'
        verbose_name_plural = 'Extraction Jobs'
    
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def can_be_cancelled(self):
        """Check if the job can be cancelled."""
        return self.status in ['pending', 'in_progress']
    
    def mark_as_started(self):
        """Mark the job as started."""
        self.status = 'in_progress'
        self.start_time = timezone.now()
        self.save(update_fields=['status', 'start_time', 'updated_at'])
    
    def mark_as_completed(self, record_count=0):
        """Mark the job as completed."""
        self.status = 'completed'
        self.end_time = timezone.now()
        self.record_count = record_count
        self.save(update_fields=['status', 'end_time', 'record_count', 'updated_at'])
    
    def mark_as_failed(self, error_message):
        """Mark the job as failed."""
        self.status = 'failed'
        self.end_time = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'end_time', 'error_message', 'updated_at'])
    
    def mark_as_cancelled(self):
        """Mark the job as cancelled."""
        if self.can_be_cancelled():
            self.status = 'cancelled'
            self.end_time = timezone.now()
            self.save(update_fields=['status', 'end_time', 'updated_at'])
            return True
        return False


class ExtractionResult(models.Model):
    """
    Model representing a single extracted record.
    
    Each ExtractionResult represents one record extracted from the
    third-party service, associated with a specific extraction job.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='Unique identifier for the result'
    )
    
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='results',
        help_text='The extraction job this result belongs to'
    )
    
    data = models.JSONField(
        help_text='The extracted data record (JSON format)'
    )
    
    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text='When the result was created'
    )
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['job', 'created_at']),
        ]
        verbose_name = 'Extraction Result'
        verbose_name_plural = 'Extraction Results'
    
    def __str__(self):
        return f"Result for {self.job.name} - {self.id}"

