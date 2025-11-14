"""
Mock external API service for testing.

Simulates third-party API behavior including authentication, data fetching,
rate limiting, and error scenarios.
"""
import time
from typing import Dict, Any, List, Optional
from unittest.mock import Mock
from .mock_data import generate_mock_extraction_response


class MockExternalAPIException(Exception):
    """Base exception for mock external API errors."""
    pass


class MockAuthenticationError(MockExternalAPIException):
    """Raised when authentication fails."""
    pass


class MockRateLimitError(MockExternalAPIException):
    """Raised when rate limit is exceeded."""
    pass


class MockServiceUnavailableError(MockExternalAPIException):
    """Raised when the external service is unavailable."""
    pass


class MockExternalAPI:
    """
    Mock external API service for testing.
    
    Simulates a third-party API with authentication, data fetching,
    pagination, rate limiting, and various error scenarios.
    """
    
    VALID_TEST_TOKENS = [
        'test_token_valid_12345',
        'valid_api_key_abc',
        'test_access_token_xyz'
    ]
    
    def __init__(self):
        """Initialize the mock API with default state."""
        self._is_available = True
        self._rate_limit_count = 0
        self._rate_limit_threshold = 100
        self._request_delay = 0  # Simulate network delay in seconds
        self._should_fail = False
        self._failure_reason = None
        
    def authenticate(self, token: str) -> bool:
        """
        Simulate authentication validation.
        
        Args:
            token: API token to validate
            
        Returns:
            True if authentication successful
            
        Raises:
            MockAuthenticationError: If token is invalid
            MockServiceUnavailableError: If service is unavailable
        """
        if not self._is_available:
            raise MockServiceUnavailableError("External API service is currently unavailable")
        
        if self._should_fail and self._failure_reason == 'auth':
            raise MockAuthenticationError("Authentication failed: Service error")
        
        # Simulate processing time
        if self._request_delay:
            time.sleep(self._request_delay)
        
        # Check if token is valid
        if not token or token.strip() == '':
            raise MockAuthenticationError("Empty or missing API token")
        
        if token not in self.VALID_TEST_TOKENS:
            raise MockAuthenticationError(f"Invalid API token: {token}")
        
        return True
    
    def fetch_data(
        self,
        token: str,
        record_type: str = 'contacts',
        page: int = 1,
        per_page: int = 100,
        **params
    ) -> Dict[str, Any]:
        """
        Simulate data fetching with realistic responses.
        
        Args:
            token: Valid API token
            record_type: Type of records to fetch ('contacts' or 'users')
            page: Page number for pagination
            per_page: Number of records per page
            **params: Additional query parameters
            
        Returns:
            Dictionary containing fetched data and pagination info
            
        Raises:
            MockAuthenticationError: If authentication fails
            MockRateLimitError: If rate limit exceeded
            MockServiceUnavailableError: If service unavailable
        """
        # Check authentication first
        self.authenticate(token)
        
        # Check rate limiting
        self._rate_limit_count += 1
        if self._rate_limit_count > self._rate_limit_threshold:
            raise MockRateLimitError("Rate limit exceeded. Please try again later.")
        
        # Check if service should fail
        if self._should_fail and self._failure_reason == 'fetch':
            raise MockServiceUnavailableError("Failed to fetch data from external service")
        
        # Simulate processing time
        if self._request_delay:
            time.sleep(self._request_delay)
        
        # Determine if there are more pages
        has_more = page < 3  # Simulate 3 pages of data
        
        # Generate mock response
        response = generate_mock_extraction_response(
            record_type=record_type,
            count=per_page,
            page=page,
            per_page=per_page,
            has_more=has_more
        )
        
        return response
    
    def fetch_all_data(
        self,
        token: str,
        record_type: str = 'contacts',
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch all data across multiple pages.
        
        Args:
            token: Valid API token
            record_type: Type of records to fetch
            max_pages: Maximum number of pages to fetch
            
        Returns:
            List of all fetched records
        """
        all_records = []
        page = 1
        
        while page <= max_pages:
            response = self.fetch_data(token, record_type, page=page)
            all_records.extend(response['data'])
            
            if not response['pagination']['has_more']:
                break
            
            page += 1
        
        return all_records
    
    def simulate_failure(self, reason: str = 'fetch'):
        """
        Configure the mock API to simulate failure scenarios.
        
        Args:
            reason: Type of failure ('auth', 'fetch', 'unavailable')
        """
        self._should_fail = True
        self._failure_reason = reason
        if reason == 'unavailable':
            self._is_available = False
    
    def restore_availability(self):
        """Restore the mock API to normal operation."""
        self._should_fail = False
        self._failure_reason = None
        self._is_available = True
    
    def set_request_delay(self, delay: float):
        """
        Set artificial delay for requests (simulates network latency).
        
        Args:
            delay: Delay in seconds
        """
        self._request_delay = delay
    
    def reset_rate_limit(self):
        """Reset the rate limit counter."""
        self._rate_limit_count = 0
    
    def set_rate_limit_threshold(self, threshold: int):
        """
        Set the rate limit threshold.
        
        Args:
            threshold: Maximum number of requests allowed
        """
        self._rate_limit_threshold = threshold
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get information about the mock API state.
        
        Returns:
            Dictionary with API state information
        """
        return {
            'is_available': self._is_available,
            'rate_limit_count': self._rate_limit_count,
            'rate_limit_threshold': self._rate_limit_threshold,
            'request_delay': self._request_delay,
            'should_fail': self._should_fail,
            'failure_reason': self._failure_reason,
        }


def create_mock_external_api() -> MockExternalAPI:
    """
    Factory function to create a fresh mock external API instance.
    
    Returns:
        New MockExternalAPI instance with default settings
    """
    return MockExternalAPI()


