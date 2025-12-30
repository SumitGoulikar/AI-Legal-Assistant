# backend/app/schemas/document.py
"""
Document Schemas
================
Pydantic models for document-related request/response validation.

Schemas:
- DocumentCreate: Metadata for uploaded documents
- DocumentResponse: Document data returned to clients
- DocumentListResponse: Paginated list of documents
- DocumentUploadResponse: Response after successful upload
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================
class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class FileType(str, Enum):
    """Supported file types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"


# ============================================
# BASE SCHEMA
# ============================================
class DocumentBase(BaseModel):
    """Base document schema with common fields."""
    original_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File extension")
    file_size: int = Field(..., description="File size in bytes")


# ============================================
# RESPONSE SCHEMAS
# ============================================
class DocumentResponse(BaseModel):
    """
    Document data returned in API responses.
    """
    id: str = Field(..., description="Unique document ID")
    user_id: str = Field(..., description="Owner's user ID")
    original_name: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (pdf, docx, txt)")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Processing status")
    chunk_count: int = Field(default=0, description="Number of text chunks")
    page_count: Optional[int] = Field(None, description="Number of pages (PDFs)")
    word_count: Optional[int] = Field(None, description="Approximate word count")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    error_message: Optional[str] = Field(None, description="Error if processing failed")
    created_at: datetime = Field(..., description="Upload timestamp")
    processed_at: Optional[datetime] = Field(None, description="Processing completion time")
    
    # Computed fields
    file_size_formatted: Optional[str] = Field(None, description="Human-readable file size")
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "123e4567-e89b-12d3-a456-426614174000",
                "original_name": "contract.pdf",
                "file_type": "pdf",
                "file_size": 102400,
                "status": "ready",
                "chunk_count": 15,
                "page_count": 5,
                "word_count": 2500,
                "summary": "This is a service agreement between...",
                "created_at": "2024-01-15T10:30:00Z",
                "processed_at": "2024-01-15T10:30:05Z",
                "file_size_formatted": "100.0 KB"
            }
        }
    }


class DocumentUploadResponse(BaseModel):
    """Response after successful document upload."""
    success: bool = True
    message: str = Field(..., description="Status message")
    document: DocumentResponse = Field(..., description="Uploaded document data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Document uploaded successfully. Processing started.",
                "document": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "original_name": "contract.pdf",
                    "file_type": "pdf",
                    "file_size": 102400,
                    "status": "processing"
                }
            }
        }
    }


class DocumentListResponse(BaseModel):
    """Paginated list of documents."""
    success: bool = True
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total: int = Field(..., description="Total number of documents")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


class DocumentDetailResponse(BaseModel):
    """Detailed document response with chunks info."""
    success: bool = True
    document: DocumentResponse = Field(..., description="Document data")
    chunks_preview: Optional[List[dict]] = Field(
        None, 
        description="Preview of first few chunks"
    )


# ============================================
# DOCUMENT CHUNK SCHEMAS
# ============================================
class DocumentChunkResponse(BaseModel):
    """Document chunk data."""
    id: str = Field(..., description="Chunk ID")
    chunk_index: int = Field(..., description="Position in document")
    content: str = Field(..., description="Chunk text content")
    start_page: Optional[int] = Field(None, description="Starting page")
    end_page: Optional[int] = Field(None, description="Ending page")
    
    model_config = {
        "from_attributes": True
    }


# ============================================
# ANALYSIS SCHEMAS
# ============================================
class AnalysisType(str, Enum):
    """Types of document analysis."""
    SUMMARY = "summary"
    KEY_CLAUSES = "key_clauses"
    RISKS = "risks"
    PARTIES = "parties"
    DATES = "dates"
    OBLIGATIONS = "obligations"


class AnalysisRequest(BaseModel):
    """Request for document analysis."""
    analysis_type: AnalysisType = Field(
        ..., 
        description="Type of analysis to perform"
    )
    custom_query: Optional[str] = Field(
        None,
        description="Custom analysis query"
    )


class AnalysisResponse(BaseModel):
    """Response from document analysis."""
    success: bool = True
    document_id: str = Field(..., description="Analyzed document ID")
    analysis_type: str = Field(..., description="Type of analysis performed")
    result: str = Field(..., description="Analysis result")
    sources: Optional[List[dict]] = Field(
        None,
        description="Source chunks used for analysis"
    )
    disclaimer: str = Field(
        default="This analysis is generated by AI and should be reviewed by a legal professional."
    )