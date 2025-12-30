# backend/app/api/auth.py
"""
Authentication API Routes
=========================
Endpoints for user authentication and account management.

Endpoints:
- POST /auth/signup - Register new user
- POST /auth/login - Login user
- GET /auth/me - Get current user profile
- PUT /auth/me - Update current user profile
- PUT /auth/password - Change password
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    PasswordUpdate,
    AuthResponse,
)
from app.schemas.common import MessageResponse, ErrorResponse
from app.services.auth_service import AuthService
from app.api.deps import ActiveUser, DBSession
from app.core.exceptions import AuthenticationError, ValidationError, NotFoundError
from app.config import settings


# ============================================
# ROUTER SETUP
# ============================================
router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        422: {"description": "Validation error"},
    },
)


# ============================================
# SIGNUP ENDPOINT
# ============================================
@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    response_description="User created successfully with access token",
)
async def signup(
    user_data: UserCreate,
    db: DBSession,
):
    """
    Register a new user account.
    
    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    
    Returns the created user and an access token for immediate login.
    """
    auth_service = AuthService(db)
    
    try:
        # Create the user
        user = await auth_service.create_user(user_data)
        
        # Generate access token
        access_token = auth_service.create_user_token(user)
        
        return AuthResponse(
            success=True,
            message="Account created successfully! Welcome to AI Legal Assistant.",
            user=UserResponse.model_validate(user),
            access_token=access_token,
            token_type="bearer",
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e.message),
        )


# ============================================
# LOGIN ENDPOINT
# ============================================
@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login user",
    response_description="Login successful with access token",
)
async def login(
    login_data: UserLogin,
    db: DBSession,
):
    """
    Authenticate user with email and password.
    
    Returns user data and an access token on successful authentication.
    
    **Note:** The access token expires after the configured time
    (default: 24 hours). Include it in the Authorization header
    for protected endpoints.
    """
    auth_service = AuthService(db)
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            email=login_data.email,
            password=login_data.password,
        )
        
        # Generate access token
        access_token = auth_service.create_user_token(user)
        
        return AuthResponse(
            success=True,
            message="Login successful!",
            user=UserResponse.model_validate(user),
            access_token=access_token,
            token_type="bearer",
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e.message),
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# GET CURRENT USER ENDPOINT
# ============================================
@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    response_description="Current user profile",
)
async def get_me(current_user: ActiveUser):
    """
    Get the currently authenticated user's profile.
    
    Requires a valid JWT token in the Authorization header.
    """
    return UserResponse.model_validate(current_user)


# ============================================
# UPDATE CURRENT USER ENDPOINT
# ============================================
@router.put(
    "/me",
    response_model=UserResponse,
    summary="Update current user",
    response_description="Updated user profile",
)
async def update_me(
    user_data: UserUpdate,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Update the currently authenticated user's profile.
    
    Only provided fields will be updated.
    """
    auth_service = AuthService(db)
    
    try:
        updated_user = await auth_service.update_user(
            user_id=current_user.id,
            user_data=user_data,
        )
        return UserResponse.model_validate(updated_user)
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e.message),
        )


# ============================================
# CHANGE PASSWORD ENDPOINT
# ============================================
@router.put(
    "/password",
    response_model=MessageResponse,
    summary="Change password",
    response_description="Password changed successfully",
)
async def change_password(
    password_data: PasswordUpdate,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Change the currently authenticated user's password.
    
    Requires current password for verification.
    
    **New Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )
        
        return MessageResponse(
            success=True,
            message="Password changed successfully!",
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message),
        )


# ============================================
# VERIFY TOKEN ENDPOINT
# ============================================
@router.get(
    "/verify",
    response_model=MessageResponse,
    summary="Verify token",
    response_description="Token is valid",
)
async def verify_token(current_user: ActiveUser):
    """
    Verify that the current JWT token is valid.
    
    Useful for frontend to check if user is still logged in.
    """
    return MessageResponse(
        success=True,
        message=f"Token is valid. Logged in as {current_user.email}",
    )


# ============================================
# USER STATS ENDPOINT (for dashboard)
# ============================================
@router.get(
    "/stats",
    summary="Get user statistics",
    response_description="User statistics for dashboard",
)
async def get_user_stats(
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get statistics for the current user.
    
    Returns counts of documents, chat sessions, generated documents, etc.
    """
    from sqlalchemy import select, func
    from app.models import Document, ChatSession, GeneratedDocument
    
    # Count documents
    doc_count = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    
    # Count chat sessions
    session_count = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id)
    )
    
    # Count generated documents
    gen_count = await db.execute(
        select(func.count(GeneratedDocument.id)).where(GeneratedDocument.user_id == current_user.id)
    )
    
    return {
        "success": True,
        "stats": {
            "documents_uploaded": doc_count.scalar() or 0,
            "chat_sessions": session_count.scalar() or 0,
            "documents_generated": gen_count.scalar() or 0,
        },
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "member_since": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "disclaimer": settings.AI_DISCLAIMER,
    }