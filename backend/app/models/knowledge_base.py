# backend/app/models/knowledge_base.py
"""
Knowledge Base Model
====================
Model for admin-uploaded legal knowledge documents.

These are the documents that power the general Legal Q&A feature.
Examples:
- Indian Contract Act, 1872
- Consumer Protection Act, 2019
- Legal textbook excerpts
- Court judgment summaries

Unlike user documents, these are:
- Uploaded by admins only
- Shared across all users
- Stored in a separate ChromaDB collection
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean, func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class KnowledgeBase(Base):
    """
    Legal knowledge base document.
    
    Admin-uploaded legal texts that form the knowledge base
    for answering general legal questions.
    
    Processing flow:
    1. Admin uploads document (PDF/TXT)
    2. Text is extracted and chunked
    3. Chunks are embedded and stored in ChromaDB
    4. Used for RAG when users ask general questions
    """
    
    __tablename__ = "knowledge_base"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True
    )
    
    # ============================================
    # DOCUMENT METADATA
    # ============================================
    title = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Document title (e.g., 'Indian Contract Act, 1872')"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Description of the document content"
    )
    
    source = Column(
        String(255),
        nullable=True,
        comment="Source of the document (e.g., 'Government of India')"
    )
    
    source_url = Column(
        String(500),
        nullable=True,
        comment="URL to original source (if available)"
    )
    
    # ============================================
    # CATEGORIZATION
    # ============================================
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Category: acts, rules, judgments, guides"
    )
    
    tags = Column(
        JSON,
        nullable=True,
        comment="Tags for filtering: ['contract', 'commercial', 'civil']"
    )
    
    # ============================================
    # FILE DATA
    # ============================================
    file_path = Column(
        String(500),
        nullable=True,
        comment="Path to original uploaded file"
    )
    
    file_type = Column(
        String(50),
        nullable=True,
        comment="File type: pdf, txt"
    )
    
    # ============================================
    # PROCESSING STATUS
    # ============================================
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Status: pending, processing, ready, failed"
    )
    
    chunk_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of chunks created"
    )
    
    # ============================================
    # STATUS FLAGS
    # ============================================
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this document is used in searches"
    )
    
    # ============================================
    # ADMIN TRACKING
    # ============================================
    uploaded_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Admin who uploaded this document"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # ============================================
    # METHODS
    # ============================================
    def __repr__(self) -> str:
        return f"<KnowledgeBase(id={self.id}, title={self.title}, status={self.status})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "source": self.source,
            "source_url": self.source_url,
            "category": self.category,
            "tags": self.tags,
            "status": self.status,
            "chunk_count": self.chunk_count,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }