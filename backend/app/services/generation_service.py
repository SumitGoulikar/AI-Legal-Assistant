# backend/app/services/generation_service.py
"""
Document Generation Service
============================
Generates legal documents from templates.

Process:
1. Get template
2. Validate form data
3. Fill template with user data
4. Optionally enhance with LLM
5. Generate PDF
6. Save to database
"""

from typing import Dict, Any, Optional, List, Tuple
import re
import uuid
from datetime import datetime
from pathlib import Path
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.template import Template, GeneratedDocument
from app.services.template_service import TemplateService
from app.utils.pdf_generator import generate_legal_pdf
from app.core.exceptions import NotFoundError, ValidationError
from app.config import settings


class GenerationService:
    """Service for generating legal documents from templates."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
        self.template_service = TemplateService(db)
    
    # ============================================
    # DOCUMENT GENERATION
    # ============================================
    
    async def generate_document(
        self,
        user_id: str,
        template_id: str,
        title: str,
        form_data: Dict[str, Any]
    ) -> GeneratedDocument:
        """
        Generate a document from a template.
        
        Args:
            user_id: User's ID
            template_id: Template to use
            title: Document title
            form_data: Form field values
            
        Returns:
            Generated document record
        """
        # Get template
        template = await self.template_service.get_template_by_id(template_id)
        if not template:
            raise NotFoundError("Template not found")
        
        if not template.is_active:
            raise ValidationError("Template is not active")
        
        # Validate form data
        self._validate_form_data(template, form_data)
        
        # Fill template
        generated_text = self._fill_template(template.template_body, form_data)
        
        # Create database record
        doc = GeneratedDocument(
            user_id=user_id,
            template_id=template_id,
            title=title,
            form_data=form_data,
            generated_text=generated_text,
            is_downloaded=False,
        )
        
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        
        # Generate PDF
        try:
            pdf_path = await self._generate_pdf(doc, template.name)
            doc.file_path = pdf_path
            await self.db.commit()
        except Exception as e:
            print(f"Error generating PDF: {e}")
            # Document still saved, just no PDF
        
        # Increment template usage
        await self.template_service.increment_usage(template_id)
        
        return doc
    
    async def preview_document(
        self,
        template_id: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a preview without saving.
        
        Args:
            template_id: Template to use
            form_data: Form field values
            
        Returns:
            Dict with preview text and HTML
        """
        # Get template
        template = await self.template_service.get_template_by_id(template_id)
        if not template:
            raise NotFoundError("Template not found")
        
        # Fill template
        preview_text = self._fill_template(template.template_body, form_data)
        
        # Convert to HTML (simple conversion)
        preview_html = self._text_to_html(preview_text)
        
        return {
            "template_name": template.name,
            "preview_text": preview_text,
            "preview_html": preview_html,
        }
    
    # ============================================
    # GENERATED DOCUMENT RETRIEVAL
    # ============================================
    
    async def get_generated_document(
        self,
        document_id: str,
        user_id: str
    ) -> Optional[GeneratedDocument]:
        """Get a generated document by ID."""
        stmt = (
            select(GeneratedDocument)
            .where(GeneratedDocument.id == document_id)
            .where(GeneratedDocument.user_id == user_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_user_documents(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[GeneratedDocument], int]:
        """List user's generated documents."""
        base_stmt = select(GeneratedDocument).where(
            GeneratedDocument.user_id == user_id
        )
        
        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = (
            base_stmt
            .order_by(GeneratedDocument.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.db.execute(stmt)
        documents = result.scalars().all()
        
        return list(documents), total
    
    async def mark_as_downloaded(self, document_id: str, user_id: str) -> None:
        """Mark a document as downloaded."""
        doc = await self.get_generated_document(document_id, user_id)
        if doc:
            doc.is_downloaded = True
            await self.db.commit()
    
    async def delete_generated_document(
        self,
        document_id: str,
        user_id: str
    ) -> bool:
        """Delete a generated document."""
        doc = await self.get_generated_document(document_id, user_id)
        if not doc:
            raise NotFoundError("Document not found")
        
        # Delete PDF file if exists
        if doc.file_path and Path(doc.file_path).exists():
            Path(doc.file_path).unlink()
        
        await self.db.delete(doc)
        await self.db.commit()
        
        return True
    
    # ============================================
    # HELPER METHODS
    # ============================================
    
    def _validate_form_data(self, template: Template, form_data: Dict[str, Any]) -> None:
        """
        Validate form data against template schema.
        
        Args:
            template: The template
            form_data: User-provided form data
            
        Raises:
            ValidationError: If validation fails
        """
        schema = template.form_schema
        fields = schema.get("fields", [])
        
        # Check required fields
        for field in fields:
            field_name = field.get("name")
            is_required = field.get("required", True)
            
            if is_required and field_name not in form_data:
                raise ValidationError(f"Required field missing: {field.get('label', field_name)}")
            
            if is_required and not form_data.get(field_name):
                raise ValidationError(f"Required field is empty: {field.get('label', field_name)}")
    
    def _fill_template(self, template_body: str, form_data: Dict[str, Any]) -> str:
        """
        Fill template placeholders with form data.
        
        Args:
            template_body: Template text with {{placeholders}}
            form_data: Form field values
            
        Returns:
            Filled template text
        """
        result = template_body
        
        # Replace all {{field_name}} with values
        for key, value in form_data.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        # Check for any remaining placeholders
        remaining = re.findall(r'\{\{([^}]+)\}\}', result)
        if remaining:
            print(f"Warning: Unfilled placeholders: {remaining}")
        
        return result
    
    def _text_to_html(self, text: str) -> str:
        """
        Convert plain text to simple HTML.
        
        Args:
            text: Plain text
            
        Returns:
            HTML formatted text
        """
        # Simple conversion
        html = text.replace('\n\n', '</p><p>')
        html = html.replace('\n', '<br>')
        html = f'<div class="document-preview"><p>{html}</p></div>'
        
        # Bold uppercase headings
        html = re.sub(
            r'<p>([A-Z][A-Z\s]+)</p>',
            r'<h3>\1</h3>',
            html
        )
        
        return html
    
    async def _generate_pdf(self, doc: GeneratedDocument, template_name: str) -> str:
        """
        Generate PDF from generated document.
        
        Args:
            doc: Generated document record
            template_name: Name of template used
            
        Returns:
            Path to generated PDF file
        """
        # Create filename
        filename = f"{uuid.uuid4().hex[:16]}.pdf"
        output_dir = Path(settings.GENERATED_DIR) / doc.user_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / filename
        
        # Generate PDF
        metadata = {
            "author": "AI Legal Assistant",
            "subject": template_name,
            "date": datetime.now().strftime("%d %B %Y"),
        }
        
        generate_legal_pdf(
            content=doc.generated_text,
            output_path=str(output_path),
            title=doc.title,
            metadata=metadata
        )
        
        return str(output_path)


def get_generation_service(db: AsyncSession) -> GenerationService:
    """Factory function to create GenerationService instance."""
    return GenerationService(db)