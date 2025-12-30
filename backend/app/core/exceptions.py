# backend/app/core/exceptions.py
"""
Custom Exceptions
=================
Centralized exception classes for the Legal Assistant API.

Why custom exceptions?
- Consistent error responses across the API
- Easy to catch and handle specific error types
- Better error messages for debugging
- Can include additional context (status codes, details)
"""

from fastapi import HTTPException, status


class LegalAssistantException(Exception):
    """Base exception for all custom exceptions in this application."""
    
    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(LegalAssistantException):
    """Raised when authentication fails."""
    pass


class AuthorizationError(LegalAssistantException):
    """Raised when user doesn't have permission."""
    pass


class NotFoundError(LegalAssistantException):
    """Raised when a requested resource is not found."""
    pass


class ValidationError(LegalAssistantException):
    """Raised when input validation fails."""
    pass


class FileProcessingError(LegalAssistantException):
    """Raised when file processing (upload, extraction) fails."""
    pass


class LLMError(LegalAssistantException):
    """Raised when LLM/AI operations fail."""
    pass


class DatabaseError(LegalAssistantException):
    """Raised when database operations fail."""
    pass


# ============================================
# HTTP EXCEPTION HELPERS
# ============================================
# These are convenience functions to raise FastAPI HTTPExceptions
# with consistent formatting

def raise_unauthorized(detail: str = "Could not validate credentials") -> None:
    """Raise 401 Unauthorized error."""
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_forbidden(detail: str = "Not enough permissions") -> None:
    """Raise 403 Forbidden error."""
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=detail,
    )


def raise_not_found(resource: str = "Resource") -> None:
    """Raise 404 Not Found error."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{resource} not found",
    )


def raise_bad_request(detail: str = "Bad request") -> None:
    """Raise 400 Bad Request error."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=detail,
    )


def raise_conflict(detail: str = "Conflict") -> None:
    """Raise 409 Conflict error (e.g., duplicate resource)."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
    )


def raise_internal_error(detail: str = "Internal server error") -> None:
    """Raise 500 Internal Server Error."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=detail,
    )