# backend/app/schemas/template.py
"""
Template Schemas
================
Pydantic models for legal document templates.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================
class TemplateCategory(str, Enum):
    """Template categories."""
    CONTRACTS = "contracts"
    AGREEMENTS = "agreements"
    NOTICES = "notices"
    LETTERS = "letters"
    AFFIDAVITS = "affidavits"
    DEEDS = "deeds"


class FieldType(str, Enum):
    """Form field types."""
    TEXT = "text"
    EMAIL = "email"
    NUMBER = "number"
    DATE = "date"
    SELECT = "select"
    TEXTAREA = "textarea"
    CHECKBOX = "checkbox"


# ============================================
# FORM FIELD SCHEMAS
# ============================================
class FormField(BaseModel):
    """Definition of a form field."""
    name: str = Field(..., description="Field name (variable name)")
    label: str = Field(..., description="Field label for UI")
    type: FieldType = Field(..., description="Field type")
    required: bool = Field(default=True, description="Whether field is required")
    placeholder: Optional[str] = Field(None, description="Placeholder text")
    default_value: Optional[str] = Field(None, description="Default value")
    options: Optional[List[str]] = Field(None, description="Options for select fields")
    help_text: Optional[str] = Field(None, description="Help text for users")
    validation: Optional[Dict[str, Any]] = Field(None, description="Validation rules")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "party_a_name",
                "label": "Party A (Disclosing Party)",
                "type": "text",
                "required": True,
                "placeholder": "Enter full legal name",
                "help_text": "Full name or company name of the disclosing party"
            }
        }
    }


class FormSchema(BaseModel):
    """Complete form schema for a template."""
    fields: List[FormField] = Field(..., description="List of form fields")
    sections: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional sections for grouping fields"
    )


# ============================================
# TEMPLATE SCHEMAS
# ============================================
class TemplateResponse(BaseModel):
    """Template response without body."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    category: str
    is_active: bool
    is_premium: bool
    usage_count: int
    applicable_laws: Optional[List[str]]
    form_schema: FormSchema
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class TemplateDetailResponse(BaseModel):
    """Template response with body."""
    id: str
    name: str
    slug: str
    description: Optional[str]
    category: str
    template_body: str
    form_schema: FormSchema
    is_active: bool
    is_premium: bool
    usage_count: int
    applicable_laws: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class TemplateListResponse(BaseModel):
    """Paginated list of templates."""
    success: bool = True
    templates: List[TemplateResponse]
    total: int
    page: int
    page_size: int


# ============================================
# GENERATION SCHEMAS
# ============================================
class GenerateDocumentRequest(BaseModel):
    """Request to generate a document from template."""
    template_id: str = Field(..., description="Template ID")
    title: str = Field(..., min_length=1, max_length=255, description="Document title")
    form_data: Dict[str, Any] = Field(..., description="Form field values")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "template_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "NDA - Acme Corp & John Doe",
                "form_data": {
                    "party_a_name": "Acme Corporation",
                    "party_b_name": "John Doe",
                    "agreement_date": "2024-01-15",
                    "jurisdiction": "Delhi"
                }
            }
        }
    }


class GeneratedDocumentResponse(BaseModel):
    """Generated document response."""
    id: str
    user_id: str
    template_id: str
    title: str
    form_data: Dict[str, Any]
    generated_text: str
    file_path: Optional[str]
    is_downloaded: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True
    }


class DocumentPreviewResponse(BaseModel):
    """Preview of generated document."""
    success: bool = True
    preview_text: str
    preview_html: Optional[str] = None
    template_name: str


class GenerateDocumentResponse(BaseModel):
    """Response after document generation."""
    success: bool = True
    message: str
    document: GeneratedDocumentResponse
    download_url: str