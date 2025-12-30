# backend/app/api/chat.py
"""
Chat API Routes
===============
Endpoints for chat sessions and AI-powered Q&A.

Endpoints:
- POST /chat/sessions - Create new chat session
- GET /chat/sessions - List user's sessions
- GET /chat/sessions/{id} - Get session with messages
- POST /chat/sessions/{id}/messages - Send message and get AI response
- PUT /chat/sessions/{id} - Update session
- DELETE /chat/sessions/{id} - Delete session
- POST /chat/query - Quick query without session
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db
from app.schemas.chat import (
    ChatSessionCreate,
    ChatMessageCreate,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatMessageResponse,
    ChatQueryResponse,
    ChatSessionListResponse,
)
from app.schemas.common import MessageResponse, ErrorResponse
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService
from app.api.deps import ActiveUser, DBSession
from app.core.exceptions import NotFoundError, ValidationError


# ============================================
# ROUTER SETUP
# ============================================
router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)


# ============================================
# CREATE SESSION
# ============================================
@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create chat session",
    response_description="Chat session created successfully",
)
async def create_chat_session(
    session_data: ChatSessionCreate,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Create a new chat session.
    
    **Session Types:**
    - `general`: General legal Q&A using knowledge base
    - `document`: Q&A about a specific uploaded document (requires document_id)
    
    The session stores your conversation history and allows follow-up questions.
    """
    chat_service = ChatService(db)
    
    try:
        session = await chat_service.create_session(
            user_id=current_user.id,
            session_type=session_data.session_type,
            document_id=session_data.document_id,
            title=session_data.title,
        )
        
        return ChatSessionResponse.model_validate(session)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )


# ============================================
# LIST SESSIONS
# ============================================
@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List chat sessions",
    response_description="List of user's chat sessions",
)
async def list_chat_sessions(
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    session_type: Optional[str] = Query(None, description="Filter by session type"),
):
    """
    List your chat sessions with pagination.
    
    Sessions are ordered by most recently updated first.
    """
    chat_service = ChatService(db)
    
    sessions, total = await chat_service.list_user_sessions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        session_type=session_type,
    )
    
    return ChatSessionListResponse(
        success=True,
        sessions=[ChatSessionResponse.model_validate(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# GET SESSION WITH MESSAGES
# ============================================
@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetailResponse,
    summary="Get chat session",
    response_description="Chat session with all messages",
)
async def get_chat_session(
    session_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get a chat session with all its messages.
    
    Returns the complete conversation history.
    """
    chat_service = ChatService(db)
    
    session = await chat_service.get_session_with_messages(
        session_id=session_id,
        user_id=current_user.id
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return ChatSessionDetailResponse(
        success=True,
        session=ChatSessionResponse.model_validate(session),
        messages=[ChatMessageResponse.model_validate(m) for m in session.messages],
    )


# ============================================
# SEND MESSAGE (RAG Query)
# ============================================
@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatQueryResponse,
    summary="Send message to chat session",
    response_description="AI response with sources",
)
async def send_chat_message(
    session_id: str,
    message_data: ChatMessageCreate,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Send a message to a chat session and get an AI response.
    
    The AI will:
    1. Retrieve relevant context from the knowledge base or document
    2. Consider the conversation history
    3. Generate a response using RAG
    4. Include source references
    
    **Note:** All responses include a disclaimer that this is AI-generated
    information and not legal advice.
    """
    chat_service = ChatService(db)
    rag_service = RAGService(db)
    
    # Get session
    session = await chat_service.get_session_by_id(session_id, current_user.id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    # Get conversation history for context
    history = await chat_service.get_conversation_history(
        session_id=session_id,
        user_id=current_user.id,
        max_messages=10
    )
    
    # Save user message
    user_message = await chat_service.add_message(
        session_id=session_id,
        role="user",
        content=message_data.content,
    )
    
    try:
        # Generate AI response
        if session.session_type == "document":
            # Document-specific Q&A
            result = await rag_service.query_document(
                query=message_data.content,
                document_id=session.document_id,
                user_id=current_user.id,
            )
        else:
            # General legal Q&A
            result = await rag_service.query_legal_knowledge(
                query=message_data.content,
                user_id=current_user.id,
                conversation_history=history,
            )
        
        # Save assistant message
        assistant_message = await chat_service.add_message(
            session_id=session_id,
            role="assistant",
            content=result["answer"],
            sources=result.get("sources"),
            tokens_used=result.get("tokens_used"),
            model_used=result.get("model_used"),
            generation_time_ms=result.get("generation_time_ms"),
        )
        
        return ChatQueryResponse(
            success=True,
            user_message=ChatMessageResponse.model_validate(user_message),
            assistant_message=ChatMessageResponse.model_validate(assistant_message),
            sources=result.get("sources"),
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )


# ============================================
# QUICK QUERY (No Session)
# ============================================
@router.post(
    "/query",
    summary="Quick legal query",
    response_description="AI response without creating a session",
)
async def quick_query(
    current_user: ActiveUser,
    db: DBSession,
    query: str = Query(..., min_length=3, description="Your legal question"),
):
    """
    Ask a quick legal question without creating a chat session.
    
    Useful for one-off questions. If you want to have a conversation
    with follow-up questions, use a chat session instead.
    
    **Example queries:**
    - "What is the statute of limitations for breach of contract in India?"
    - "Explain Section 420 of IPC"
    - "What are the requirements for a valid will?"
    """
    rag_service = RAGService(db)
    
    try:
        result = await rag_service.query_legal_knowledge(
            query=query,
            user_id=current_user.id,
        )
        
        return {
            "success": True,
            "query": query,
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "tokens_used": result.get("tokens_used", 0),
            "model_used": result.get("model_used", "unknown"),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating response: {str(e)}"
        )


# ============================================
# UPDATE SESSION
# ============================================
@router.put(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
    summary="Update chat session",
    response_description="Updated session",
)
async def update_chat_session(
    session_id: str,
    current_user: ActiveUser,
    db: DBSession,
    title: str = Query(..., min_length=1, max_length=255, description="New title"),
):
    """
    Update a chat session (currently only title can be updated).
    """
    chat_service = ChatService(db)
    
    try:
        session = await chat_service.update_session_title(
            session_id=session_id,
            user_id=current_user.id,
            title=title,
        )
        
        return ChatSessionResponse.model_validate(session)
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )


# ============================================
# DELETE SESSION
# ============================================
@router.delete(
    "/sessions/{session_id}",
    response_model=MessageResponse,
    summary="Delete chat session",
    response_description="Session deleted successfully",
)
async def delete_chat_session(
    session_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Delete a chat session and all its messages.
    
    This action is irreversible.
    """
    chat_service = ChatService(db)
    
    try:
        await chat_service.delete_session(
            session_id=session_id,
            user_id=current_user.id
        )
        
        return MessageResponse(
            success=True,
            message="Chat session deleted successfully"
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )


# ============================================
# CHAT STATISTICS
# ============================================
@router.get(
    "/stats",
    summary="Get chat statistics",
    response_description="User's chat statistics",
)
async def get_chat_stats(
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get statistics about your chat usage.
    """
    chat_service = ChatService(db)
    
    stats = await chat_service.get_user_chat_stats(current_user.id)
    
    return {
        "success": True,
        "stats": stats,
    }