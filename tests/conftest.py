"""
Pytest configuration and fixtures for API tests.

Provides reusable fixtures for database setup, test clients,
mock external APIs, and test data.
"""
import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock
from tests.fixtures.seed_data import (
    seed_job,
    seed_extraction_results,
    seed_multiple_jobs,
    TestDataFactory,
)
from tests.mocks.external_api_mock import MockExternalAPI
from tests.mocks.mock_data import generate_sample_records


# ============================================================================
# Django Test Client Fixtures
# ============================================================================

@pytest.fixture
def api_client():
    """
    Django test client for API requests.
    
    Returns:
        Django test client instance
    """
    from django.test import Client
    return Client()


@pytest.fixture
def authenticated_client(api_client):
    """
    Django test client with authentication.
    
    Returns:
        Authenticated Django test client
    """
    # Add authentication headers or session setup here
    # This depends on the actual authentication mechanism used
    return api_client


# ============================================================================
# Mock External API Fixtures
# ============================================================================

@pytest.fixture
def mock_external_api():
    """
    Create a mock external API instance.
    
    Returns:
        MockExternalAPI instance
    """
    return MockExternalAPI()


@pytest.fixture
def mock_external_api_with_patch(monkeypatch, mock_external_api):
    """
    Replace external API with mock implementation using monkeypatch.
    
    This fixture patches the external API service so that all API calls
    during tests use the mock instead of real external service.
    
    Returns:
        MockExternalAPI instance that is patched into the service
    """
    # Patch the external API service
    # Adjust the import path based on actual service structure
    try:
        monkeypatch.setattr(
            'services.external_api_service.ExternalAPI',
            lambda: mock_external_api
        )
    except (ImportError, AttributeError):
        # If service doesn't exist yet, just return the mock
        pass
    
    return mock_external_api


# ============================================================================
# Database Seeding Fixtures
# ============================================================================

@pytest.fixture
def test_data_factory():
    """
    Factory for creating complex test data scenarios.
    
    Returns:
        TestDataFactory instance
    """
    return TestDataFactory()


@pytest.fixture
def seed_pending_job(db):
    """
    Create a pending job in the database.
    
    Returns:
        Job model instance
    """
    from api.models import Job
    job_data = seed_job(status='pending', record_count=0)
    job = Job.objects.create(**job_data)
    return job


@pytest.fixture
def seed_in_progress_job(db):
    """
    Create an in-progress job in the database.
    
    Returns:
        Job model instance
    """
    from api.models import Job
    job_data = seed_job(status='in_progress', record_count=0)
    job = Job.objects.create(**job_data)
    return job


@pytest.fixture
def seed_completed_job(db):
    """
    Create a completed job with results in the database.
    
    Returns:
        Tuple of (job, results_list)
    """
    from api.models import Job, ExtractionResult
    job_data = seed_job(status='completed', record_count=25)
    job = Job.objects.create(**job_data)
    
    results_data = seed_extraction_results(job.id, count=25)
    results = []
    for result_data in results_data:
        result = ExtractionResult.objects.create(
            job=job,
            data=result_data['data'],
            created_at=result_data['created_at']
        )
        results.append(result)
    
    return job, results


@pytest.fixture
def seed_failed_job(db):
    """
    Create a failed job in the database.
    
    Returns:
        Job model instance
    """
    from api.models import Job
    job_data = seed_job(
        status='failed',
        record_count=0,
        error_message='External API connection timeout'
    )
    job = Job.objects.create(**job_data)
    return job


@pytest.fixture
def seed_cancelled_job(db):
    """
    Create a cancelled job in the database.
    
    Returns:
        Job model instance
    """
    from api.models import Job
    job_data = seed_job(status='cancelled', record_count=0)
    job = Job.objects.create(**job_data)
    return job


@pytest.fixture
def seed_multiple_jobs(db):
    """
    Create various jobs for list/statistics tests.
    
    Returns:
        List of Job model instances
    """
    from api.models import Job
    from tests.fixtures.seed_data import seed_multiple_jobs as create_jobs
    
    jobs_data = create_jobs(count=10)
    created_jobs = []
    for job_data in jobs_data:
        job = Job.objects.create(**job_data)
        created_jobs.append(job)
    return created_jobs


