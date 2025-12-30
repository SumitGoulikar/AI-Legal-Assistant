# backend/app/schemas/chat.py
"""
Chat Schemas
=============
Pydantic models for chat-related requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================
class SessionType(str, Enum):
    """Type of chat session."""
    GENERAL = "general"      # General legal Q&A
    DOCUMENT = "document"    # Q&A about specific document


class MessageRole(str, Enum):
    """Role of message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ============================================
# REQUEST SCHEMAS
# ============================================
class ChatSessionCreate(BaseModel):
    """Create a new chat session."""
    session_type: SessionType = Field(
        default=SessionType.GENERAL,
        description="Type of chat session"
    )
    document_id: Optional[str] = Field(
        None,
        description="Document ID for document-specific sessions"
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional session title"
    )


class ChatMessageCreate(BaseModel):
    """Send a message in a chat session."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content"
    )


# ============================================
# RESPONSE SCHEMAS
# ============================================
class ChatMessageResponse(BaseModel):
    """Chat message in responses."""
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[List[Dict[str, Any]]] = None
    tokens_used: Optional[int] = None
    model_used: Optional[str] = None
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class ChatSessionResponse(BaseModel):
    """Chat session response."""
    id: str
    user_id: str
    document_id: Optional[str] = None
    title: Optional[str] = None
    session_type: str
    message_count: int
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class ChatSessionDetailResponse(BaseModel):
    """Detailed session with messages."""
    success: bool = True
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]


class ChatQueryResponse(BaseModel):
    """Response from sending a chat message."""
    success: bool = True
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    sources: Optional[List[Dict[str, Any]]] = None


class ChatSessionListResponse(BaseModel):
    """Paginated list of chat sessions."""
    success: bool = True
    sessions: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int