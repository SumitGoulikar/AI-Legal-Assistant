# backend/app/models/template.py
"""
Template and Generated Document Models
======================================
Models for legal document templates and user-generated documents.

Template: Predefined legal document templates (NDA, agreements, etc.)
GeneratedDocument: Documents created by users from templates

Template Structure:
- template_body: The document text with placeholders like {{party_a_name}}
- form_schema: JSON schema defining the form fields
- category: For organizing templates (contracts, notices, etc.)
"""

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Boolean, func
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class Template(Base):
    """
    Legal document template.
    
    Stores:
    - Template content with placeholders
    - Form schema for user input
    - Metadata (category, description)
    
    Form Schema Example:
    {
        "fields": [
            {
                "name": "party_a_name",
                "label": "Party A (Disclosing Party)",
                "type": "text",
                "required": true,
                "placeholder": "Enter company/person name"
            },
            {
                "name": "agreement_date",
                "label": "Agreement Date",
                "type": "date",
                "required": true
            },
            {
                "name": "jurisdiction",
                "label": "Jurisdiction",
                "type": "select",
                "options": ["Delhi", "Mumbai", "Bangalore", ...],
                "required": true
            }
        ]
    }
    """
    
    __tablename__ = "templates"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True
    )
    
    # ============================================
    # TEMPLATE METADATA
    # ============================================
    name = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Template name (e.g., 'Non-Disclosure Agreement')"
    )
    
    slug = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="URL-friendly identifier (e.g., 'nda')"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Description of when to use this template"
    )
    
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Category: contracts, agreements, notices, letters"
    )
    
    # ============================================
    # TEMPLATE CONTENT
    # ============================================
    template_body = Column(
        Text,
        nullable=False,
        comment="Template text with {{placeholders}}"
    )
    
    form_schema = Column(
        JSON,
        nullable=False,
        comment="JSON schema defining form fields"
    )
    
    # ============================================
    # STATUS FLAGS
    # ============================================
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether template is available for use"
    )
    
    is_premium = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Premium template (future feature)"
    )
    
    # ============================================
    # STATISTICS
    # ============================================
    usage_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of times this template was used"
    )
    
    # ============================================
    # INDIAN LEGAL CONTEXT
    # ============================================
    applicable_laws = Column(
        JSON,
        nullable=True,
        comment="Relevant Indian laws (e.g., ['Indian Contract Act, 1872'])"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    generated_documents = relationship(
        "GeneratedDocument",
        back_populates="template",
        lazy="selectin"
    )
    
    # ============================================
    # METHODS
    # ============================================
    def __repr__(self) -> str:
        return f"<Template(id={self.id}, name={self.name}, category={self.category})>"
    
    def to_dict(self, include_body: bool = False) -> dict:
        result = {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "category": self.category,
            "form_schema": self.form_schema,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "applicable_laws": self.applicable_laws,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_body:
            result["template_body"] = self.template_body
        return result


class GeneratedDocument(Base):
    """
    User-generated legal document.
    
    Created when a user fills out a template form.
    Stores:
    - Reference to template used
    - User-provided form values
    - Generated document text
    - PDF file path (if generated)
    """
    
    __tablename__ = "generated_documents"
    
    # ============================================
    # PRIMARY KEY
    # ============================================
    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        nullable=False,
        index=True
    )
    
    # ============================================
    # FOREIGN KEYS
    # ============================================
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    template_id = Column(
        String(36),
        ForeignKey("templates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # ============================================
    # DOCUMENT METADATA
    # ============================================
    title = Column(
        String(255),
        nullable=False,
        comment="User-provided document title"
    )
    
    # ============================================
    # GENERATION DATA
    # ============================================
    form_data = Column(
        JSON,
        nullable=False,
        comment="User-provided form values"
    )
    
    generated_text = Column(
        Text,
        nullable=False,
        comment="The generated document content"
    )
    
    # ============================================
    # FILE STORAGE
    # ============================================
    file_path = Column(
        String(500),
        nullable=True,
        comment="Path to generated PDF file"
    )
    
    # ============================================
    # STATUS
    # ============================================
    is_downloaded = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has downloaded this document"
    )
    
    # ============================================
    # TIMESTAMPS
    # ============================================
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # ============================================
    # RELATIONSHIPS
    # ============================================
    owner = relationship(
        "User",
        back_populates="generated_documents"
    )
    
    template = relationship(
        "Template",
        back_populates="generated_documents"
    )
    
    # ============================================
    # METHODS
    # ============================================
    def __repr__(self) -> str:
        return f"<GeneratedDocument(id={self.id}, title={self.title})>"
    
    def to_dict(self, include_text: bool = False) -> dict:
        result = {
            "id": self.id,
            "user_id": self.user_id,
            "template_id": self.template_id,
            "title": self.title,
            "form_data": self.form_data,
            "file_path": self.file_path,
            "is_downloaded": self.is_downloaded,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_text:
            result["generated_text"] = self.generated_text
        return result