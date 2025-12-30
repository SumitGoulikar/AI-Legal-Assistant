# backend/app/models/__init__.py
"""
Database Models Package
=======================
This package contains all SQLAlchemy ORM models for the application.

Models:
- User: User accounts and authentication
- Document: User-uploaded documents
- DocumentChunk: Text chunks from documents
- ChatSession: Chat conversation threads
- ChatMessage: Individual chat messages
- Template: Legal document templates
- GeneratedDocument: User-generated documents
- KnowledgeBase: Admin legal knowledge documents

Import all models here so they're registered with SQLAlchemy
when this package is imported.
"""

from app.models.user import User
from app.models.document import Document, DocumentChunk, DocumentStatus
from app.models.chat import ChatSession, ChatMessage, SessionType, MessageRole
from app.models.template import Template, GeneratedDocument
from app.models.knowledge_base import KnowledgeBase

# Export all models
__all__ = [
    "User",
    "Document",
    "DocumentChunk",
    "DocumentStatus",
    "ChatSession",
    "ChatMessage",
    "SessionType",
    "MessageRole",
    "Template",
    "GeneratedDocument",
    "KnowledgeBase",
]