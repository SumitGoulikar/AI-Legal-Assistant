# backend/app/services/admin_service.py
"""
Admin Service
=============
Business logic for administrative tasks.
"""

from typing import List, Dict, Any, Tuple
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.document import Document
from app.models.chat import ChatSession
from app.models.knowledge_base import KnowledgeBase
from app.core.exceptions import NotFoundError, ValidationError

class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_system_stats(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        
        # Count users
        user_count = await self.db.execute(select(func.count(User.id)))
        total_users = user_count.scalar() or 0
        
        # Count documents
        doc_count = await self.db.execute(select(func.count(Document.id)))
        total_docs = doc_count.scalar() or 0
        
        # Count chat sessions
        chat_count = await self.db.execute(select(func.count(ChatSession.id)))
        total_chats = chat_count.scalar() or 0
        
        # Count KB entries
        kb_count = await self.db.execute(select(func.count(KnowledgeBase.id)))
        total_kb = kb_count.scalar() or 0
        
        return {
            "total_users": total_users,
            "total_documents": total_docs,
            "total_chat_sessions": total_chats,
            "total_knowledge_base_items": total_kb,
        }

    async def list_users(self, page: int = 1, page_size: int = 20) -> Tuple[List[User], int]:
        """List all users."""
        count_stmt = select(func.count(User.id))
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        offset = (page - 1) * page_size
        stmt = select(User).order_by(desc(User.created_at)).offset(offset).limit(page_size)
        result = await self.db.execute(stmt)
        users = result.scalars().all()
        
        return list(users), total

def get_admin_service(db: AsyncSession) -> AdminService:
    return AdminService(db)