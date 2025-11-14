"""
Database seeding utilities for tests.

Provides helper functions to populate the test database with realistic
job and extraction result data.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import uuid
from tests.mocks.mock_data import generate_sample_records


def generate_job_id() -> str:
    """Generate a unique job ID."""
    return str(uuid.uuid4())


def seed_job(
    status: str,
    record_count: int = 0,
    job_id: Optional[str] = None,
    name: str = None,
    created_minutes_ago: int = 10,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a job with specific state for testing.
    
    Args:
        status: Job status ('pending', 'in_progress', 'completed', 'failed', 'cancelled')
        record_count: Number of records associated with job
        job_id: Optional specific job ID (generates new one if not provided)
        name: Optional job name
        created_minutes_ago: How many minutes ago the job was created
        **kwargs: Additional job attributes
        
    Returns:
        Dictionary containing job data that can be used to create a database record
    """
    if not job_id:
        job_id = generate_job_id()
    
    if not name:
        name = f"test_job_{status}_{job_id[:8]}"
    
    created_at = datetime.utcnow() - timedelta(minutes=created_minutes_ago)
    
    job_data = {
        'id': job_id,
        'name': name,
        'status': status,
        'record_count': record_count,
        'created_at': created_at,
        'updated_at': created_at,
        'start_time': None,
        'end_time': None,
        'error_message': None,
        'config': kwargs.get('config', {}),
    }
    
    # Set timestamps based on status
    if status in ['in_progress', 'completed', 'failed', 'cancelled']:
        job_data['start_time'] = created_at + timedelta(seconds=5)
        job_data['updated_at'] = job_data['start_time']
    
    if status in ['completed', 'failed', 'cancelled']:
        job_data['end_time'] = job_data['start_time'] + timedelta(minutes=2)
        job_data['updated_at'] = job_data['end_time']
    
    if status == 'failed':
        job_data['error_message'] = kwargs.get('error_message', 'External API error occurred')
    
    # Merge any additional kwargs
    job_data.update(kwargs)
    
    return job_data


def seed_extraction_results(
    job_id: str,
    records: List[Dict[str, Any]] = None,
    count: int = 10,
    record_type: str = 'contacts'
) -> List[Dict[str, Any]]:
    """
    Create extraction results for a job.
    
    Args:
        job_id: ID of the job these results belong to
        records: Optional list of record dictionaries (generates if not provided)
        count: Number of records to generate if records not provided
        record_type: Type of records to generate ('contacts', 'users', 'mixed')
        
    Returns:
        List of extraction result dictionaries
    """
    if records is None:
        records = generate_sample_records(count, record_type)
    
    results = []
    for record in records:
        result_data = {
            'id': str(uuid.uuid4()),
            'job_id': job_id,
            'data': record,
            'created_at': datetime.utcnow(),
        }
        results.append(result_data)
    
    return results


def seed_multiple_jobs(
    count: int = 5,
    status_distribution: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    Create multiple jobs with various statuses.
    
    Args:
        count: Total number of jobs to create
        status_distribution: Dictionary mapping status to count
                            e.g., {'completed': 3, 'pending': 2}
                            If None, creates random distribution
        
    Returns:
        List of job data dictionaries
    """
    if status_distribution is None:
        # Default distribution
        status_distribution = {
            'completed': max(1, count // 2),
            'pending': max(1, count // 4),
            'in_progress': max(1, count // 8),
            'failed': max(1, count // 8),
        }
    
    jobs = []
    job_index = 0
    
    for status, status_count in status_distribution.items():
        for i in range(status_count):
            record_count = 50 if status == 'completed' else 0
            job = seed_job(
                status=status,
                record_count=record_count,
                created_minutes_ago=10 + job_index * 5,
                name=f"test_job_{status}_{i}"
            )
            jobs.append(job)
            job_index += 1
    
    return jobs


def create_sample_records(count: int, record_type: str = 'contacts') -> List[Dict[str, Any]]:
    """
    Generate sample extracted records.
    
    Args:
        count: Number of records to generate
        record_type: Type of records ('contacts', 'users', 'mixed')
        
    Returns:
        List of record dictionaries with required fields
    """
    return generate_sample_records(count, record_type)


class TestDataFactory:
    """
    Factory class for creating test data with related jobs and results.
    
    Useful for creating complex test scenarios with multiple related objects.
    """
    
    def __init__(self):
        """Initialize the factory."""
        self.created_jobs = []
        self.created_results = []
    
    def create_job_with_results(
        self,
        status: str = 'completed',
        result_count: int = 10,
        **job_kwargs
    ) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Create a job along with its extraction results.
        
        Args:
            status: Job status
            result_count: Number of results to create
            **job_kwargs: Additional job attributes
            
        Returns:
            Tuple of (job_data, results_list)
        """
        job_data = seed_job(status=status, record_count=result_count, **job_kwargs)
        self.created_jobs.append(job_data)
        
        results = []
        if status == 'completed' and result_count > 0:
            results = seed_extraction_results(
                job_id=job_data['id'],
                count=result_count
            )
            self.created_results.extend(results)
        
        return job_data, results
    
    def create_complete_workflow(self) -> Dict[str, Any]:
        """
        Create a complete set of test data representing various workflow states.
        
        Returns:
            Dictionary with categorized jobs and results
        """
        # Create jobs in different states
        pending_job, _ = self.create_job_with_results(status='pending', result_count=0)
        in_progress_job, _ = self.create_job_with_results(status='in_progress', result_count=0)
        completed_job, completed_results = self.create_job_with_results(
            status='completed',
            result_count=25
        )
        failed_job, _ = self.create_job_with_results(
            status='failed',
            result_count=0,
            error_message='Connection timeout to external API'
        )
        cancelled_job, _ = self.create_job_with_results(status='cancelled', result_count=0)
        
        return {
            'jobs': {
                'pending': pending_job,
                'in_progress': in_progress_job,
                'completed': completed_job,
                'failed': failed_job,
                'cancelled': cancelled_job,
            },
            'results': {
                'completed': completed_results,
            },
            'all_jobs': self.created_jobs,
            'all_results': self.created_results,
        }
    
    def reset(self):
        """Clear all created test data references."""
        self.created_jobs = []
        self.created_results = []


def clear_test_data():
    """
    Placeholder for clearing test database.
    
    This should be implemented based on the actual Django models
    and database setup in the real service.
    
    Example implementation:
        from django.contrib.contenttypes.models import ContentType
        from myapp.models import Job, ExtractionResult
        
        Job.objects.all().delete()
        ExtractionResult.objects.all().delete()
    """
    pass


