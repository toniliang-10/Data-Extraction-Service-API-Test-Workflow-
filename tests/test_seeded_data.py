"""
Seeded Data Tests for Data Extraction Service API.

Tests that validate core API behavior using pre-populated database entries.
This approach removes external dependencies for rapid, controlled testing.
"""
import pytest
from tests.utils.assertions import (
    assert_http_status,
    assert_response_schema,
    assert_job_status,
    assert_pagination_present,
    assert_extraction_data_format,
)
from tests.utils.test_helpers import (
    make_api_request,
    extract_json_response,
    get_response_field,
)


@pytest.mark.seeded
class TestJobStatus:
    """Tests for job status endpoint using seeded data."""
    
    def test_verify_job_status_pending(self, api_client, seed_pending_job):
        """
        Test: Query status for seeded pending job.
        
        Verifies that the status endpoint returns correct information
        for a pending job.
        """
        job_id = seed_pending_job.id
        response = api_client.get(f'/api/v1/scan/status/{job_id}')
        
        # Assert response status
        assert_http_status(response, 200)
        
        # Assert response structure
        assert_response_schema(response, ['id', 'status'])
        
        # Assert job status
        assert_job_status(response, 'pending')
        
        # Verify additional fields
        data = extract_json_response(response)
        assert data['id'] == str(job_id)
        assert data.get('record_count') == 0
        assert 'created_at' in data
    
    def test_verify_job_status_completed(self, api_client, seed_completed_job):
        """
        Test: Query status for seeded completed job.
        
        Verifies that the status endpoint returns correct information
        for a completed job including record count and timestamps.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/status/{job_id}')
        
        # Assert response status
        assert_http_status(response, 200)
        
        # Assert response structure
        assert_response_schema(response, [
            'id', 'status', 'record_count', 'created_at', 'start_time', 'end_time'
        ])
        
        # Assert job status
        assert_job_status(response, 'completed')
        
        # Verify completion details
        data = extract_json_response(response)
        assert data['id'] == job_id
        assert data['record_count'] == 25
        assert data['start_time'] is not None
        assert data['end_time'] is not None
    
    def test_verify_job_status_in_progress(self, api_client, seed_in_progress_job):
        """
        Test: Query status for seeded in-progress job.
        
        Verifies that in-progress jobs show correct status and timestamps.
        """
        job_id = seed_in_progress_job['id']
        response = api_client.get(f'/api/v1/scan/status/{job_id}')
        
        assert_http_status(response, 200)
        assert_job_status(response, 'in_progress')
        
        data = extract_json_response(response)
        assert data['start_time'] is not None
        assert data.get('end_time') is None  # Should not have end time yet
    
    def test_verify_job_status_failed(self, api_client, seed_failed_job):
        """
        Test: Query status for seeded failed job.
        
        Verifies that failed jobs include error information.
        """
        job_id = seed_failed_job['id']
        response = api_client.get(f'/api/v1/scan/status/{job_id}')
        
        assert_http_status(response, 200)
        assert_job_status(response, 'failed')
        
        data = extract_json_response(response)
        assert data.get('error_message') is not None
        assert len(data['error_message']) > 0
    
    def test_verify_job_status_cancelled(self, api_client, seed_cancelled_job):
        """
        Test: Query status for seeded cancelled job.
        
        Verifies that cancelled jobs show correct status.
        """
        job_id = seed_cancelled_job['id']
        response = api_client.get(f'/api/v1/scan/status/{job_id}')
        
        assert_http_status(response, 200)
        assert_job_status(response, 'cancelled')


@pytest.mark.seeded
class TestExtractionResults:
    """Tests for extraction results endpoint using seeded data."""
    
    def test_fetch_extraction_results(self, api_client, seed_completed_job):
        """
        Test: Retrieve results for completed job.
        
        Verifies that extraction results can be fetched for a completed job
        and that the data has the correct structure.
        """
        job_data, results = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}')
        
        # Assert response status
        assert_http_status(response, 200)
        
        # Assert response structure
        assert_response_schema(response, ['data'])
        
        # Verify data
        data = extract_json_response(response)
        records = data['data']
        
        # Verify record count
        assert len(records) > 0
        assert len(records) <= 25
        
        # Verify data format
        assert_extraction_data_format(records)
    
    def test_fetch_results_with_pagination(self, api_client, seed_job_with_large_results):
        """
        Test: Test pagination on large result sets.
        
        Verifies that pagination works correctly for jobs with many results.
        """
        job_data, results = seed_job_with_large_results
        job_id = job_data['id']
        
        # Fetch first page
        response = api_client.get(f'/api/v1/scan/result/{job_id}?page=1&per_page=50')
        
        assert_http_status(response, 200)
        assert_pagination_present(response)
        
        data = extract_json_response(response)
        page_1_records = data['data']
        
        # Verify first page has correct number of records
        assert len(page_1_records) == 50
        
        # Fetch second page
        response = api_client.get(f'/api/v1/scan/result/{job_id}?page=2&per_page=50')
        
        assert_http_status(response, 200)
        
        data = extract_json_response(response)
        page_2_records = data['data']
        
        # Verify second page has remaining records
        assert len(page_2_records) > 0
        
        # Verify records are different between pages
        page_1_ids = [r['id_from_service'] for r in page_1_records]
        page_2_ids = [r['id_from_service'] for r in page_2_records]
        assert len(set(page_1_ids) & set(page_2_ids)) == 0  # No overlap
    
    def test_fetch_results_empty_job(self, api_client, seed_completed_job):
        """
        Test: Fetch results for a job with zero records.
        
        Verifies that the API handles jobs with no extracted data gracefully.
        """
        # Create a completed job with zero results
        from tests.fixtures.seed_data import seed_job
        job_data = seed_job(status='completed', record_count=0)
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}')
        
        assert_http_status(response, 200)
        
        data = extract_json_response(response)
        assert data['data'] == [] or len(data['data']) == 0


@pytest.mark.seeded
class TestJobsList:
    """Tests for jobs list endpoint using seeded data."""
    
    def test_list_all_jobs(self, api_client, seed_multiple_jobs):
        """
        Test: Verify all seeded jobs appear in list.
        
        Verifies that the jobs list endpoint returns all jobs.
        """
        response = api_client.get('/api/v1/jobs/jobs')
        
        assert_http_status(response, 200)
        assert_response_schema(response, ['jobs'])
        
        data = extract_json_response(response)
        jobs = data['jobs']
        
        # Verify we have jobs
        assert len(jobs) > 0
        
        # Verify job structure
        for job in jobs:
            assert 'id' in job
            assert 'status' in job
            assert 'created_at' in job
    
    def test_list_jobs_with_pagination(self, api_client, seed_multiple_jobs):
        """
        Test: Test job list pagination.
        
        Verifies that pagination works correctly for the jobs list.
        """
        # Fetch first page
        response = api_client.get('/api/v1/jobs/jobs?page=1&per_page=5')
        
        assert_http_status(response, 200)
        assert_pagination_present(response)
        
        data = extract_json_response(response)
        page_1_jobs = data['jobs']
        
        assert len(page_1_jobs) <= 5
    
    def test_list_jobs_filter_by_status(self, api_client, seed_multiple_jobs):
        """
        Test: Filter jobs by status.
        
        Verifies that jobs can be filtered by their status.
        """
        response = api_client.get('/api/v1/jobs/jobs?status=completed')
        
        assert_http_status(response, 200)
        
        data = extract_json_response(response)
        jobs = data['jobs']
        
        # All returned jobs should be completed
        for job in jobs:
            assert job['status'] == 'completed'


@pytest.mark.seeded
class TestJobStatistics:
    """Tests for job statistics endpoint using seeded data."""
    
    def test_retrieve_job_statistics(self, api_client, seed_multiple_jobs):
        """
        Test: Validate aggregated statistics.
        
        Verifies that the statistics endpoint returns accurate metrics.
        """
        response = api_client.get('/api/v1/jobs/statistics')
        
        assert_http_status(response, 200)
        assert_response_schema(response, ['total_jobs'])
        
        data = extract_json_response(response)
        
        # Verify statistics fields
        assert 'total_jobs' in data
        assert 'completed_jobs' in data or 'jobs_by_status' in data
        
        # Verify counts are non-negative
        assert data['total_jobs'] >= 0
        
        if 'completed_jobs' in data:
            assert data['completed_jobs'] >= 0
            assert data['completed_jobs'] <= data['total_jobs']
    
    def test_statistics_accuracy(self, api_client, seed_complete_workflow):
        """
        Test: Verify statistics match actual data.
        
        Creates known data set and verifies statistics are accurate.
        """
        workflow_data = seed_complete_workflow
        
        response = api_client.get('/api/v1/jobs/statistics')
        assert_http_status(response, 200)
        
        data = extract_json_response(response)
        
        # Count actual jobs from seeded data
        expected_total = len(workflow_data['all_jobs'])
        
        # Statistics should reflect seeded data
        assert data['total_jobs'] >= expected_total


@pytest.mark.seeded
class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self, api_client):
        """
        Test: Verify service health endpoint.
        
        Verifies that the health endpoint returns a healthy status.
        """
        response = api_client.get('/api/v1/health')
        
        assert_http_status(response, 200)
        assert_response_schema(response, ['status'])
        
        data = extract_json_response(response)
        assert data['status'] in ['ok', 'healthy', 'up']
    
    def test_health_check_includes_version(self, api_client):
        """
        Test: Health check includes version information.
        
        Verifies that health endpoint provides version details.
        """
        response = api_client.get('/api/v1/health')
        
        assert_http_status(response, 200)
        
        data = extract_json_response(response)
        # Version field is optional but recommended
        if 'version' in data:
            assert isinstance(data['version'], str)
            assert len(data['version']) > 0


@pytest.mark.seeded
class TestJobCancellation:
    """Tests for job cancellation endpoint using seeded data."""
    
    def test_cancel_pending_job(self, api_client, seed_pending_job):
        """
        Test: Cancel a pending job and verify status change.
        
        Verifies that a pending job can be cancelled and status updates correctly.
        """
        job_id = seed_pending_job['id']
        
        # Cancel the job
        response = api_client.post(f'/api/v1/scan/cancel/{job_id}')
        
        # Assert cancellation accepted
        assert_http_status(response, 200) or assert_http_status(response, 202)
        
        # Verify status changed to cancelled
        status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
        assert_http_status(status_response, 200)
        assert_job_status(status_response, 'cancelled')
    
    def test_cancel_in_progress_job(self, api_client, seed_in_progress_job):
        """
        Test: Cancel an in-progress job.
        
        Verifies that in-progress jobs can be cancelled.
        """
        job_id = seed_in_progress_job['id']
        
        response = api_client.post(f'/api/v1/scan/cancel/{job_id}')
        
        # Should accept cancellation
        assert response.status_code in [200, 202]
        
        # Verify status
        status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
        data = extract_json_response(status_response)
        
        # Status should be cancelled or still in_progress (if cancellation is async)
        assert data['status'] in ['cancelled', 'in_progress']


@pytest.mark.seeded
class TestJobRemoval:
    """Tests for job removal endpoint using seeded data."""
    
    def test_remove_job_data(self, api_client, seed_completed_job):
        """
        Test: Delete job data and verify removal.
        
        Verifies that job data can be deleted and is no longer accessible.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        # Remove the job
        response = api_client.delete(f'/api/v1/scan/remove/{job_id}')
        
        # Assert successful deletion
        assert response.status_code in [200, 204]
        
        # Verify job no longer exists
        status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
        assert_http_status(status_response, 404)
        
        # Verify results no longer accessible
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        assert_http_status(result_response, 404)
    
    def test_remove_cancelled_job(self, api_client, seed_cancelled_job):
        """
        Test: Remove a cancelled job.
        
        Verifies that cancelled jobs can be removed.
        """
        job_id = seed_cancelled_job['id']
        
        response = api_client.delete(f'/api/v1/scan/remove/{job_id}')
        
        assert response.status_code in [200, 204]
    
    def test_remove_failed_job(self, api_client, seed_failed_job):
        """
        Test: Remove a failed job.
        
        Verifies that failed jobs can be removed.
        """
        job_id = seed_failed_job['id']
        
        response = api_client.delete(f'/api/v1/scan/remove/{job_id}')
        
        assert response.status_code in [200, 204]


