"""
Test helper functions for API testing.

Provides utility functions for creating test data, making API requests,
and performing common test operations.
"""
from typing import Dict, Any, Optional
import json
import time


def create_test_job(status: str, **kwargs) -> Dict[str, Any]:
    """
    Helper to create test job data.
    
    This is a convenience wrapper around seed_job for use in tests.
    
    Args:
        status: Job status
        **kwargs: Additional job attributes
        
    Returns:
        Dictionary with job data
    """
    from tests.fixtures.seed_data import seed_job
    return seed_job(status=status, **kwargs)


def create_test_results(job_id: str, count: int = 10, **kwargs) -> list:
    """
    Helper to create test extraction results.
    
    Args:
        job_id: ID of the job
        count: Number of results to create
        **kwargs: Additional parameters
        
    Returns:
        List of extraction result dictionaries
    """
    from tests.fixtures.seed_data import seed_extraction_results
    return seed_extraction_results(job_id=job_id, count=count, **kwargs)


def make_api_request(
    client,
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    **kwargs
):
    """
    Make an API request using Django test client.
    
    Args:
        client: Django test client
        method: HTTP method ('GET', 'POST', 'PUT', 'DELETE', etc.)
        endpoint: API endpoint URL
        data: Request body data
        headers: Request headers
        **kwargs: Additional arguments for the request
        
    Returns:
        Response object
    """
    method = method.upper()
    
    # Prepare headers
    if headers is None:
        headers = {}
    
    # Set content type for JSON requests
    if data is not None and 'content_type' not in kwargs:
        kwargs['content_type'] = 'application/json'
        if not isinstance(data, str):
            data = json.dumps(data)
    
    # Make the request
    if method == 'GET':
        return client.get(endpoint, **headers, **kwargs)
    elif method == 'POST':
        return client.post(endpoint, data=data, **headers, **kwargs)
    elif method == 'PUT':
        return client.put(endpoint, data=data, **headers, **kwargs)
    elif method == 'PATCH':
        return client.patch(endpoint, data=data, **headers, **kwargs)
    elif method == 'DELETE':
        return client.delete(endpoint, **headers, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")


def poll_until_status(
    client,
    job_id: str,
    expected_status: str,
    max_attempts: int = 30,
    interval: float = 1.0,
    status_endpoint_template: str = '/api/v1/scan/status/{job_id}'
) -> Dict[str, Any]:
    """
    Poll job status endpoint until desired status is reached or timeout.
    
    Args:
        client: Django test client
        job_id: ID of the job to poll
        expected_status: Status to wait for
        max_attempts: Maximum number of polling attempts
        interval: Time between polling attempts in seconds
        status_endpoint_template: URL template for status endpoint
        
    Returns:
        Final response data as dictionary
        
    Raises:
        TimeoutError: If max attempts reached without getting expected status
    """
    endpoint = status_endpoint_template.format(job_id=job_id)
    
    for attempt in range(max_attempts):
        response = client.get(endpoint)
        
        if response.status_code == 200:
            data = response.json()
            current_status = data.get('status')
            
            if current_status == expected_status:
                return data
            
            # If job failed, stop polling
            if current_status == 'failed':
                return data
        
        if attempt < max_attempts - 1:
            time.sleep(interval)
    
    raise TimeoutError(
        f"Job {job_id} did not reach status '{expected_status}' "
        f"after {max_attempts} attempts"
    )


def wait_for_job_completion(
    client,
    job_id: str,
    max_wait_seconds: int = 60,
    poll_interval: float = 2.0
) -> Dict[str, Any]:
    """
    Wait for a job to complete (or fail).
    
    Args:
        client: Django test client
        job_id: ID of the job
        max_wait_seconds: Maximum time to wait
        poll_interval: Time between polls
        
    Returns:
        Final job status data
        
    Raises:
        TimeoutError: If job doesn't complete within max_wait_seconds
    """
    max_attempts = int(max_wait_seconds / poll_interval)
    
    try:
        # First try to wait for completed status
        return poll_until_status(
            client,
            job_id,
            'completed',
            max_attempts=max_attempts,
            interval=poll_interval
        )
    except TimeoutError:
        # Check if it failed instead
        endpoint = f'/api/v1/scan/status/{job_id}'
        response = client.get(endpoint)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'failed':
                return data
        raise


def extract_json_response(response) -> Dict[str, Any]:
    """
    Extract JSON data from response.
    
    Args:
        response: Django test client response
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        ValueError: If response is not valid JSON
    """
    try:
        if hasattr(response, 'json'):
            return response.json()
        else:
            return json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f"Response is not valid JSON: {e}")


