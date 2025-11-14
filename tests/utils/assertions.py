"""
Common assertion utilities for API testing.

Provides reusable assertion functions for validating API responses,
status codes, schemas, and error messages.
"""
from typing import Dict, Any, List, Optional
import json


def assert_http_status(response, expected_status: int, message: str = None):
    """
    Assert that response has the expected HTTP status code.
    
    Args:
        response: Django test client response or requests response
        expected_status: Expected HTTP status code
        message: Optional custom error message
    """
    actual_status = response.status_code
    
    if actual_status != expected_status:
        # Try to get response body for debugging
        try:
            if hasattr(response, 'json'):
                body = response.json()
            else:
                body = json.loads(response.content)
            body_str = json.dumps(body, indent=2)
        except:
            body_str = str(response.content)
        
        error_msg = message or (
            f"Expected status code {expected_status}, got {actual_status}.\n"
            f"Response body: {body_str}"
        )
        raise AssertionError(error_msg)


def assert_response_schema(response, expected_fields: List[str], message: str = None):
    """
    Assert that response JSON contains all expected fields.
    
    Args:
        response: Django test client response
        expected_fields: List of field names that must be present
        message: Optional custom error message
    """
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise AssertionError(f"Response is not valid JSON: {e}")
    
    missing_fields = []
    for field in expected_fields:
        # Support nested field checking with dot notation
        if '.' in field:
            parts = field.split('.')
            current = data
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    missing_fields.append(field)
                    break
        else:
            if field not in data:
                missing_fields.append(field)
    
    if missing_fields:
        error_msg = message or (
            f"Response missing required fields: {missing_fields}.\n"
            f"Response data: {json.dumps(data, indent=2)}"
        )
        raise AssertionError(error_msg)


def assert_job_status(response, expected_status: str, message: str = None):
    """
    Assert that job status in response matches expected status.
    
    Args:
        response: Django test client response
        expected_status: Expected job status value
        message: Optional custom error message
    """
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise AssertionError(f"Response is not valid JSON: {e}")
    
    actual_status = data.get('status')
    
    if actual_status != expected_status:
        error_msg = message or (
            f"Expected job status '{expected_status}', got '{actual_status}'.\n"
            f"Response data: {json.dumps(data, indent=2)}"
        )
        raise AssertionError(error_msg)


def assert_error_message_present(response, message: str = None):
    """
    Assert that response contains an error message.
    
    Args:
        response: Django test client response
        message: Optional custom error message
    """
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise AssertionError(f"Response is not valid JSON: {e}")
    
    # Check for common error message fields
    error_fields = ['error', 'message', 'detail', 'error_message']
    has_error = any(field in data for field in error_fields)
    
    if not has_error:
        error_msg = message or (
            f"Response does not contain an error message field. "
            f"Expected one of {error_fields}.\n"
            f"Response data: {json.dumps(data, indent=2)}"
        )
        raise AssertionError(error_msg)


def assert_error_message_contains(response, expected_text: str, message: str = None):
    """
    Assert that error response contains specific text.
    
    Args:
        response: Django test client response
        expected_text: Text that should appear in error message
        message: Optional custom error message
    """
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise AssertionError(f"Response is not valid JSON: {e}")
    
    # Check common error message fields
    error_fields = ['error', 'message', 'detail', 'error_message']
    error_text = None
    
    for field in error_fields:
        if field in data:
            error_text = str(data[field])
            break
    
    if not error_text:
        raise AssertionError("No error message found in response")
    
    if expected_text.lower() not in error_text.lower():
        error_msg = message or (
            f"Expected error message to contain '{expected_text}', "
            f"but got: '{error_text}'"
        )
        raise AssertionError(error_msg)


def assert_pagination_present(response, message: str = None):
    """
    Assert that response contains pagination information.
    
    Args:
        response: Django test client response
        message: Optional custom error message
    """
    try:
        if hasattr(response, 'json'):
            data = response.json()
        else:
            data = json.loads(response.content)
    except (json.JSONDecodeError, AttributeError) as e:
        raise AssertionError(f"Response is not valid JSON: {e}")
    
    # Check for pagination fields
    pagination_indicators = [
        'pagination',
        'page',
        'next',
        'previous',
        'count',
        'total'
    ]
    
    has_pagination = any(field in data for field in pagination_indicators)
    
    if not has_pagination:
        error_msg = message or (
            f"Response does not contain pagination information. "
            f"Expected one of {pagination_indicators}.\n"
            f"Response data: {json.dumps(data, indent=2)}"
        )
        raise AssertionError(error_msg)


def assert_data_integrity(record: Dict[str, Any], required_fields: List[str]):
    """
    Assert that a data record contains all required fields.
    
    Args:
        record: Data record dictionary
        required_fields: List of field names that must be present
    """
    missing_fields = [field for field in required_fields if field not in record]
    
    if missing_fields:
        raise AssertionError(
            f"Record missing required fields: {missing_fields}.\n"
            f"Record: {json.dumps(record, indent=2)}"
        )


def assert_extraction_data_format(records: List[Dict[str, Any]], message: str = None):
    """
    Assert that extraction result records have the expected format.
    
    Validates that records contain required fields: email, first_name,
    last_name, id_from_service.
    
    Args:
        records: List of extraction result records
        message: Optional custom error message
    """
    if not isinstance(records, list):
        raise AssertionError(f"Expected list of records, got {type(records)}")
    
    if len(records) == 0:
        # Empty list is valid for some cases
        return
    
    required_fields = ['email', 'first_name', 'last_name', 'id_from_service']
    
    for i, record in enumerate(records):
        try:
            assert_data_integrity(record, required_fields)
        except AssertionError as e:
            error_msg = message or f"Record at index {i} failed validation: {e}"
            raise AssertionError(error_msg)


def assert_job_status_transition(
    old_status: str,
    new_status: str,
    valid_transitions: Optional[Dict[str, List[str]]] = None
):
    """
    Assert that job status transition is valid.
    
    Args:
        old_status: Previous job status
        new_status: New job status
        valid_transitions: Optional dict mapping status to list of valid next statuses
    """
    if valid_transitions is None:
        # Default valid transitions
        valid_transitions = {
            'pending': ['in_progress', 'cancelled', 'failed'],
            'in_progress': ['completed', 'failed', 'cancelled'],
            'completed': [],  # Terminal state
            'failed': [],  # Terminal state
            'cancelled': [],  # Terminal state
        }
    
    if old_status not in valid_transitions:
        raise AssertionError(f"Unknown status: {old_status}")
    
    valid_next = valid_transitions[old_status]
    
    if new_status not in valid_next and old_status != new_status:
        raise AssertionError(
            f"Invalid status transition from '{old_status}' to '{new_status}'. "
            f"Valid transitions: {valid_next}"
        )


def assert_response_time(response, max_seconds: float, message: str = None):
    """
    Assert that response time is within acceptable threshold.
    
    Args:
        response: Response object with elapsed time
        max_seconds: Maximum acceptable response time in seconds
        message: Optional custom error message
    """
    if hasattr(response, 'elapsed'):
        elapsed = response.elapsed.total_seconds()
        if elapsed > max_seconds:
            error_msg = message or (
                f"Response time {elapsed:.2f}s exceeded threshold of {max_seconds}s"
            )
            raise AssertionError(error_msg)


