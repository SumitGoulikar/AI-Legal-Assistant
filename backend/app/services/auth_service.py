# backend/app/services/auth_service.py
"""
Authentication Service
======================
Business logic for user authentication operations.

Responsibilities:
- User registration
- User authentication (login)
- Password management
- User retrieval

This layer separates business logic from API routes,
making the code more testable and maintainable.
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
)


class AuthService:
    """
    Authentication service handling user operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    # ============================================
    # USER RETRIEVAL
    # ============================================
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            email: User's email
            
        Returns:
            User object if found, None otherwise
        """
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ============================================
    # USER REGISTRATION
    # ============================================
    
    async def create_user(self, user_data: UserCreate) -> User:
        """
        Create a new user account.
        
        Args:
            user_data: User registration data
            
        Returns:
            Created user object
            
        Raises:
            ValidationError: If email already exists
        """
        # Check if email already exists
        existing_user = await self.get_user_by_email(user_data.email)
        if existing_user:
            raise ValidationError(f"Email '{user_data.email}' is already registered")
        
        # Create new user with hashed password
        new_user = User(
            email=user_data.email.lower(),  # Normalize email
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            is_active=True,
            is_admin=False,
        )
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user
    
    # ============================================
    # USER AUTHENTICATION
    # ============================================
    
    async def authenticate_user(self, email: str, password: str) -> User:
        """
        Authenticate user with email and password.
        
        Args:
            email: User's email
            password: Plain text password
            
        Returns:
            Authenticated user object
            
        Raises:
            AuthenticationError: If credentials are invalid
        """
        # Find user by email
        user = await self.get_user_by_email(email)
        
        if not user:
            # Use same error message to prevent email enumeration
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")
        
        # Check if account is active
        if not user.is_active:
            raise AuthenticationError("Account is deactivated. Please contact support.")
        
        return user
    
    # ============================================
    # TOKEN GENERATION
    # ============================================
    
    def create_user_token(self, user: User) -> str:
        """
        Create access token for user.
        
        Args:
            user: User object
            
        Returns:
            JWT access token string
        """
        return create_access_token(
            subject=user.id,
            additional_claims={
                "email": user.email,
                "is_admin": user.is_admin,
            }
        )
    
    # ============================================
    # USER UPDATE
    # ============================================
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """
        Update user profile.
        
        Args:
            user_id: User's UUID
            user_data: Update data
            
        Returns:
            Updated user object
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Update only provided fields
        if user_data.full_name is not None:
            user.full_name = user_data.full_name
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    # ============================================
    # PASSWORD MANAGEMENT
    # ============================================
    
    async def change_password(
        self,
        user_id: str,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's password.
        
        Args:
            user_id: User's UUID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            True if successful
            
        Raises:
            NotFoundError: If user doesn't exist
            AuthenticationError: If current password is wrong
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")
        
        # Update to new password
        user.hashed_password = hash_password(new_password)
        
        await self.db.commit()
        
        return True
    
    # ============================================
    # ADMIN OPERATIONS
    # ============================================
    
    async def deactivate_user(self, user_id: str) -> User:
        """
        Deactivate a user account (admin only).
        
        Args:
            user_id: User's UUID
            
        Returns:
            Updated user object
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.is_active = False
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def activate_user(self, user_id: str) -> User:
        """
        Activate a user account (admin only).
        
        Args:
            user_id: User's UUID
            
        Returns:
            Updated user object
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise NotFoundError("User not found")
        
        user.is_active = True
        await self.db.commit()
        await self.db.refresh(user)
        
        return user


# ============================================
# HELPER FUNCTION FOR DEPENDENCY INJECTION
# ============================================
def get_auth_service(db: AsyncSession) -> AuthService:
    """
    Factory function to create AuthService instance.
    
    Usage with FastAPI Depends:
        @app.post("/login")
        async def login(
            db: AsyncSession = Depends(get_db),
            auth_service: AuthService = Depends(get_auth_service)
        ):
            ...
    """
    return AuthService(db)