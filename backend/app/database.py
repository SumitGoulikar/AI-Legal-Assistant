# backend/app/database.py
"""
Database Configuration
======================
This module sets up the async SQLAlchemy engine, session management,
and provides the base class for all database models.

Why Async SQLAlchemy?
- Non-blocking database operations
- Better performance under high load
- Matches FastAPI's async nature
- Efficient connection pooling

Architecture:
- Engine: Manages the connection pool
- SessionLocal: Factory for creating sessions
- Base: Declarative base for ORM models
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData
from typing import AsyncGenerator

from app.config import settings


# ============================================
# NAMING CONVENTIONS FOR CONSTRAINTS
# ============================================
# This ensures consistent naming for indexes, foreign keys, etc.
# Makes migrations cleaner and more predictable

convention = {
    "ix": "ix_%(column_0_label)s",                    # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",      # Unique constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",    # Check constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",  # Foreign key
    "pk": "pk_%(table_name)s"                          # Primary key
}

metadata = MetaData(naming_convention=convention)


# ============================================
# DECLARATIVE BASE CLASS
# ============================================
class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    All models inherit from this class, which provides:
    - Common metadata with naming conventions
    - Automatic table name generation (optional)
    - Shared functionality across models
    """
    metadata = metadata


# ============================================
# ASYNC ENGINE CONFIGURATION
# ============================================
# Create the async engine with appropriate settings

# For SQLite, we need to enable foreign keys and use check_same_thread=False
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,  # Log SQL queries in debug mode
        future=True,
        connect_args={"check_same_thread": False}  # Required for SQLite
    )
else:
    # PostgreSQL or other databases
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        future=True,
        pool_size=5,          # Number of connections to keep open
        max_overflow=10,      # Extra connections when pool is full
        pool_timeout=30,      # Seconds to wait for a connection
        pool_recycle=1800,    # Recycle connections after 30 minutes
    )


# ============================================
# SESSION FACTORY
# ============================================
# Creates async session instances for database operations

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


# ============================================
# DEPENDENCY INJECTION FOR FASTAPI
# ============================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage in FastAPI routes:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # use db here
            pass
    
    The session is automatically closed after the request completes,
    even if an exception occurs.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ============================================
# DATABASE INITIALIZATION
# ============================================
async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This is called during application startup.
    In production, you should use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        # Import all models to register them with Base
        from app.models import user, document, chat, template, knowledge_base
        
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Database tables created successfully!")


async def close_db() -> None:
    """
    Close database connections.
    
    Called during application shutdown.
    """
    await engine.dispose()
    print("✅ Database connections closed.")