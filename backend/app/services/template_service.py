# backend/app/services/template_service.py
"""
Template Service
================
Manages legal document templates.

Responsibilities:
- Load and manage templates
- Retrieve templates by category
- Track usage statistics
"""

from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import json
from pathlib import Path

from app.models.template import Template
from app.core.exceptions import NotFoundError


class TemplateService:
    """Service for managing document templates."""
    
    def __init__(self, db: AsyncSession):
        """
        Initialize with database session.
        
        Args:
            db: Async database session
        """
        self.db = db
    
    # ============================================
    # TEMPLATE RETRIEVAL
    # ============================================
    
    async def get_template_by_id(self, template_id: str) -> Optional[Template]:
        """Get a template by ID."""
        stmt = select(Template).where(Template.id == template_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_template_by_slug(self, slug: str) -> Optional[Template]:
        """Get a template by slug."""
        stmt = select(Template).where(Template.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def list_templates(
        self,
        page: int = 1,
        page_size: int = 20,
        category: Optional[str] = None,
        is_active: bool = True
    ) -> Tuple[List[Template], int]:
        """
        List templates with pagination.
        
        Args:
            page: Page number
            page_size: Items per page
            category: Optional category filter
            is_active: Filter by active status
            
        Returns:
            Tuple of (templates list, total count)
        """
        base_stmt = select(Template).where(Template.is_active == is_active)
        
        if category:
            base_stmt = base_stmt.where(Template.category == category)
        
        # Count total
        count_stmt = select(func.count()).select_from(base_stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        stmt = base_stmt.order_by(Template.name).offset(offset).limit(page_size)
        
        result = await self.db.execute(stmt)
        templates = result.scalars().all()
        
        return list(templates), total
    
    async def get_categories(self) -> List[str]:
        """Get all unique template categories."""
        stmt = select(Template.category).distinct()
        result = await self.db.execute(stmt)
        return [row[0] for row in result.all() if row[0]]
    
    # ============================================
    # TEMPLATE USAGE
    # ============================================
    
    async def increment_usage(self, template_id: str) -> None:
        """Increment usage count for a template."""
        template = await self.get_template_by_id(template_id)
        if template:
            template.usage_count += 1
            await self.db.commit()
    
    # ============================================
    # TEMPLATE CREATION
    # ============================================
    
    async def create_template_from_dict(self, template_data: dict) -> Template:
        """
        Create a template from a dictionary.
        
        Args:
            template_data: Template data from JSON file
            
        Returns:
            Created template
        """
        # Check if template already exists
        existing = await self.get_template_by_slug(template_data["slug"])
        if existing:
            return existing
        
        template = Template(
            name=template_data["name"],
            slug=template_data["slug"],
            description=template_data.get("description"),
            category=template_data["category"],
            template_body=template_data["template_body"],
            form_schema=template_data["form_schema"],
            applicable_laws=template_data.get("applicable_laws"),
            is_active=True,
        )
        
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        
        return template
    
    async def load_templates_from_directory(self, directory: str) -> int:
        """
        Load all templates from a directory.
        
        Args:
            directory: Path to templates directory
            
        Returns:
            Number of templates loaded
        """
        templates_dir = Path(directory)
        if not templates_dir.exists():
            return 0
        
        count = 0
        for file_path in templates_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    template_data = json.load(f)
                    await self.create_template_from_dict(template_data)
                    count += 1
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")
        
        return count


def get_template_service(db: AsyncSession) -> TemplateService:
    """Factory function to create TemplateService instance."""
    return TemplateService(db)