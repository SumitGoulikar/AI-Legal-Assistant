# backend/app/api/deps.py
"""
API Dependencies
================
Reusable dependencies for FastAPI routes.
"""

from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User

# Type alias for database session
DBSession = Annotated[AsyncSession, Depends(get_db)]

async def get_current_user(db: DBSession) -> User:
    """
    BYPASSED AUTH: Always returns the Guest User.
    In a real app, this would validate the JWT token.
    """
    # Fetch the fixed Guest User ID
    result = await db.execute(
        select(User).where(User.id == "00000000-0000-0000-0000-000000000000")
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Fallback object if DB wasn't seeded correctly (avoids crash)
        return User(
            id="00000000-0000-0000-0000-000000000000", 
            email="guest@example.com", 
            is_active=True, 
            is_admin=True
        )
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Returns active user."""
    return current_user

async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """Returns admin user (Guest is admin in this mode)."""
    return current_user

# --- EXPORTED ALIASES ---
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
AdminUser = Annotated[User, Depends(get_current_admin)]  # <--- This was missing!