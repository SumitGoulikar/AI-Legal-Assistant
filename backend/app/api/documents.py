# backend/app/api/documents.py
"""
Document API Routes
===================
Endpoints for document management and analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
import os
from pydantic import BaseModel
from app.utils.file_processor import extract_text
import shutil
import tempfile

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
from app.services.llm_service import get_llm_service
from app.api.deps import ActiveUser, DBSession
from app.core.exceptions import NotFoundError, ValidationError, FileProcessingError
from app.utils.file_processor import format_file_size

router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)

# --- REQUEST MODELS ---
class AnalyzeRequest(BaseModel):
    text: str
    analysis_type: str = "summary"

# --- HELPER FUNCTION ---
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
)
async def upload_document(
    current_user: ActiveUser,
    db: DBSession,
    file: UploadFile = File(..., description="Document file (PDF, DOCX, or TXT)"),
):
    """Upload a legal document for analysis."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    content = await file.read()
    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Empty file")
    
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
        raise HTTPException(status_code=400, detail=str(e))
    except FileProcessingError as e:
        raise HTTPException(status_code=422, detail=str(e))

# ============================================
# LIST DOCUMENTS
# ============================================
@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
)
async def list_documents(
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
):
    """Get a paginated list of documents."""
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
@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """Get detailed information about a document."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document_by_id(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    chunks_preview = None
    if document.status == "ready":
        chunks = await doc_service.get_document_chunks(document_id, limit=3)
        chunks_preview = [
            {
                "chunk_index": c.chunk_index,
                "content_preview": c.content[:200] + "...",
                "page": c.start_page,
            } for c in chunks
        ]
    
    return DocumentDetailResponse(
        success=True,
        document=document_to_response(document),
        chunks_preview=chunks_preview,
    )

# ============================================
# DOWNLOAD DOCUMENT
# ============================================
@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """Download the original uploaded document."""
    doc_service = DocumentService(db)
    document = await doc_service.get_document_by_id(document_id, current_user.id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not os.path.exists(document.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=document.file_path,
        filename=document.original_name,
        media_type="application/octet-stream",
    )

# ============================================
# DELETE DOCUMENT
# ============================================
@router.delete("/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """Delete a document permanently."""
    doc_service = DocumentService(db)
    try:
        await doc_service.delete_document(document_id, current_user.id)
        return MessageResponse(success=True, message="Document deleted successfully")
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Document not found")

# ============================================
# TEXT ANALYSIS (New Feature)
# ============================================
@router.post("/analyze_text")
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze legal text using the LLM directly.
    Doesn't require file upload or storage.
    """
    llm = get_llm_service()
    
    prompts = {
        "summary": "Please provide a clear and concise summary of the following legal text:",
        "risks": "Identify any potential legal risks, liabilities, or unfair clauses in this text:",
        "clauses": "List and explain the key clauses found in this text:"
    }
    
    instruction = prompts.get(request.analysis_type, prompts["summary"])
    
    # Truncate text to avoid token limits (approx 15k chars ~ 3-4k tokens)
    safe_text = request.text[:15000]
    
    system_prompt = "You are an expert legal AI assistant. Analyze the provided text professionally."
    user_prompt = f"{instruction}\n\n---\n{safe_text}\n---"
    
    response = await llm.generate_response(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.3,
        max_tokens=1000
    )
    
    return {"result": response["response"]}

# ============================================
# SEARCH WITHIN DOCUMENT
# ============================================
@router.post("/{document_id}/search")
async def search_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
    query: str = Query(..., min_length=3),
    n_results: int = Query(5, ge=1, le=20),
):
    """Search within a specific document."""
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
        raise HTTPException(status_code=404, detail="Document not found")
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.post("/extract_text")
async def extract_document_text(
    file: UploadFile = File(...)
):
    # 1. Determine file extension
    filename = file.filename
    ext = filename.split('.')[-1].lower()
    
    if ext not in ['pdf', 'docx', 'txt']:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # 2. Save to temp file
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        # 3. Extract Text
        # Note: extract_text returns a dict or object depending on your implementation
        # Let's handle the dict return from the code above
        result = extract_text(tmp_path, ext)
        
        # Cleanup temp file
        os.remove(tmp_path)
        
        if result.get("error"):
             raise HTTPException(status_code=422, detail=result["error"])
             
        return {"text": result["full_text"]}

    except Exception as e:
        # Ensure cleanup even on error
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)