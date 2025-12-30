# backend/app/api/documents.py
"""
Document API Routes
===================
Endpoints for document management.

Endpoints:
- POST /documents/upload - Upload a document
- GET /documents - List user's documents
- GET /documents/{id} - Get document details
- GET /documents/{id}/content - Get document text content
- GET /documents/{id}/download - Download original file
- DELETE /documents/{id} - Delete a document
- GET /documents/stats - Get document statistics
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os
import io

from app.database import get_db
from app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentChunkResponse,
)
from app.schemas.common import MessageResponse, ErrorResponse
from app.services.document_service import DocumentService
from app.api.deps import ActiveUser, DBSession
from app.core.exceptions import NotFoundError, ValidationError, FileProcessingError
from app.config import settings
from app.utils.file_processor import format_file_size
from app.services.vector_store_service import get_vector_store_service

# ============================================
# ROUTER SETUP
# ============================================
router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)


# ============================================
# HELPER FUNCTION
# ============================================
def document_to_response(doc) -> DocumentResponse:
    """Convert document model to response schema."""
    return DocumentResponse(
        id=doc.id,
        user_id=doc.user_id,
        original_name=doc.original_name,
        file_type=doc.file_type,
        file_size=doc.file_size,
        status=doc.status,
        chunk_count=doc.chunk_count,
        page_count=doc.page_count,
        word_count=doc.word_count,
        summary=doc.summary,
        error_message=doc.error_message,
        created_at=doc.created_at,
        processed_at=doc.processed_at,
        file_size_formatted=format_file_size(doc.file_size),
    )


# ============================================
# UPLOAD DOCUMENT
# ============================================
@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    response_description="Document uploaded successfully",
)
async def upload_document(
    current_user: ActiveUser,
    db: DBSession,
    file: UploadFile = File(..., description="Document file (PDF, DOCX, or TXT)"),
):
    """
    Upload a legal document for analysis.
    
    **Supported formats:** PDF, DOCX, TXT
    
    **Max file size:** 10 MB
    
    The document will be:
    1. Saved to storage
    2. Text extracted
    3. Split into chunks for AI analysis
    
    Processing happens immediately. Check the status field to confirm completion.
    """
    # Validate file
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No filename provided"
        )
    
    # Read file content
    content = await file.read()
    
    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file"
        )
    
    # Create document service and upload
    doc_service = DocumentService(db)
    
    try:
        document = await doc_service.upload_and_process(
            user_id=current_user.id,
            file_content=content,
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream"
        )
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document uploaded successfully. Status: {document.status}",
            document=document_to_response(document),
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message)
        )


# ============================================
# LIST DOCUMENTS
# ============================================
@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
    response_description="Paginated list of user's documents",
)
async def list_documents(
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        None,
        description="Filter by status (pending, processing, ready, failed)"
    ),
):
    """
    Get a paginated list of your uploaded documents.
    
    **Pagination:**
    - `page`: Page number (starts at 1)
    - `page_size`: Items per page (max 100)
    
    **Filtering:**
    - `status`: Filter by processing status
    """
    doc_service = DocumentService(db)
    
    documents, total = await doc_service.get_user_documents(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )
    
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return DocumentListResponse(
        success=True,
        documents=[document_to_response(doc) for doc in documents],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ============================================
# GET DOCUMENT DETAILS
# ============================================
@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get document details",
    response_description="Document details with chunks preview",
)
async def get_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get detailed information about a specific document.
    
    Includes a preview of the first few text chunks.
    """
    doc_service = DocumentService(db)
    
    document = await doc_service.get_document_by_id(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Get first few chunks for preview
    chunks_preview = None
    if document.status == "ready":
        chunks = await doc_service.get_document_chunks(document_id, limit=3)
        chunks_preview = [
            {
                "chunk_index": c.chunk_index,
                "content_preview": c.content[:200] + "..." if len(c.content) > 200 else c.content,
                "page": c.start_page,
            }
            for c in chunks
        ]
    
    return DocumentDetailResponse(
        success=True,
        document=document_to_response(document),
        chunks_preview=chunks_preview,
    )


# ============================================
# GET DOCUMENT CONTENT
# ============================================
@router.get(
    "/{document_id}/content",
    summary="Get document text content",
    response_description="Full text content of the document",
)
async def get_document_content(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get the full extracted text content of a document.
    
    Only available for documents with status 'ready'.
    """
    doc_service = DocumentService(db)
    
    document = await doc_service.get_document_by_id(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Current status: {document.status}"
        )
    
    # Get full text from chunks
    text = await doc_service.get_document_text(document_id)
    
    return {
        "success": True,
        "document_id": document_id,
        "original_name": document.original_name,
        "content": text,
        "word_count": document.word_count,
        "chunk_count": document.chunk_count,
    }


# ============================================
# GET DOCUMENT CHUNKS
# ============================================
@router.get(
    "/{document_id}/chunks",
    summary="Get document chunks",
    response_description="List of document chunks",
)
async def get_document_chunks(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Get the text chunks of a document.
    
    Chunks are the segments used for AI analysis.
    """
    doc_service = DocumentService(db)
    
    document = await doc_service.get_document_by_id(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if document.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready. Current status: {document.status}"
        )
    
    # Get chunks with pagination
    all_chunks = await doc_service.get_document_chunks(document_id)
    
    # Manual pagination (for simplicity)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_chunks = all_chunks[start_idx:end_idx]
    
    total = len(all_chunks)
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    
    return {
        "success": True,
        "document_id": document_id,
        "chunks": [
            DocumentChunkResponse.model_validate(chunk)
            for chunk in paginated_chunks
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


# ============================================
# DOWNLOAD DOCUMENT
# ============================================
@router.get(
    "/{document_id}/download",
    summary="Download original document",
    response_description="Original file download",
)
async def download_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Download the original uploaded document file.
    """
    doc_service = DocumentService(db)
    
    document = await doc_service.get_document_by_id(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )
    
    # Determine media type
    media_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
    }
    media_type = media_types.get(document.file_type, "application/octet-stream")
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_name,
        media_type=media_type,
    )


# ============================================
# DELETE DOCUMENT
# ============================================
@router.delete(
    "/{document_id}",
    response_model=MessageResponse,
    summary="Delete document",
    response_description="Document deleted successfully",
)
async def delete_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Delete a document and all its associated data.
    
    This action is irreversible. The original file and all text chunks
    will be permanently removed.
    """
    doc_service = DocumentService(db)
    
    try:
        await doc_service.delete_document(
            document_id=document_id,
            user_id=current_user.id
        )
        
        return MessageResponse(
            success=True,
            message="Document deleted successfully"
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )


# ============================================
# DOCUMENT STATISTICS
# ============================================
@router.get(
    "/stats/summary",
    summary="Get document statistics",
    response_description="Document usage statistics",
)
async def get_document_stats(
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get statistics about your uploaded documents.
    
    Includes:
    - Total document count
    - Documents by status
    - Total storage used
    """
    doc_service = DocumentService(db)
    
    stats = await doc_service.get_user_document_stats(current_user.id)
    
    return {
        "success": True,
        "stats": stats,
    }


# ============================================
# REPROCESS DOCUMENT
# ============================================
@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentUploadResponse,
    summary="Reprocess document",
    response_description="Document reprocessing started",
)
async def reprocess_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Reprocess a failed document.
    
    Useful if a document failed to process and you want to try again.
    """
    doc_service = DocumentService(db)
    
    document = await doc_service.get_document_by_id(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    try:
        document = await doc_service.process_document(document_id)
        
        return DocumentUploadResponse(
            success=True,
            message=f"Document reprocessed. Status: {document.status}",
            document=document_to_response(document),
        )
        
    except FileProcessingError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e.message)
        )# ============================================
# SEARCH DOCUMENT
# ============================================
@router.post(
    "/{document_id}/search",
    summary="Search within a document",
    response_description="Relevant chunks matching the query",
)
async def search_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
    query: str = Query(..., min_length=3, description="Search query"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """
    Search within a specific document using semantic similarity.
    
    This uses AI embeddings to find the most relevant sections
    of the document that match your query.
    
    **Example queries:**
    - "What are the termination clauses?"
    - "Find payment terms"
    - "Confidentiality obligations"
    """
    doc_service = DocumentService(db)
    
    try:
        results = await doc_service.search_document(
            document_id=document_id,
            user_id=current_user.id,
            query=query,
            n_results=n_results
        )
        
        return {
            "success": True,
            "query": query,
            "document_id": document_id,
            "results": results,
            "count": len(results),
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )


# ============================================
# SEARCH ALL DOCUMENTS
# ============================================
@router.post(
    "/search/all",
    summary="Search across all documents",
    response_description="Relevant chunks from all user documents",
)
async def search_all_documents(
    current_user: ActiveUser,
    db: DBSession,
    query: str = Query(..., min_length=3, description="Search query"),
    n_results: int = Query(5, ge=1, le=20, description="Number of results"),
):
    """
    Search across all your uploaded documents using semantic similarity.
    
    Returns the most relevant sections from any of your documents
    that match the query.
    """
    doc_service = DocumentService(db)
    
    results = await doc_service.search_all_documents(
        user_id=current_user.id,
        query=query,
        n_results=n_results
    )
    
    return {
        "success": True,
        "query": query,
        "results": results,
        "count": len(results),
    }