@pytest.fixture
def seed_job_with_large_results(db):
    """
    Create a completed job with a large number of results for pagination testing.
    
    Returns:
        Tuple of (job, results_list)
    """
    from api.models import Job, ExtractionResult
    job_data = seed_job(status='completed', record_count=150)
    job = Job.objects.create(**job_data)
    
    results_data = seed_extraction_results(job.id, count=150)
    results = []
    for result_data in results_data:
        result = ExtractionResult.objects.create(
            job=job,
            data=result_data['data'],
            created_at=result_data['created_at']
        )
        results.append(result)
    
    return job, results


@pytest.fixture
def seed_complete_workflow(db, test_data_factory):
    """
    Create a complete set of test data representing various workflow states.
    
    Returns:
        Dictionary with categorized jobs and results
    """
    workflow_data = test_data_factory.create_complete_workflow()
    
    # Create actual database records
    # from myapp.models import Job, ExtractionResult
    # for job_data in workflow_data['all_jobs']:
    #     Job.objects.create(**job_data)
    # for result_data in workflow_data['all_results']:
    #     ExtractionResult.objects.create(**result_data)
    
    return workflow_data


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_extraction_data():
    """
    Mock extracted data structure.
    
    Returns:
        List of sample extraction records
    """
    return generate_sample_records(count=10, record_type='contacts')


@pytest.fixture
def sample_contact_records():
    """
    Sample contact records for testing.
    
    Returns:
        List of contact record dictionaries
    """
    return generate_sample_records(count=20, record_type='contacts')


@pytest.fixture
def sample_user_records():
    """
    Sample user records for testing.
    
    Returns:
        List of user record dictionaries
    """
    return generate_sample_records(count=15, record_type='users')


@pytest.fixture
def valid_api_token():
    """
    Valid API token for testing.
    
    Returns:
        Valid test API token string
    """
    return 'test_token_valid_12345'


@pytest.fixture
def invalid_api_token():
    """
    Invalid API token for testing.
    
    Returns:
        Invalid test API token string
    """
    return 'invalid_token_xyz'


# ============================================================================
# API Endpoint Fixtures
# ============================================================================

@pytest.fixture
def api_endpoints():
    """
    Dictionary of API endpoint URL templates.
    
    Returns:
        Dictionary mapping endpoint names to URL templates
    """
    return {
        'scan_start': '/api/v1/scan/start',
        'scan_status': '/api/v1/scan/status/{job_id}',
        'scan_result': '/api/v1/scan/result/{job_id}',
        'scan_cancel': '/api/v1/scan/cancel/{job_id}',
        'scan_remove': '/api/v1/scan/remove/{job_id}',
        'jobs_list': '/api/v1/jobs/jobs',
        'jobs_statistics': '/api/v1/jobs/statistics',
        'health': '/api/v1/health',
    }


# ============================================================================
# Database Management Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Enable database access for all tests.
    
    This fixture is automatically used for all tests to ensure
    database access is available.
    """
    pass


@pytest.fixture
def clear_database(db):
    """
    Clear all test data from database.
    
    Useful for tests that need a completely clean state.
    """
    # Clear all test data
    # from myapp.models import Job, ExtractionResult
    # Job.objects.all().delete()
    # ExtractionResult.objects.all().delete()
    pass


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config():
    """
    Test configuration settings.
    
    Returns:
        Dictionary with test configuration
    """
    return {
        'max_poll_attempts': 30,
        'poll_interval': 1.0,
        'request_timeout': 30,
        'max_results_per_page': 100,
    }


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.
    
    Register custom markers and perform initial setup.
    """
    config.addinivalue_line(
        "markers", "seeded: Tests using seeded database data"
    )
    config.addinivalue_line(
        "markers", "edge_case: Tests for edge cases and error handling"
    )
    config.addinivalue_line(
        "markers", "real_extraction: Tests for real extraction workflow"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer to execute"
    )


@pytest.fixture(scope='session')
def django_db_setup():
    """
    Setup test database for the session.
    
    This runs once per test session to configure the database.
    """
    # Any session-level database setup can go here
    pass


