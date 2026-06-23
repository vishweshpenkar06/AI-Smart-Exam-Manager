"""
AI Exam Manager — Custom Exception Classes
Structured exception hierarchy for clean error handling across the app.
"""
from datetime import datetime


class AppException(Exception):
    """Base exception for the application"""

    def __init__(self, message, status_code=400, error_code=None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)

    def to_dict(self):
        return {
            'status': 'error',
            'message': self.message,
            'error_code': self.error_code,
            'timestamp': datetime.utcnow().isoformat()
        }


class ValidationError(AppException):
    """Raised when input data fails validation (422 Unprocessable Entity)"""

    def __init__(self, message, field=None):
        super().__init__(message, 422, 'VALIDATION_ERROR')
        self.field = field

    def to_dict(self):
        data = super().to_dict()
        if self.field:
            data['field'] = self.field
        return data


class ResourceNotFoundError(AppException):
    """Raised when a requested resource doesn't exist (404 Not Found)"""

    def __init__(self, resource_type, resource_id):
        message = f'{resource_type} with ID {resource_id} not found'
        super().__init__(message, 404, 'RESOURCE_NOT_FOUND')


class ConflictError(AppException):
    """Raised on data conflicts, e.g. duplicate records (409 Conflict)"""

    def __init__(self, message):
        super().__init__(message, 409, 'CONFLICT')


class UnauthorizedError(AppException):
    """Raised when user is not authenticated (401 Unauthorized)"""

    def __init__(self, message='Unauthorized access'):
        super().__init__(message, 401, 'UNAUTHORIZED')


class ForbiddenError(AppException):
    """Raised when user lacks permission (403 Forbidden)"""

    def __init__(self, message='Access forbidden'):
        super().__init__(message, 403, 'FORBIDDEN')


class InsufficientResourcesError(AppException):
    """Raised when required resources (rooms, invigilators) are unavailable"""

    def __init__(self, resource_type):
        message = f'Insufficient {resource_type} available'
        super().__init__(message, 409, 'INSUFFICIENT_RESOURCES')
