# backend/app/schemas/common.py
"""
Common Response Schemas
=======================
Standard response schemas used across the API.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Generic, TypeVar, List
from datetime import datetime


# Generic type for paginated responses
T = TypeVar("T")


class MessageResponse(BaseModel):
    """Simple message response."""
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    success: bool = False
    error: str
    detail: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "Authentication failed",
                "detail": "Invalid email or password"
            }
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response."""
    success: bool = True
    data: List[Any]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    service: str
    version: str
    environment: str