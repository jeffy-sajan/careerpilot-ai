"""
Custom exceptions.
"""

class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, error_code: str = "APP_ERROR", status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, error_code="NOT_FOUND", status_code=404)

class ValidationError(AppException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message=message, error_code="VALIDATION_ERROR", status_code=422)
