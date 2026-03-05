from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, PermissionDenied, NotAuthenticated, APIException
from django.http import Http404
from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    Custom exception handler for Django REST Framework that returns 
    consistent JSON responses for all errors.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response is None, it means it's a generic python exception (500)
    # We should handle it to return JSON instead of HTML/Django default 500
    if response is None:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return Response({
            "success": False,
            "message": "An unexpected server error occurred.",
            "error_code": "SERVER_ERROR"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Default values
    error_code = "API_ERROR"
    message = "An error occurred."
    errors = None

    # Handle specific exception types to set appropriate error codes
    if isinstance(exc, ValidationError):
        error_code = "VALIDATION_ERROR"
        message = "Validation failed."
        errors = response.data
        
    elif isinstance(exc, (PermissionDenied, DjangoPermissionDenied)):
        error_code = "PERMISSION_DENIED"
        message = "You do not have permission to perform this action."
        
    elif isinstance(exc, NotAuthenticated):
        error_code = "AUTHENTICATION_FAILED"
        message = "Authentication credentials were not provided."
        
    elif isinstance(exc, Http404):
        error_code = "NOT_FOUND"
        message = "Resource not found."
        
    elif isinstance(exc, APIException):
        # Generic API Exception
        code = getattr(exc, 'default_code', 'API_ERROR')
        if code == 'error':
            code = 'API_ERROR'
        error_code = code.upper()
        
        if isinstance(exc.detail, (list, dict)):
             message = "Request processing failed."
             errors = exc.detail
        else:
             message = str(exc.detail)

    # Construct the final response data
    custom_data = {
        "success": False,
        "message": message,
        "error_code": error_code
    }
    
    # Add detailed errors if available (for validation errors mostly)
    if errors is not None:
        custom_data["errors"] = errors
        
    response.data = custom_data
    
    return response
