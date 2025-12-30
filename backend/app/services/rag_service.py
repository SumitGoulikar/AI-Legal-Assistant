# backend/app/services/rag_service.py
"""
RAG (Retrieval Augmented Generation) Service
=============================================
Combines vector search with LLM generation for intelligent Q&A.

Flow:
1. User asks a question
2. Retrieve relevant context from vector store
3. Build prompt with context
4. Generate response using LLM
5. Return response with sources
"""

from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.vector_store_service import get_vector_store_service
from app.services.llm_service import get_llm_service
from app.services.document_service import DocumentService
from app.utils.prompts import (
    build_rag_prompt,
    build_document_query_prompt,
    add_disclaimer,
    format_sources,
)
from app.config import settings
from app.core.exceptions import ValidationError


class RAGService:
    """
    RAG service for intelligent question answering.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize RAG service.
        
        Args:
            db: Database session
        """
        self.db = db
        self.vector_store = get_vector_store_service()
        self.llm_service = get_llm_service()
    
    # ============================================
    # GENERAL LEGAL Q&A
    # ============================================
    
    async def query_legal_knowledge(
        self,
        query: str,
        user_id: str,
        n_results: int = 5,
        conversation_history: Optional[List[Dict]] = None,
        include_user_docs: bool = False
    ) -> Dict[str, Any]:
        """
        Answer a general legal question using RAG.
        
        Args:
            query: User's question
            user_id: User's ID
            n_results: Number of context chunks to retrieve
            conversation_history: Previous messages for context
            include_user_docs: Whether to search user's documents too
            
        Returns:
            Dict with answer, sources, and metadata
        """
        # Retrieve relevant context
        if include_user_docs:
            context_chunks = self.vector_store.search_all(
                query=query,
                user_id=user_id,
                n_results=n_results,
                include_knowledge_base=True,
                include_user_docs=True
            )
        else:
            context_chunks = self.vector_store.search_legal_knowledge(
                query=query,
                n_results=n_results
            )
        
        # Build prompt
        messages = build_rag_prompt(
            user_query=query,
            context_chunks=context_chunks,
            conversation_history=conversation_history
        )
        
        # Generate response
        llm_response = await self.llm_service.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Add disclaimer
        answer = add_disclaimer(llm_response["response"])
        
        # Format sources
        sources = format_sources(context_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "context_chunks_used": len(context_chunks),
            "tokens_used": llm_response.get("tokens_used", 0),
            "model_used": llm_response.get("model", "unknown"),
            "generation_time_ms": llm_response.get("generation_time_ms", 0),
        }
    
    # ============================================
    # DOCUMENT Q&A
    # ============================================
    
    async def query_document(
        self,
        query: str,
        document_id: str,
        user_id: str,
        n_results: int = 5
    ) -> Dict[str, Any]:
        """
        Answer a question about a specific document.
        
        Args:
            query: User's question
            document_id: Document to query
            user_id: User's ID
            n_results: Number of chunks to retrieve
            
        Returns:
            Dict with answer, sources, and metadata
        """
        # Get document info
        doc_service = DocumentService(self.db)
        document = await doc_service.get_document_by_id(document_id, user_id)
        
        if not document:
            raise ValidationError("Document not found")
        
        if document.status != "ready":
            raise ValidationError(f"Document is not ready (status: {document.status})")
        
        # Retrieve relevant chunks from the document
        context_chunks = self.vector_store.search_user_documents(
            query=query,
            user_id=user_id,
            document_id=document_id,
            n_results=n_results
        )
        
        if not context_chunks:
            return {
                "answer": add_disclaimer(
                    "I couldn't find relevant information in this document to answer your question. "
                    "Please try rephrasing your question or ask about a different topic covered in the document."
                ),
                "sources": [],
                "context_chunks_used": 0,
                "tokens_used": 0,
            }
        
        # Build prompt
        messages = build_document_query_prompt(
            user_query=query,
            document_chunks=context_chunks,
            document_name=document.original_name
        )
        
        # Generate response
        llm_response = await self.llm_service.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=1000
        )
        
        # Add disclaimer
        answer = add_disclaimer(llm_response["response"])
        
        # Format sources
        sources = format_sources(context_chunks)
        
        return {
            "answer": answer,
            "sources": sources,
            "document_id": document_id,
            "document_name": document.original_name,
            "context_chunks_used": len(context_chunks),
            "tokens_used": llm_response.get("tokens_used", 0),
            "model_used": llm_response.get("model", "unknown"),
            "generation_time_ms": llm_response.get("generation_time_ms", 0),
        }
    
    # ============================================
    # DOCUMENT ANALYSIS
    # ============================================
    
    async def analyze_document(
        self,
        document_id: str,
        user_id: str,
        analysis_type: str,
        custom_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform AI analysis on a document.
        
        Args:
            document_id: Document to analyze
            user_id: User's ID
            analysis_type: Type of analysis (summary, risks, key_clauses)
            custom_query: Optional custom analysis query
            
        Returns:
            Analysis results
        """
        from app.utils.prompts import (
            DOCUMENT_SUMMARY_PROMPT,
            RISK_ANALYSIS_PROMPT,
            KEY_CLAUSES_PROMPT,
        )
        
        # Get document
        doc_service = DocumentService(self.db)
        document = await doc_service.get_document_by_id(document_id, user_id)
        
        if not document:
            raise ValidationError("Document not found")
        
        if document.status != "ready":
            raise ValidationError(f"Document is not ready (status: {document.status})")
        
        # Determine analysis query
        if custom_query:
            query = custom_query
        elif analysis_type == "summary":
            query = DOCUMENT_SUMMARY_PROMPT
        elif analysis_type == "risks":
            query = RISK_ANALYSIS_PROMPT
        elif analysis_type == "key_clauses":
            query = KEY_CLAUSES_PROMPT
        else:
            raise ValidationError(f"Unknown analysis type: {analysis_type}")
        
        # Get document chunks (more for analysis)
        context_chunks = self.vector_store.search_user_documents(
            query=query,
            user_id=user_id,
            document_id=document_id,
            n_results=10  # More chunks for comprehensive analysis
        )
        
        # Build prompt
        messages = build_document_query_prompt(
            user_query=query,
            document_chunks=context_chunks,
            document_name=document.original_name
        )
        
        # Generate analysis
        llm_response = await self.llm_service.generate_response(
            messages=messages,
            temperature=0.3,
            max_tokens=1500  # More tokens for detailed analysis
        )
        
        # Add disclaimer
        analysis = add_disclaimer(llm_response["response"])
        
        return {
            "analysis": analysis,
            "analysis_type": analysis_type,
            "document_id": document_id,
            "document_name": document.original_name,
            "tokens_used": llm_response.get("tokens_used", 0),
            "model_used": llm_response.get("model", "unknown"),
        }


def get_rag_service(db: AsyncSession) -> RAGService:
    """Factory function to create RAGService instance."""
    return RAGService(db)