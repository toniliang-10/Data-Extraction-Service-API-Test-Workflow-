"""
Custom exception handler for the API.

Provides consistent error responses across the entire API.
"""
from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Custom exception handler for DRF.
    
    Ensures all error responses have a consistent format with 'error' and 'message' fields.
    """
    # Call DRF's default exception handler first
    response = drf_exception_handler(exc, context)
    
    if response is not None:
        # Customize the response format
        custom_response_data = {}
        
        if isinstance(response.data, dict):
            # If it's a validation error with field-specific errors
            if 'detail' in response.data:
                custom_response_data['error'] = 'Error'
                custom_response_data['message'] = response.data['detail']
            else:
                custom_response_data['error'] = 'Validation failed'
                custom_response_data['details'] = response.data
        elif isinstance(response.data, list):
            custom_response_data['error'] = 'Error'
            custom_response_data['message'] = response.data[0] if response.data else 'An error occurred'
        else:
            custom_response_data['error'] = 'Error'
            custom_response_data['message'] = str(response.data)
        
        response.data = custom_response_data
    
    return response

