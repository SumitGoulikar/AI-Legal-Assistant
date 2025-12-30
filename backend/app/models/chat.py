# backend/app/models/chat.py
"""
Chat Models
===========
Models for chat sessions and messages.

ChatSession: A conversation thread (can be general or about a specific document)
ChatMessage: Individual messages within a session (user or assistant)

Sessions are used to:
- Maintain conversation history
- Provide context for follow-up questions
- Allow users to review past conversations
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, func, Enum
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class SessionType(str, enum.Enum):
    """Type of chat session."""
    GENERAL = "general"      # General legal Q&A (uses knowledge base)
    DOCUMENT = "document"    # Q&A about a specific user document


class MessageRole(str, enum.Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"        # For system prompts/context


class ChatSession(Base):
    """
    Chat conversation session.
    
    Groups related messages into a conversation thread.
    Can be:
    - General: Legal Q&A using the knowledge base
    - Document: Q&A about a specific uploaded document
    
    Relationships:
    - owner: User who started the session
    - document: Optional document being discussed
    - messages: Messages in this session
    """
    
    __tablename__ = "chat_sessions"
    
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
    # FOREIGN KEYS
    # ============================================
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner of this chat session"
    )
    
    document_id = Column(
        String(36),
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Document being discussed (if any)"
    )
    
    # ============================================
    # SESSION METADATA
    # ============================================
    title = Column(
        String(255),
        nullable=True,
        comment="Session title (auto-generated from first message)"
    )
    
    session_type = Column(
        String(20),
        default=SessionType.GENERAL.value,
        nullable=False,
        index=True,
        comment="Type: general or document"
    )
    
    # ============================================
    # STATISTICS
    # ============================================
    message_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of messages in session"
    )
    
    total_tokens = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total tokens used in this session"
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
        nullable=False,
        comment="Last activity timestamp"
    )
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    owner = relationship(
        "User",
        back_populates="chat_sessions"
    )
    
    document = relationship(
        "Document",
        back_populates="chat_sessions"
    )
    
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
        lazy="selectin"
    )
    
    # ============================================
    # METHODS
    # ============================================
    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, type={self.session_type}, messages={self.message_count})>"
    
    def to_dict(self, include_messages: bool = False) -> dict:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "document_id": self.document_id,
            "title": self.title,
            "session_type": self.session_type,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_messages and self.messages:
            result["messages"] = [msg.to_dict() for msg in self.messages]
        return result


class ChatMessage(Base):
    """
    Individual chat message.
    
    Stores:
    - The message content (from user or AI)
    - Sources used to generate the response (for AI messages)
    - Token usage for tracking
    
    Sources are stored as JSON containing:
    - chunk_ids: IDs of chunks used
    - excerpts: Text excerpts shown to user
    - confidence scores
    """
    
    __tablename__ = "chat_messages"
    
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
    # FOREIGN KEY
    # ============================================
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # ============================================
    # MESSAGE DATA
    # ============================================
    role = Column(
        String(20),
        nullable=False,
        comment="Role: user, assistant, or system"
    )
    
    content = Column(
        Text,
        nullable=False,
        comment="The message text content"
    )
    
    # ============================================
    # AI RESPONSE METADATA
    # ============================================
    # For assistant messages, store the sources used
    sources = Column(
        JSON,
        nullable=True,
        comment="Sources/chunks used for this response"
    )
    
    # Token usage for tracking/billing
    tokens_used = Column(
        Integer,
        nullable=True,
        comment="Tokens used for this message"
    )
    
    # Model used for generation
    model_used = Column(
        String(100),
        nullable=True,
        comment="LLM model used for this response"
    )
    
    # Response generation time
    generation_time_ms = Column(
        Integer,
        nullable=True,
        comment="Time taken to generate response (milliseconds)"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    session = relationship(
        "ChatSession",
        back_populates="messages"
    )
    
    # ============================================
    # METHODS
    # ============================================
    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<ChatMessage(id={self.id}, role={self.role}, content='{content_preview}')>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "tokens_used": self.tokens_used,
            "model_used": self.model_used,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }