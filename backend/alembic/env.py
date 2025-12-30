# backend/alembic/env.py
"""
Alembic Environment Configuration
=================================
Configures Alembic to work with our async SQLAlchemy setup.
"""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import our app configuration and models
import sys
from pathlib import Path

# Add the parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.database import Base

# Import all models to ensure they're registered with Base.metadata
from app.models import (
    User, 
    Document, 
    DocumentChunk, 
    ChatSession, 
    ChatMessage,
    Template, 
    GeneratedDocument, 
    KnowledgeBase
)

# Alembic Config object
config = context.config

# Set the database URL from our settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+aiosqlite", ""))

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.
    
    This configures the context with just a URL and not an Engine.
    Calls to context.execute() emit the given string to the script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations with a database connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode with async support.
    
    Creates an async Engine and associates a connection with the context.
    """
    # For SQLite, we need synchronous connection
    from sqlalchemy import create_engine
    
    url = config.get_main_option("sqlalchemy.url")
    
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()