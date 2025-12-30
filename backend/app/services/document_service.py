# backend/app/services/document_service.py
"""
Document Service
================
Business logic for document operations.

Updated to include vector embeddings for RAG.
"""

from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentChunk, DocumentStatus
from app.utils.file_processor import (
    validate_file_extension,
    validate_file_size,
    save_upload_file,
    delete_file,
    get_file_content,
    extract_text,
    chunk_text,
    assign_pages_to_chunks,
    format_file_size,
)
from app.services.vector_store_service import get_vector_store_service
from app.core.exceptions import NotFoundError, ValidationError, FileProcessingError
from app.config import settings


class DocumentService:
    """
    Document service handling file operations.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.vector_store = get_vector_store_service()
    
    # ============================================
    # DOCUMENT UPLOAD
    # ============================================
    
    async def upload_document(
        self,
        user_id: str,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Document:
        """
        Upload and process a new document.
        
        Args:
            user_id: ID of the uploading user
            file_content: Raw file bytes
            filename: Original filename
            content_type: MIME type of file
            
        Returns:
            Created document record
        """
        # Validate file
        file_type = validate_file_extension(filename)
        file_size = len(file_content)
        validate_file_size(file_size)
        
        # Save file to disk
        stored_filename, file_path = await save_upload_file(
            file_content=file_content,
            user_id=user_id,
            original_filename=filename
        )
        
        # Create document record
        document = Document(
            user_id=user_id,
            filename=stored_filename,
            original_name=filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status=DocumentStatus.PENDING.value,
        )
        
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        
        return document
    
    async def process_document(self, document_id: str) -> Document:
        """
        Process a document: extract text, create chunks, and generate embeddings.
        
        Args:
            document_id: ID of document to process
            
        Returns:
            Updated document record
        """
        # Get document
        document = await self.get_document_by_id(document_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Update status to processing
        document.status = DocumentStatus.PROCESSING.value
        await self.db.commit()
        
        try:
            # Extract text
            print(f"📄 Extracting text from: {document.original_name}")
            result = extract_text(document.file_path, document.file_type)
            
            if result.error:
                document.status = DocumentStatus.FAILED.value
                document.error_message = result.error
                await self.db.commit()
                return document
            
            # Update document metadata
            document.page_count = result.page_count
            document.word_count = result.word_count
            
            # Create chunks
            print(f"🔪 Chunking text...")
            chunks = chunk_text(
                text=result.full_text,
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )
            
            # Assign page numbers to chunks
            chunks = assign_pages_to_chunks(chunks, result.pages)
            
            # Save chunks to database
            print(f"💾 Saving {len(chunks)} chunks to database...")
            db_chunks = []
            for chunk_data in chunks:
                chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    start_char=chunk_data.get("start_char"),
                    end_char=chunk_data.get("start_char", 0) + chunk_data["char_count"],
                    start_page=chunk_data.get("start_page"),
                    end_page=chunk_data.get("end_page"),
                )
                self.db.add(chunk)
                db_chunks.append(chunk_data)
            
            # Commit chunks to database first
            await self.db.commit()
            
            # Generate and store embeddings in vector store
            print(f"🧠 Generating embeddings for {len(chunks)} chunks...")
            chroma_ids = self.vector_store.add_document_chunks(
                chunks=chunks,
                user_id=document.user_id,
                document_id=document.id,
                document_name=document.original_name
            )
            
            # Update chunk records with chroma IDs
            stmt = select(DocumentChunk).where(
                DocumentChunk.document_id == document.id
            ).order_by(DocumentChunk.chunk_index)
            result_chunks = await self.db.execute(stmt)
            db_chunk_records = result_chunks.scalars().all()
            
            for i, db_chunk in enumerate(db_chunk_records):
                if i < len(chroma_ids):
                    db_chunk.chroma_id = chroma_ids[i]
            
            document.chunk_count = len(chunks)
            document.status = DocumentStatus.READY.value
            document.processed_at = datetime.utcnow()
            
            await self.db.commit()
            await self.db.refresh(document)
            
            print(f"✅ Document processed successfully: {document.original_name}")
            
            return document
            
        except Exception as e:
            print(f"❌ Error processing document: {e}")
            document.status = DocumentStatus.FAILED.value
            document.error_message = str(e)
            await self.db.commit()
            raise FileProcessingError(f"Failed to process document: {str(e)}")
    
    async def upload_and_process(
        self,
        user_id: str,
        file_content: bytes,
        filename: str,
        content_type: str
    ) -> Document:
        """
        Upload and immediately process a document.
        """
        document = await self.upload_document(
            user_id=user_id,
            file_content=file_content,
            filename=filename,
            content_type=content_type
        )
        
        try:
            document = await self.process_document(document.id)
        except Exception as e:
            print(f"Document processing failed: {e}")
        
        return document
    
    # ============================================
    # DOCUMENT RETRIEVAL
    # ============================================
    
    async def get_document_by_id(
        self,
        document_id: str,
        user_id: Optional[str] = None
    ) -> Optional[Document]:
        """Get a document by ID."""
        stmt = select(Document).where(Document.id == document_id)
        
        if user_id:
            stmt = stmt.where(Document.user_id == user_id)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_documents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None
    ) -> Tuple[List[Document], int]:
        """Get paginated list of user's documents."""
        base_stmt = select(Document).where(Document.user_id == user_id)
        
        if status_filter:
            base_stmt = base_stmt.where(Document.status == status_filter)
        
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(Document.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        documents = result.scalars().all()
        
        return list(documents), total
    
    async def get_document_with_chunks(
        self,
        document_id: str,
        user_id: str
    ) -> Optional[Document]:
        """Get document with its chunks loaded."""
        stmt = (
            select(Document)
            .options(selectinload(Document.chunks))
            .where(Document.id == document_id)
            .where(Document.user_id == user_id)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ============================================
    # DOCUMENT SEARCH (Vector-based)
    # ============================================
    
    async def search_document(
        self,
        document_id: str,
        user_id: str,
        query: str,
        n_results: int = 5
    ) -> List[dict]:
        """
        Search within a specific document using semantic similarity.
        
        Args:
            document_id: Document to search
            user_id: User's ID
            query: Search query
            n_results: Number of results
            
        Returns:
            List of relevant chunks with similarity scores
        """
        # Verify document belongs to user
        document = await self.get_document_by_id(document_id, user_id)
        if not document:
            raise NotFoundError("Document not found")
        
        if document.status != "ready":
            raise ValidationError("Document is not ready for search")
        
        # Search in vector store
        results = self.vector_store.search_user_documents(
            query=query,
            user_id=user_id,
            document_id=document_id,
            n_results=n_results
        )
        
        return results
    
    async def search_all_documents(
        self,
        user_id: str,
        query: str,
        n_results: int = 5
    ) -> List[dict]:
        """
        Search across all user's documents.
        
        Args:
            user_id: User's ID
            query: Search query
            n_results: Number of results
            
        Returns:
            List of relevant chunks from all documents
        """
        results = self.vector_store.search_user_documents(
            query=query,
            user_id=user_id,
            n_results=n_results
        )
        
        return results
    
    # ============================================
    # DOCUMENT CHUNKS
    # ============================================
    
    async def get_document_chunks(
        self,
        document_id: str,
        limit: Optional[int] = None
    ) -> List[DocumentChunk]:
        """Get chunks for a document."""
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        
        if limit:
            stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_document_text(self, document_id: str) -> str:
        """Get full text of a document from its chunks."""
        chunks = await self.get_document_chunks(document_id)
        return "\n\n".join(chunk.content for chunk in chunks)
    
    # ============================================
    # DOCUMENT DELETION
    # ============================================
    
    async def delete_document(
        self,
        document_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a document and its associated data including embeddings.
        """
        document = await self.get_document_by_id(document_id, user_id)
        if not document:
            raise NotFoundError("Document not found")
        
        # Delete from vector store first
        self.vector_store.delete_document_chunks(document_id, user_id)
        
        # Delete file from disk
        await delete_file(document.file_path)
        
        # Delete chunks from database
        await self.db.execute(
            delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        )
        
        # Delete document record
        await self.db.delete(document)
        await self.db.commit()
        
        return True
    
    # ============================================
    # STATISTICS
    # ============================================
    
    async def get_user_document_stats(self, user_id: str) -> dict:
        """Get document statistics for a user."""
        total_stmt = select(func.count(Document.id)).where(
            Document.user_id == user_id
        )
        total_result = await self.db.execute(total_stmt)
        total = total_result.scalar() or 0
        
        status_stmt = select(
            Document.status,
            func.count(Document.id)
        ).where(
            Document.user_id == user_id
        ).group_by(Document.status)
        
        status_result = await self.db.execute(status_stmt)
        status_counts = {row[0]: row[1] for row in status_result.all()}
        
        size_stmt = select(func.sum(Document.file_size)).where(
            Document.user_id == user_id
        )
        size_result = await self.db.execute(size_stmt)
        total_size = size_result.scalar() or 0
        
        # Get embedding count from vector store
        embedding_count = self.vector_store.get_user_document_count(user_id)
        
        return {
            "total_documents": total,
            "by_status": {
                "pending": status_counts.get("pending", 0),
                "processing": status_counts.get("processing", 0),
                "ready": status_counts.get("ready", 0),
                "failed": status_counts.get("failed", 0),
            },
            "total_size_bytes": total_size,
            "total_size_formatted": format_file_size(total_size),
            "total_embeddings": embedding_count,
        }


def get_document_service(db: AsyncSession) -> DocumentService:
    """Factory function to create DocumentService instance."""
    return DocumentService(db)