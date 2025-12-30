# backend/app/services/chat_service.py
"""
Chat Service
============
Manages chat sessions and messages.

Responsibilities:
- Create and manage chat sessions
- Store messages
- Retrieve conversation history
- Track token usage
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage, SessionType, MessageRole
from app.core.exceptions import NotFoundError, ValidationError


class ChatService:
    """Service for managing chat sessions and messages."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    # ============================================
    # SESSION MANAGEMENT
    # ============================================
    
    async def create_session(
        self,
        user_id: str,
        session_type: str = "general",
        document_id: Optional[str] = None,
        title: Optional[str] = None
    ) -> ChatSession:
        """
        Create a new chat session.
        
        Args:
            user_id: User's ID
            session_type: "general" or "document"
            document_id: Optional document ID for document sessions
            title: Optional session title
            
        Returns:
            Created chat session
        """
        # Validate document session
        if session_type == "document" and not document_id:
            raise ValidationError("Document ID required for document sessions")
        
        # Create session
        session = ChatSession(
            user_id=user_id,
            session_type=session_type,
            document_id=document_id,
            title=title or self._generate_session_title(session_type),
            message_count=0,
            total_tokens=0,
        )
        
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def get_session_by_id(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[ChatSession]:
        """
        Get a chat session by ID.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID (for ownership verification)
            
        Returns:
            Chat session if found
        """
        stmt = (
            select(ChatSession)
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == user_id)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_session_with_messages(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[ChatSession]:
        """
        Get session with all its messages loaded.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID
            
        Returns:
            Chat session with messages
        """
        stmt = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
            .where(ChatSession.user_id == user_id)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_user_sessions(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        session_type: Optional[str] = None
    ) -> Tuple[List[ChatSession], int]:
        """
        List user's chat sessions with pagination.
        
        Args:
            user_id: User's ID
            page: Page number (1-indexed)
            page_size: Items per page
            session_type: Optional filter by type
            
        Returns:
            Tuple of (sessions list, total count)
        """
        base_stmt = select(ChatSession).where(ChatSession.user_id == user_id)
        
        if session_type:
            base_stmt = base_stmt.where(ChatSession.session_type == session_type)
        
        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            base_stmt
            .order_by(desc(ChatSession.updated_at))
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.db.execute(stmt)
        sessions = result.scalars().all()
        
        return list(sessions), total
    
    async def update_session_title(
        self,
        session_id: str,
        user_id: str,
        title: str
    ) -> ChatSession:
        """
        Update session title.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID
            title: New title
            
        Returns:
            Updated session
        """
        session = await self.get_session_by_id(session_id, user_id)
        if not session:
            raise NotFoundError("Chat session not found")
        
        session.title = title
        await self.db.commit()
        await self.db.refresh(session)
        
        return session
    
    async def delete_session(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a chat session and all its messages.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID
            
        Returns:
            True if deleted successfully
        """
        session = await self.get_session_by_id(session_id, user_id)
        if not session:
            raise NotFoundError("Chat session not found")
        
        await self.db.delete(session)
        await self.db.commit()
        
        return True
    
    # ============================================
    # MESSAGE MANAGEMENT
    # ============================================
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List[dict]] = None,
        tokens_used: Optional[int] = None,
        model_used: Optional[str] = None,
        generation_time_ms: Optional[int] = None
    ) -> ChatMessage:
        """
        Add a message to a chat session.
        
        Args:
            session_id: Session's UUID
            role: Message role (user, assistant, system)
            content: Message content
            sources: Optional source chunks used
            tokens_used: Token count
            model_used: Model name
            generation_time_ms: Generation time in ms
            
        Returns:
            Created message
        """
        # Create message
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            sources=sources,
            tokens_used=tokens_used,
            model_used=model_used,
            generation_time_ms=generation_time_ms,
        )
        
        self.db.add(message)
        
        # Update session stats
        session = await self.db.get(ChatSession, session_id)
        if session:
            session.message_count += 1
            if tokens_used:
                session.total_tokens += tokens_used
            session.updated_at = datetime.utcnow()
            
            # Auto-generate title from first user message
            if not session.title or session.title.startswith("New "):
                if role == "user" and session.message_count == 1:
                    session.title = self._generate_title_from_message(content)
        
        await self.db.commit()
        await self.db.refresh(message)
        
        return message
    
    async def get_session_messages(
        self,
        session_id: str,
        user_id: str,
        limit: Optional[int] = None
    ) -> List[ChatMessage]:
        """
        Get messages for a session.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID
            limit: Optional limit on number of messages
            
        Returns:
            List of messages ordered by creation time
        """
        # Verify session belongs to user
        session = await self.get_session_by_id(session_id, user_id)
        if not session:
            raise NotFoundError("Chat session not found")
        
        stmt = (
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_conversation_history(
        self,
        session_id: str,
        user_id: str,
        max_messages: int = 10
    ) -> List[dict]:
        """
        Get conversation history formatted for LLM context.
        
        Args:
            session_id: Session's UUID
            user_id: User's ID
            max_messages: Maximum number of messages to include
            
        Returns:
            List of message dicts with 'role' and 'content'
        """
        messages = await self.get_session_messages(
            session_id, user_id, limit=max_messages
        )
        
        # Convert to LLM format
        history = []
        for msg in messages:
            if msg.role in ["user", "assistant"]:
                history.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        return history
    
    # ============================================
    # STATISTICS
    # ============================================
    
    async def get_user_chat_stats(self, user_id: str) -> dict:
        """
        Get chat statistics for a user.
        
        Args:
            user_id: User's ID
            
        Returns:
            Dictionary with statistics
        """
        # Total sessions
        total_stmt = select(func.count(ChatSession.id)).where(
            ChatSession.user_id == user_id
        )
        total_result = await self.db.execute(total_stmt)
        total_sessions = total_result.scalar() or 0
        
        # Total messages
        msg_stmt = (
            select(func.count(ChatMessage.id))
            .join(ChatSession)
            .where(ChatSession.user_id == user_id)
        )
        msg_result = await self.db.execute(msg_stmt)
        total_messages = msg_result.scalar() or 0
        
        # Total tokens
        token_stmt = select(func.sum(ChatSession.total_tokens)).where(
            ChatSession.user_id == user_id
        )
        token_result = await self.db.execute(token_stmt)
        total_tokens = token_result.scalar() or 0
        
        # By session type
        type_stmt = (
            select(ChatSession.session_type, func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id)
            .group_by(ChatSession.session_type)
        )
        type_result = await self.db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_result.all()}
        
        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "by_type": by_type,
        }
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _generate_session_title(self, session_type: str) -> str:
        """Generate a default session title."""
        if session_type == "document":
            return "New Document Q&A"
        return "New Legal Query"
    
    def _generate_title_from_message(self, content: str, max_length: int = 50) -> str:
        """Generate session title from first message."""
        # Take first sentence or truncate
        title = content.split('.')[0].split('?')[0].split('!')[0]
        title = title.strip()
        
        if len(title) > max_length:
            title = title[:max_length].rsplit(' ', 1)[0] + "..."
        
        return title or "New Conversation"


def get_chat_service(db: AsyncSession) -> ChatService:
    """Factory function to create ChatService instance."""
    return ChatService(db)