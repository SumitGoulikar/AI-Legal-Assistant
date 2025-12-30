# backend/app/models/user.py
"""
User Model
==========
Defines the User table for authentication and user management.

Fields:
- id: Unique identifier (UUID)
- email: User's email (unique, used for login)
- hashed_password: Bcrypt hashed password
- full_name: Display name
- is_active: Whether account is active
- is_admin: Admin privileges flag
- created_at, updated_at: Timestamps
"""

from sqlalchemy import Column, String, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class User(Base):
    """
    User account model.
    
    Relationships:
    - documents: User's uploaded documents
    - chat_sessions: User's chat conversations
    - generated_documents: Documents created by user
    """
    
    __tablename__ = "users"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(
        String(36),  # UUID as string for SQLite compatibility
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True,
        comment="Unique user identifier"
    )
    
    # ============================================
    # AUTHENTICATION FIELDS
    # ============================================
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (used for login)"
    )
    
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    # ============================================
    # PROFILE FIELDS
    # ============================================
    full_name = Column(
        String(255),
        nullable=False,
        comment="User's full display name"
    )
    
    # ============================================
    # STATUS FLAGS
    # ============================================
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is active"
    )
    
    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has admin privileges"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Account creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp"
    )
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    # One-to-Many: User has many documents
    documents = relationship(
        "Document",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # One-to-Many: User has many chat sessions
    chat_sessions = relationship(
        "ChatSession",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # One-to-Many: User has many generated documents
    generated_documents = relationship(
        "GeneratedDocument",
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    # ============================================
    # MODEL METHODS
    # ============================================
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (excluding sensitive data)."""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }