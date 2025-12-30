# backend/app/api/generate.py
"""
Document Generation API Routes
===============================
Endpoints for generating legal documents from templates.

Endpoints:
- GET /generate/templates - List templates
- GET /generate/templates/{id} - Get template details
- POST /generate/preview - Preview document
- POST /generate/create - Generate and save document
- GET /generate/documents - List generated documents
- GET /generate/documents/{id} - Get generated document
- GET /generate/documents/{id}/download - Download PDF
- DELETE /generate/documents/{id} - Delete document
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from app.database import get_db
from app.schemas.template import (
    TemplateResponse,
    TemplateDetailResponse,
    TemplateListResponse,
    GenerateDocumentRequest,
    GeneratedDocumentResponse,
    DocumentPreviewResponse,
    GenerateDocumentResponse,
)
from app.schemas.common import MessageResponse, ErrorResponse
from app.services.template_service import TemplateService
from app.services.generation_service import GenerationService
from app.api.deps import ActiveUser, DBSession
from app.core.exceptions import NotFoundError, ValidationError


# ============================================
# ROUTER SETUP
# ============================================
router = APIRouter(
    prefix="/generate",
    tags=["Document Generation"],
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
    },
)


# ============================================
# LIST TEMPLATES
# ============================================
@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List document templates",
    response_description="List of available templates",
)
async def list_templates(
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
):
    """
    List available document templates.
    
    **Categories:**
    - contracts
    - agreements
    - notices
    - letters
    - affidavits
    - deeds
    """
    template_service = TemplateService(db)
    
    templates, total = await template_service.list_templates(
        page=page,
        page_size=page_size,
        category=category,
        is_active=True
    )
    
    return TemplateListResponse(
        success=True,
        templates=[TemplateResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
    )


# ============================================
# GET TEMPLATE DETAILS
# ============================================
@router.get(
    "/templates/{template_id}",
    response_model=TemplateDetailResponse,
    summary="Get template details",
    response_description="Template details with form schema",
)
async def get_template(
    template_id: str,
    db: DBSession,
):
    """
    Get detailed information about a template.
    
    Includes:
    - Form schema (fields to fill)
    - Template preview
    - Applicable laws
    - Usage count
    """
    template_service = TemplateService(db)
    
    template = await template_service.get_template_by_id(template_id)
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    return TemplateDetailResponse.model_validate(template)


# ============================================
# PREVIEW DOCUMENT
# ============================================
@router.post(
    "/preview",
    response_model=DocumentPreviewResponse,
    summary="Preview document",
    response_description="Document preview without saving",
)
async def preview_document(
    request: GenerateDocumentRequest,
    db: DBSession,
):
    """
    Generate a preview of the document without saving.
    
    Useful for showing users what the final document will look like
    before they commit to generating it.
    """
    generation_service = GenerationService(db)
    
    try:
        preview = await generation_service.preview_document(
            template_id=request.template_id,
            form_data=request.form_data
        )
        
        return DocumentPreviewResponse(
            success=True,
            preview_text=preview["preview_text"],
            preview_html=preview.get("preview_html"),
            template_name=preview["template_name"],
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )


# ============================================
# GENERATE DOCUMENT
# ============================================
@router.post(
    "/create",
    response_model=GenerateDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate document",
    response_description="Document generated successfully",
)
async def generate_document(
    request: GenerateDocumentRequest,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Generate and save a legal document.
    
    The document will be:
    1. Generated from the template
    2. Saved to your account
    3. Available for download as PDF
    
    **Important:** All generated documents include a disclaimer that they
    should be reviewed by a qualified legal professional before use.
    """
    generation_service = GenerationService(db)
    
    try:
        document = await generation_service.generate_document(
            user_id=current_user.id,
            template_id=request.template_id,
            title=request.title,
            form_data=request.form_data
        )
        
        # Build download URL
        download_url = f"/api/v1/generate/documents/{document.id}/download"
        
        return GenerateDocumentResponse(
            success=True,
            message="Document generated successfully!",
            document=GeneratedDocumentResponse.model_validate(document),
            download_url=download_url,
        )
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.message)
        )


# ============================================
# LIST GENERATED DOCUMENTS
# ============================================
@router.get(
    "/documents",
    summary="List generated documents",
    response_description="List of user's generated documents",
)
async def list_generated_documents(
    current_user: ActiveUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List all documents you've generated.
    
    Ordered by most recent first.
    """
    generation_service = GenerationService(db)
    
    documents, total = await generation_service.list_user_documents(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "documents": [GeneratedDocumentResponse.model_validate(d) for d in documents],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


# ============================================
# GET GENERATED DOCUMENT
# ============================================
@router.get(
    "/documents/{document_id}",
    response_model=GeneratedDocumentResponse,
    summary="Get generated document",
    response_description="Document details",
)
async def get_generated_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Get details of a generated document.
    """
    generation_service = GenerationService(db)
    
    document = await generation_service.get_generated_document(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    return GeneratedDocumentResponse.model_validate(document)


# ============================================
# DOWNLOAD DOCUMENT
# ============================================
@router.get(
    "/documents/{document_id}/download",
    summary="Download document PDF",
    response_description="PDF file download",
)
async def download_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Download the generated document as a PDF.
    """
    generation_service = GenerationService(db)
    
    document = await generation_service.get_generated_document(
        document_id=document_id,
        user_id=current_user.id
    )
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.file_path or not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PDF file not found"
        )
    
    # Mark as downloaded
    await generation_service.mark_as_downloaded(document_id, current_user.id)
    
    # Return PDF file
    return FileResponse(
        path=document.file_path,
        filename=f"{document.title}.pdf",
        media_type="application/pdf",
    )


# ============================================
# DELETE DOCUMENT
# ============================================
@router.delete(
    "/documents/{document_id}",
    response_model=MessageResponse,
    summary="Delete generated document",
    response_description="Document deleted successfully",
)
async def delete_generated_document(
    document_id: str,
    current_user: ActiveUser,
    db: DBSession,
):
    """
    Delete a generated document.
    
    This will delete both the database record and the PDF file.
    This action is irreversible.
    """
    generation_service = GenerationService(db)
    
    try:
        await generation_service.delete_generated_document(
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
# GET CATEGORIES
# ============================================
@router.get(
    "/categories",
    summary="Get template categories",
    response_description="List of categories",
)
async def get_categories(db: DBSession):
    """Get all available template categories."""
    template_service = TemplateService(db)
    
    categories = await template_service.get_categories()
    
    return {
        "success": True,
        "categories": categories,
    }