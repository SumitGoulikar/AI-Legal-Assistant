# backend/app/api/admin.py
"""
Admin API Routes
================
Endpoints for admin management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db
from app.api.deps import AdminUser, DBSession
from app.services.admin_service import AdminService
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.user import UserResponse
from app.schemas.common import MessageResponse

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    responses={403: {"description": "Not authorized"}},
)

@router.get("/stats", summary="Get system stats")
async def get_system_stats(
    current_user: AdminUser,
    db: DBSession,
):
    """Get overall system statistics (Admin only)."""
    admin_service = AdminService(db)
    return await admin_service.get_system_stats()

@router.get("/users", response_model=List[UserResponse], summary="List users")
async def list_users(
    current_user: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List all registered users (Admin only)."""
    admin_service = AdminService(db)
    users, total = await admin_service.list_users(page, page_size)
    return [UserResponse.model_validate(u) for u in users]

# --- KNOWLEDGE BASE MANAGEMENT ---

@router.post("/knowledge-base/upload", summary="Upload to Knowledge Base")
async def upload_knowledge_base(
    current_user: AdminUser,
    db: DBSession,
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    source: str = Form("Manual Upload"),
):
    """Upload a document to the shared Knowledge Base (Admin only)."""
    kb_service = KnowledgeBaseService(db)
    
    # Read file content
    content = await file.read()
    
    try:
        kb_entry = await kb_service.add_knowledge_from_file(
            file_content=content,
            filename=file.filename,
            title=title,
            description=description,
            source=source,
            category=category,
            uploaded_by=current_user.id
        )
        
        return {
            "success": True,
            "message": "Knowledge base entry added successfully",
            "id": kb_entry.id,
            "status": kb_entry.status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/knowledge-base", summary="List Knowledge Base")
async def list_knowledge_base(
    current_user: AdminUser,
    db: DBSession,
    category: Optional[str] = None
):
    """List all knowledge base entries."""
    kb_service = KnowledgeBaseService(db)
    entries, total = await kb_service.list_all(category=category, page_size=100)
    
    return {
        "success": True,
        "total": total,
        "entries": [entry.to_dict() for entry in entries]
    }

@router.delete("/knowledge-base/{kb_id}", summary="Delete KB Entry")
async def delete_kb_entry(
    kb_id: str,
    current_user: AdminUser,
    db: DBSession,
):
    """Delete an entry from the Knowledge Base."""
    kb_service = KnowledgeBaseService(db)
    await kb_service.delete(kb_id)
    return {"success": True, "message": "Deleted successfully"}