def get_response_field(response, field_path: str, default: Any = None) -> Any:
    """
    Get a field from response JSON using dot notation.
    
    Args:
        response: Django test client response
        field_path: Path to field (e.g., 'data.job_id' or 'status')
        default: Default value if field not found
        
    Returns:
        Field value or default
    """
    try:
        data = extract_json_response(response)
        
        # Navigate nested fields
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return default
            
            if current is None:
                return default
        
        return current
    except (ValueError, KeyError):
        return default


def create_api_token_header(token: str) -> Dict[str, str]:
    """
    Create headers dictionary with API token.
    
    Args:
        token: API token value
        
    Returns:
        Dictionary with authorization header
    """
    return {
        'HTTP_AUTHORIZATION': f'Bearer {token}',
        'HTTP_X_API_KEY': token,
    }


def format_endpoint(template: str, **params) -> str:
    """
    Format endpoint URL with parameters.
    
    Args:
        template: URL template (e.g., '/api/v1/jobs/{job_id}')
        **params: Parameters to substitute
        
    Returns:
        Formatted URL
    """
    return template.format(**params)


def assert_successful_response(response, expected_status: int = 200):
    """
    Quick assertion that response is successful.
    
    Args:
        response: Django test client response
        expected_status: Expected status code (default 200)
        
    Raises:
        AssertionError: If response is not successful
    """
    from tests.utils.assertions import assert_http_status
    assert_http_status(response, expected_status)


def get_pagination_info(response) -> Dict[str, Any]:
    """
    Extract pagination information from response.
    
    Args:
        response: Django test client response
        
    Returns:
        Dictionary with pagination info (page, per_page, total, has_more, etc.)
    """
    data = extract_json_response(response)
    
    # Try different pagination field names
    if 'pagination' in data:
        return data['pagination']
    
    # Build from top-level fields
    pagination = {}
    for field in ['page', 'per_page', 'count', 'total', 'next', 'previous', 'has_more']:
        if field in data:
            pagination[field] = data[field]
    
    return pagination


def calculate_expected_pages(total_count: int, per_page: int) -> int:
    """
    Calculate expected number of pages for pagination.
    
    Args:
        total_count: Total number of items
        per_page: Items per page
        
    Returns:
        Number of pages
    """
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    
    return (total_count + per_page - 1) // per_page


def build_query_params(**params) -> str:
    """
    Build query string from parameters.
    
    Args:
        **params: Query parameters
        
    Returns:
        Query string (e.g., '?page=1&limit=10')
    """
    if not params:
        return ''
    
    from urllib.parse import urlencode
    return '?' + urlencode(params)


class APITestContext:
    """
    Context manager for API tests with automatic cleanup.
    
    Usage:
        with APITestContext(client) as ctx:
            job_id = ctx.create_job_and_get_id(...)
            # Test operations
            # Cleanup happens automatically
    """
    
    def __init__(self, client):
        """Initialize context with Django test client."""
        self.client = client
        self.created_job_ids = []
        self.cleanup_handlers = []
    
    def __enter__(self):
        """Enter context."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and perform cleanup."""
        self.cleanup()
        return False
    
    def create_job_and_get_id(self, data: Dict[str, Any]) -> str:
        """
        Create a job via API and track it for cleanup.
        
        Args:
            data: Job creation data
            
        Returns:
            Created job ID
        """
        response = self.client.post(
            '/api/v1/scan/start',
            data=json.dumps(data),
            content_type='application/json'
        )
        
        job_id = get_response_field(response, 'job_id')
        if job_id:
            self.created_job_ids.append(job_id)
        
        return job_id
    
    def register_cleanup(self, handler, *args, **kwargs):
        """
        Register a cleanup handler to be called on exit.
        
        Args:
            handler: Callable to execute during cleanup
            *args: Arguments for handler
            **kwargs: Keyword arguments for handler
        """
        self.cleanup_handlers.append((handler, args, kwargs))
    
    def cleanup(self):
        """Perform all cleanup operations."""
        # Remove created jobs
        for job_id in self.created_job_ids:
            try:
                self.client.delete(f'/api/v1/scan/remove/{job_id}')
            except Exception:
                pass  # Ignore cleanup errors
        
        # Execute registered cleanup handlers
        for handler, args, kwargs in self.cleanup_handlers:
            try:
                handler(*args, **kwargs)
            except Exception:
                pass  # Ignore cleanup errors


