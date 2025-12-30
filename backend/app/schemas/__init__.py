# backend/app/schemas/__init__.py
"""
Pydantic Schemas Package
========================
Request/Response validation schemas for the API.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserLogin,
    PasswordUpdate,
    Token,
    TokenPayload,
    AuthResponse,
)

from app.schemas.common import (
    MessageResponse,
    ErrorResponse,
    PaginatedResponse,
    HealthResponse,
)

from app.schemas.document import (
    DocumentStatus,
    FileType,
    DocumentBase,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    DocumentChunkResponse,
    AnalysisType,
    AnalysisRequest,
    AnalysisResponse,
)

from app.schemas.chat import (
    SessionType,
    MessageRole,
    ChatSessionCreate,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatSessionResponse,
    ChatSessionDetailResponse,
    ChatQueryResponse,
    ChatSessionListResponse,
)

from app.schemas.template import (
    TemplateCategory,
    FieldType,
    FormField,
    FormSchema,
    TemplateResponse,
    TemplateDetailResponse,
    TemplateListResponse,
    GenerateDocumentRequest,
    GeneratedDocumentResponse,
    DocumentPreviewResponse,
    GenerateDocumentResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserLogin",
    "PasswordUpdate",
    "Token",
    "TokenPayload",
    "AuthResponse",
    # Common schemas
    "MessageResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "HealthResponse",
    # Document schemas
    "DocumentStatus",
    "FileType",
    "DocumentBase",
    "DocumentResponse",
    "DocumentUploadResponse",
    "DocumentListResponse",
    "DocumentDetailResponse",
    "DocumentChunkResponse",
    "AnalysisType",
    "AnalysisRequest",
    "AnalysisResponse",
    # Chat schemas
    "SessionType",
    "MessageRole",
    "ChatSessionCreate",
    "ChatMessageCreate",
    "ChatMessageResponse",
    "ChatSessionResponse",
    "ChatSessionDetailResponse",
    "ChatQueryResponse",
    "ChatSessionListResponse",
    # Template schemas
    "TemplateCategory",
    "FieldType",
    "FormField",
    "FormSchema",
    "TemplateResponse",
    "TemplateDetailResponse",
    "TemplateListResponse",
    "GenerateDocumentRequest",
    "GeneratedDocumentResponse",
    "DocumentPreviewResponse",
    "GenerateDocumentResponse",
]