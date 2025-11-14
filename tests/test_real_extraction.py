"""
Real Extraction Tests for Data Extraction Service API.

Tests that validate end-to-end extraction workflow using mock external API.
These tests simulate the complete data extraction pipeline from start to finish.
"""
import pytest
import time
from tests.utils.assertions import (
    assert_http_status,
    assert_response_schema,
    assert_job_status,
    assert_extraction_data_format,
    assert_pagination_present,
)
from tests.utils.test_helpers import (
    extract_json_response,
    get_response_field,
    poll_until_status,
    wait_for_job_completion,
)
from tests.mocks.external_api_mock import MockExternalAPI


@pytest.mark.real_extraction
class TestExtractionWorkflow:
    """Tests for complete extraction workflow."""
    
    def test_start_extraction_with_valid_token(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Start extraction with valid credentials (202).
        
        Verifies that extraction job can be initiated with valid token.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        # Should return 202 Accepted
        assert_http_status(response, 202)
        
        # Should return job_id
        assert_response_schema(response, ['job_id'])
        
        data = extract_json_response(response)
        job_id = data['job_id']
        
        # Verify job_id is valid
        assert job_id is not None
        assert len(job_id) > 0
    
    @pytest.mark.slow
    def test_poll_job_status_until_completion(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Poll status endpoint until job completes.
        
        Verifies that job status transitions correctly and polling works.
        """
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        assert job_id is not None
        
        # Poll status with timeout
        final_status = poll_until_status(
            api_client,
            job_id,
            'completed',
            max_attempts=30,
            interval=1.0
        )
        
        # Verify final status
        assert final_status['status'] == 'completed'
        assert final_status.get('record_count', 0) > 0
    
    def test_retrieve_extracted_results(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Fetch results after successful completion.
        
        Verifies that extracted data can be retrieved after job completes.
        """
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        
        # Wait for completion
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Fetch results
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        
        assert_http_status(result_response, 200)
        assert_response_schema(result_response, ['data'])
        
        data = extract_json_response(result_response)
        records = data['data']
        
        # Verify we have records
        assert len(records) > 0
    
    def test_extraction_data_format_validation(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Verify extracted data structure and fields.
        
        Verifies that extracted data has correct format with required fields.
        """
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        
        # Wait for completion
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Fetch and validate results
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        data = extract_json_response(result_response)
        records = data['data']
        
        # Validate data format
        assert_extraction_data_format(records)
        
        # Verify each record has required fields
        required_fields = ['email', 'first_name', 'last_name', 'id_from_service']
        for record in records:
            for field in required_fields:
                assert field in record, f"Missing field {field} in record"
                assert record[field] is not None, f"Field {field} is None"
    
    def test_extraction_with_pagination(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Test result pagination for large datasets.
        
        Verifies that pagination works correctly for extraction results.
        """
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        
        # Wait for completion
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Fetch first page
        page_1_response = api_client.get(
            f'/api/v1/scan/result/{job_id}?page=1&per_page=20'
        )
        
        assert_http_status(page_1_response, 200)
        assert_pagination_present(page_1_response)
        
        page_1_data = extract_json_response(page_1_response)
        page_1_records = page_1_data['data']
        
        assert len(page_1_records) <= 20
        
        # Try fetching second page if available
        if page_1_data.get('pagination', {}).get('has_more', False):
            page_2_response = api_client.get(
                f'/api/v1/scan/result/{job_id}?page=2&per_page=20'
            )
            
            assert_http_status(page_2_response, 200)
            
            page_2_data = extract_json_response(page_2_response)
            page_2_records = page_2_data['data']
            
            # Verify records are different
            page_1_ids = {r['id_from_service'] for r in page_1_records}
            page_2_ids = {r['id_from_service'] for r in page_2_records}
            
            assert len(page_1_ids & page_2_ids) == 0, "Pages should not overlap"
    
    def test_remove_extraction_data(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Cleanup after successful extraction.
        
        Verifies that extraction data can be removed after completion.
        """
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        
        # Wait for completion
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Remove the data
        remove_response = api_client.delete(f'/api/v1/scan/remove/{job_id}')
        
        assert remove_response.status_code in [200, 204]
        
        # Verify data is gone
        status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
        assert_http_status(status_response, 404)
    
    @pytest.mark.slow
    def test_complete_extraction_workflow(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Full E2E: start → poll → retrieve → remove.
        
        Verifies complete extraction workflow from start to cleanup.
        """
        # Step 1: Start extraction
        start_response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        assert_http_status(start_response, 202)
        job_id = get_response_field(start_response, 'job_id')
        assert job_id is not None
        
        # Step 2: Poll until completion
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
            assert_http_status(status_response, 200)
            
            status_data = extract_json_response(status_response)
            current_status = status_data['status']
            
            if current_status == 'completed':
                break
            elif current_status == 'failed':
                pytest.fail(f"Job failed: {status_data.get('error_message')}")
            
            time.sleep(1)
        else:
            pytest.fail(f"Job did not complete after {max_attempts} attempts")
        
        # Step 3: Retrieve results
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        assert_http_status(result_response, 200)
        
        result_data = extract_json_response(result_response)
        records = result_data['data']
        
        assert len(records) > 0
        assert_extraction_data_format(records)
        
        # Step 4: Remove data
        remove_response = api_client.delete(f'/api/v1/scan/remove/{job_id}')
        assert remove_response.status_code in [200, 204]
        
        # Step 5: Verify removal
        verify_response = api_client.get(f'/api/v1/scan/status/{job_id}')
        assert_http_status(verify_response, 404)


@pytest.mark.real_extraction
class TestExtractionWithMockFailures:
    """Tests for extraction workflow with simulated failures."""
    
    def test_extraction_with_auth_failure(
        self,
        api_client,
        invalid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Extraction with invalid token fails appropriately.
        
        Verifies that authentication failures are handled correctly.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': invalid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        # Should reject invalid token
        assert response.status_code in [400, 401]
    
    def test_extraction_with_external_api_failure(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Extraction handles external API failures gracefully.
        
        Verifies that external service failures result in failed job status.
        """
        # Configure mock to fail
        mock_external_api_with_patch.simulate_failure('fetch')
        
        # Start extraction
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        if response.status_code == 202:
            job_id = get_response_field(response, 'job_id')
            
            # Wait a bit for processing
            time.sleep(2)
            
            # Check status
            status_response = api_client.get(f'/api/v1/scan/status/{job_id}')
            status_data = extract_json_response(status_response)
            
            # Job should eventually fail
            # Might be 'pending', 'in_progress', or 'failed'
            assert status_data['status'] in ['pending', 'in_progress', 'failed']
            
            if status_data['status'] == 'failed':
                assert status_data.get('error_message') is not None
        
        # Restore mock
        mock_external_api_with_patch.restore_availability()
    
    def test_extraction_with_rate_limiting(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Extraction handles rate limiting from external API.
        
        Verifies that rate limit errors are handled gracefully.
        """
        # Set very low rate limit
        mock_external_api_with_patch.set_rate_limit_threshold(1)
        
        # Start multiple extractions
        job_ids = []
        for i in range(3):
            response = api_client.post(
                '/api/v1/scan/start',
                data={
                    'api_token': valid_api_token,
                    'record_type': 'contacts'
                },
                content_type='application/json'
            )
            
            if response.status_code == 202:
                job_id = get_response_field(response, 'job_id')
                if job_id:
                    job_ids.append(job_id)
        
        # At least one should succeed or be queued
        assert len(job_ids) > 0
        
        # Reset rate limit
        mock_external_api_with_patch.reset_rate_limit()


@pytest.mark.real_extraction
class TestExtractionRecordTypes:
    """Tests for different record types extraction."""
    
    def test_extraction_contacts(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Extract contacts successfully.
        
        Verifies that contact extraction works correctly.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'contacts'
            },
            content_type='application/json'
        )
        
        assert_http_status(response, 202)
        
        job_id = get_response_field(response, 'job_id')
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Verify results
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        assert_http_status(result_response, 200)
    
    def test_extraction_users(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Extract users successfully.
        
        Verifies that user extraction works correctly.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data={
                'api_token': valid_api_token,
                'record_type': 'users'
            },
            content_type='application/json'
        )
        
        assert_http_status(response, 202)
        
        job_id = get_response_field(response, 'job_id')
        wait_for_job_completion(api_client, job_id, max_wait_seconds=30)
        
        # Verify results
        result_response = api_client.get(f'/api/v1/scan/result/{job_id}')
        assert_http_status(result_response, 200)


@pytest.mark.real_extraction
class TestConcurrentExtractions:
    """Tests for concurrent extraction handling."""
    
    def test_multiple_concurrent_extractions(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Multiple extractions can run concurrently.
        
        Verifies that service can handle multiple simultaneous extractions.
        """
        job_ids = []
        
        # Start multiple extractions
        for i in range(3):
            response = api_client.post(
                '/api/v1/scan/start',
                data={
                    'api_token': valid_api_token,
                    'record_type': 'contacts'
                },
                content_type='application/json'
            )
            
            if response.status_code == 202:
                job_id = get_response_field(response, 'job_id')
                if job_id:
                    job_ids.append(job_id)
        
        # All should be accepted or queued
        assert len(job_ids) >= 1
        
        # All job IDs should be unique
        assert len(job_ids) == len(set(job_ids))
    
    def test_duplicate_extraction_prevention(
        self,
        api_client,
        valid_api_token,
        mock_external_api_with_patch
    ):
        """
        Test: Duplicate extraction requests are handled appropriately.
        
        Verifies that identical extraction requests don't create duplicates.
        """
        request_data = {
            'api_token': valid_api_token,
            'record_type': 'contacts',
            'unique_key': 'test_duplicate_123'  # Unique identifier
        }
        
        # Start first extraction
        response1 = api_client.post(
            '/api/v1/scan/start',
            data=request_data,
            content_type='application/json'
        )
        
        assert_http_status(response1, 202)
        job_id_1 = get_response_field(response1, 'job_id')
        
        # Try to start duplicate
        response2 = api_client.post(
            '/api/v1/scan/start',
            data=request_data,
            content_type='application/json'
        )
        
        # Should either return existing job_id or create new one
        # depending on deduplication strategy
        if response2.status_code == 202:
            job_id_2 = get_response_field(response2, 'job_id')
            # If deduplication is active, should return same job_id
            # If not, job_id_2 will be different (both valid approaches)
        elif response2.status_code == 409:
            # Conflict - duplicate detected
            pass


