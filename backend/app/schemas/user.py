# backend/app/schemas/user.py
"""
User Schemas
============
Pydantic models for user-related request/response validation.

Schema Types:
- Base: Shared fields
- Create: For registration (includes password)
- Update: For profile updates (all optional)
- Response: What we return to clients (no password)
- InDB: Internal representation (includes hashed password)

Why separate schemas?
- Security: Never expose password hash
- Flexibility: Different fields for different operations
- Validation: Automatic type checking and constraints
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ============================================
# BASE SCHEMA (Shared Fields)
# ============================================
class UserBase(BaseModel):
    """
    Base user schema with common fields.
    """
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"]
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="User's full name",
        examples=["Rahul Sharma"]
    )


# ============================================
# CREATE SCHEMA (Registration)
# ============================================
class UserCreate(UserBase):
    """
    Schema for user registration.
    
    Includes password with validation rules:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 chars, must include uppercase, lowercase, and digit)",
        examples=["SecurePass123"]
    )
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and clean full name."""
        # Remove extra whitespace
        v = " ".join(v.split())
        if len(v) < 2:
            raise ValueError("Full name must be at least 2 characters")
        return v


# ============================================
# UPDATE SCHEMA (Profile Update)
# ============================================
class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    All fields are optional.
    """
    full_name: Optional[str] = Field(
        None,
        min_length=2,
        max_length=255,
        description="Updated full name"
    )
    
    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean full name if provided."""
        if v is not None:
            v = " ".join(v.split())
            if len(v) < 2:
                raise ValueError("Full name must be at least 2 characters")
        return v


# ============================================
# PASSWORD UPDATE SCHEMA
# ============================================
class PasswordUpdate(BaseModel):
    """
    Schema for changing password.
    """
    current_password: str = Field(
        ...,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password"
    )
    
    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate new password strength."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        return v


# ============================================
# RESPONSE SCHEMA (API Response)
# ============================================
class UserResponse(BaseModel):
    """
    Schema for user data in API responses.
    Excludes sensitive data like password hash.
    """
    id: str = Field(..., description="Unique user ID")
    email: EmailStr = Field(..., description="User's email")
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(..., description="Account active status")
    is_admin: bool = Field(..., description="Admin privileges")
    created_at: datetime = Field(..., description="Registration date")
    updated_at: datetime = Field(..., description="Last update date")
    
    model_config = {
        "from_attributes": True,  # Allow creating from ORM models
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "rahul@example.com",
                "full_name": "Rahul Sharma",
                "is_active": True,
                "is_admin": False,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }
    }


# ============================================
# LOGIN SCHEMA
# ============================================
class UserLogin(BaseModel):
    """
    Schema for login request.
    """
    email: EmailStr = Field(
        ...,
        description="Registered email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="Account password",
        examples=["SecurePass123"]
    )


# ============================================
# TOKEN SCHEMAS
# ============================================
class Token(BaseModel):
    """
    Schema for authentication token response.
    """
    access_token: str = Field(
        ...,
        description="JWT access token"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }


class TokenPayload(BaseModel):
    """
    Schema for decoded token payload.
    """
    sub: str = Field(..., description="Subject (user ID)")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(default="access", description="Token type")


# ============================================
# AUTH RESPONSE SCHEMA (Login/Signup Response)
# ============================================
class AuthResponse(BaseModel):
    """
    Complete authentication response with user data and token.
    """
    success: bool = Field(default=True)
    message: str = Field(..., description="Response message")
    user: UserResponse = Field(..., description="User data")
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Login successful",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "rahul@example.com",
                    "full_name": "Rahul Sharma",
                    "is_active": True,
                    "is_admin": False,
                    "created_at": "2024-01-15T10:30:00Z",
                    "updated_at": "2024-01-15T10:30:00Z"
                },
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    }