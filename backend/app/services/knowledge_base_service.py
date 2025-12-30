# backend/app/services/knowledge_base_service.py
"""
Knowledge Base Service
======================
Manages the legal knowledge base for RAG.

The knowledge base contains:
- Indian legal acts and amendments
- Legal textbook content
- Court judgment summaries
- Legal guides and explanations

This forms the "knowledge" that powers general legal Q&A.
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_base import KnowledgeBase
from app.utils.file_processor import (
    validate_file_extension,
    save_upload_file,
    extract_text,
    chunk_text,
    format_file_size,
)
from app.services.vector_store_service import get_vector_store_service
from app.core.exceptions import NotFoundError, ValidationError
from app.config import settings


class KnowledgeBaseService:
    """
    Service for managing the legal knowledge base.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.vector_store = get_vector_store_service()
    
    # ============================================
    # ADD KNOWLEDGE
    # ============================================
    
    async def add_knowledge_from_file(
        self,
        file_content: bytes,
        filename: str,
        title: str,
        description: str,
        source: str,
        category: str,
        uploaded_by: str,
        tags: Optional[List[str]] = None
    ) -> KnowledgeBase:
        """
        Add a new document to the knowledge base.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename
            title: Document title
            description: Description
            source: Source of the document
            category: Category (acts, rules, etc.)
            uploaded_by: Admin user ID
            tags: Optional tags for filtering
            
        Returns:
            Created knowledge base entry
        """
        # Validate file
        file_type = validate_file_extension(filename)
        
        # Save file
        stored_filename, file_path = await save_upload_file(
            file_content=file_content,
            user_id="knowledge_base",  # Special folder for KB
            original_filename=filename
        )
        
        # Create database record
        kb_entry = KnowledgeBase(
            title=title,
            description=description,
            source=source,
            category=category,
            file_path=file_path,
            file_type=file_type,
            status="pending",
            tags=tags or [],
            uploaded_by=uploaded_by,
        )
        
        self.db.add(kb_entry)
        await self.db.commit()
        await self.db.refresh(kb_entry)
        
        # Process the document
        await self.process_knowledge_entry(kb_entry.id)
        
        return kb_entry
    
    async def add_knowledge_from_text(
        self,
        text: str,
        title: str,
        description: str,
        source: str,
        category: str,
        uploaded_by: str,
        tags: Optional[List[str]] = None
    ) -> KnowledgeBase:
        """
        Add knowledge directly from text (no file).
        
        Useful for adding specific legal sections or summaries.
        """
        kb_entry = KnowledgeBase(
            title=title,
            description=description,
            source=source,
            category=category,
            status="pending",
            tags=tags or [],
            uploaded_by=uploaded_by,
        )
        
        self.db.add(kb_entry)
        await self.db.commit()
        await self.db.refresh(kb_entry)
        
        # Create chunks and embeddings
        chunks = chunk_text(
            text=text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
        
        # Add to vector store
        self.vector_store.add_knowledge_base_chunks(
            chunks=chunks,
            knowledge_base_id=kb_entry.id,
            title=title,
            source=source,
            category=category
        )
        
        kb_entry.chunk_count = len(chunks)
        kb_entry.status = "ready"
        
        await self.db.commit()
        await self.db.refresh(kb_entry)
        
        return kb_entry
    
    async def process_knowledge_entry(self, kb_id: str) -> KnowledgeBase:
        """
        Process a knowledge base entry: extract text and create embeddings.
        """
        kb_entry = await self.get_by_id(kb_id)
        if not kb_entry:
            raise NotFoundError("Knowledge base entry not found")
        
        if not kb_entry.file_path:
            raise ValidationError("No file associated with this entry")
        
        kb_entry.status = "processing"
        await self.db.commit()
        
        try:
            # Extract text
            result = extract_text(kb_entry.file_path, kb_entry.file_type)
            
            if result.error:
                kb_entry.status = "failed"
                await self.db.commit()
                raise ValidationError(f"Text extraction failed: {result.error}")
            
            # Create chunks
            chunks = chunk_text(
                text=result.full_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Add to vector store
            self.vector_store.add_knowledge_base_chunks(
                chunks=chunks,
                knowledge_base_id=kb_entry.id,
                title=kb_entry.title,
                source=kb_entry.source or "",
                category=kb_entry.category
            )
            
            kb_entry.chunk_count = len(chunks)
            kb_entry.status = "ready"
            
            await self.db.commit()
            await self.db.refresh(kb_entry)
            
            print(f"✅ Knowledge base entry processed: {kb_entry.title}")
            
            return kb_entry
            
        except Exception as e:
            kb_entry.status = "failed"
            await self.db.commit()
            raise
    
    # ============================================
    # RETRIEVAL
    # ============================================
    
    async def get_by_id(self, kb_id: str) -> Optional[KnowledgeBase]:
        """Get a knowledge base entry by ID."""
        stmt = select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_all(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: Optional[bool] = True
    ) -> Tuple[List[KnowledgeBase], int]:
        """List all knowledge base entries."""
        base_stmt = select(KnowledgeBase)
        
        if category:
            base_stmt = base_stmt.where(KnowledgeBase.category == category)
        
        if is_active is not None:
            base_stmt = base_stmt.where(KnowledgeBase.is_active == is_active)
        
        # Count
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Paginate
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(KnowledgeBase.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        entries = result.scalars().all()
        
        return list(entries), total
    
    async def get_categories(self) -> List[str]:
        """Get all unique categories."""
        stmt = select(KnowledgeBase.category).distinct()
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all() if row[0]]
    
    # ============================================
    # SEARCH
    # ============================================
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> List[dict]:
        """
        Search the knowledge base using semantic similarity.
        
        Args:
            query: Search query
            n_results: Number of results
            category: Optional category filter
            
        Returns:
            List of relevant chunks
        """
        return self.vector_store.search_legal_knowledge(
            query=query,
            n_results=n_results,
            category=category
        )
    
    # ============================================
    # DELETE
    # ============================================
    
    async def delete(self, kb_id: str) -> bool:
        """Delete a knowledge base entry."""
        kb_entry = await self.get_by_id(kb_id)
        if not kb_entry:
            raise NotFoundError("Knowledge base entry not found")
        
        # Delete from vector store
        self.vector_store.delete_knowledge_base_chunks(kb_id)
        
        # Delete database record
        await self.db.delete(kb_entry)
        await self.db.commit()
        
        return True
    
    # ============================================
    # STATISTICS
    # ============================================
    
    async def get_stats(self) -> dict:
        """Get knowledge base statistics."""
        # Total count
        total_stmt = select(func.count(KnowledgeBase.id))
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        # By category
        cat_stmt = select(
            KnowledgeBase.category,
            func.count(KnowledgeBase.id)
        ).group_by(KnowledgeBase.category)
        cat_result = await self.db.execute(cat_stmt)
        by_category = {row[0]: row[1] for row in cat_result.all()}
        
        # By status
        status_stmt = select(
            KnowledgeBase.status,
            func.count(KnowledgeBase.id)
        ).group_by(KnowledgeBase.status)
        status_result = await self.db.execute(status_stmt)
        by_status = {row[0]: row[1] for row in status_result.all()}
        
        # Vector store stats
        vector_stats = self.vector_store.get_collection_stats(
            self.vector_store.LEGAL_KNOWLEDGE_COLLECTION
        )
        
        return {
            "total_entries": total,
            "by_category": by_category,
            "by_status": by_status,
            "vector_store": vector_stats,
        }


def get_knowledge_base_service(db: AsyncSession) -> KnowledgeBaseService:
    """Factory function to create KnowledgeBaseService instance."""
    return KnowledgeBaseService(db)