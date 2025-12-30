# backend/app/utils/prompts.py
"""
Prompt Templates
================
Prompt templates for different AI tasks.

Templates include:
- System prompts for legal assistant
- RAG prompts with context injection
- Document analysis prompts
- Safety and disclaimer prompts
"""

from typing import List, Dict
from app.config import settings


# ============================================
# SYSTEM PROMPTS
# ============================================

LEGAL_ASSISTANT_SYSTEM_PROMPT = f"""You are an AI legal assistant specializing in Indian law. Your role is to provide helpful, accurate, and educational information about legal concepts, statutes, and procedures in India.

IMPORTANT RULES:
1. You are NOT a licensed lawyer or advocate. Never claim to be one.
2. Always include a disclaimer that this is general information only.
3. Strongly recommend consulting a qualified advocate registered with the Bar Council of India for specific legal matters.
4. Base your answers ONLY on the provided context and well-established legal principles.
5. If you don't have enough information to answer, say so clearly.
6. Be clear, concise, and use simple language when possible.
7. When citing laws, mention the specific Act and section if available.
8. Acknowledge the jurisdiction (India) and mention if laws vary by state.
9. Never provide advice that could be construed as practicing law.
10. Focus on education and general information, not case-specific advice.

Jurisdiction: {settings.DEFAULT_JURISDICTION}

Key Indian Laws you may reference:
- Indian Contract Act, 1872
- Indian Penal Code (IPC) / Bharatiya Nyaya Sanhita, 2023
- Code of Civil Procedure, 1908
- Code of Criminal Procedure, 1973
- Constitution of India, 1950
- Consumer Protection Act, 2019
- Information Technology Act, 2000
- Companies Act, 2013
- Indian Evidence Act, 1872

Remember: Your purpose is to educate and inform, not to provide legal counsel."""


DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """You are an AI assistant specialized in analyzing legal documents. 

Your task is to:
1. Carefully read the provided document excerpts
2. Answer the user's question based ONLY on the document content
3. Cite specific sections or clauses when possible
4. If the information is not in the document, clearly state that
5. Highlight any potentially important or risky clauses
6. Use clear, professional language

Remember: You are analyzing a document, not providing legal advice. Always recommend professional legal review."""


# ============================================
# RAG PROMPT BUILDERS
# ============================================

def build_rag_prompt(
    user_query: str,
    context_chunks: List[Dict],
    conversation_history: List[Dict] = None
) -> List[Dict[str, str]]:
    """
    Build a RAG prompt with context from retrieved documents.
    
    Args:
        user_query: The user's question
        context_chunks: Retrieved document chunks with metadata
        conversation_history: Previous messages in the conversation
        
    Returns:
        List of message dicts for the LLM
    """
    messages = []
    
    # System prompt
    messages.append({
        "role": "system",
        "content": LEGAL_ASSISTANT_SYSTEM_PROMPT
    })
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Build context from chunks
    context_text = build_context_text(context_chunks)
    
    # User message with context
    user_message = f"""Context from legal knowledge base:
---
{context_text}
---

User Question: {user_query}

Please provide a helpful answer based on the context above. Include the disclaimer and cite sources where applicable."""
    
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages


def build_document_query_prompt(
    user_query: str,
    document_chunks: List[Dict],
    document_name: str
) -> List[Dict[str, str]]:
    """
    Build a prompt for querying a specific document.
    
    Args:
        user_query: The user's question
        document_chunks: Relevant chunks from the document
        document_name: Name of the document being queried
        
    Returns:
        List of message dicts for the LLM
    """
    messages = []
    
    # System prompt
    messages.append({
        "role": "system",
        "content": DOCUMENT_ANALYSIS_SYSTEM_PROMPT
    })
    
    # Build context from document chunks
    context_text = build_context_text(document_chunks, include_page_numbers=True)
    
    # User message
    user_message = f"""Document: {document_name}

Relevant excerpts:
---
{context_text}
---

Question: {user_query}

Please answer based on the document excerpts above. If the information is not present in these excerpts, clearly state that."""
    
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    return messages


def build_context_text(
    chunks: List[Dict],
    max_chunks: int = 5,
    include_page_numbers: bool = False
) -> str:
    """
    Build context text from retrieved chunks.
    
    Args:
        chunks: List of chunk dicts with 'content' and 'metadata'
        max_chunks: Maximum number of chunks to include
        include_page_numbers: Whether to include page references
        
    Returns:
        Formatted context string
    """
    if not chunks:
        return "No relevant information found in the knowledge base."
    
    context_parts = []
    
    for i, chunk in enumerate(chunks[:max_chunks]):
        content = chunk.get('content', '')
        metadata = chunk.get('metadata', {})
        
        # Build source reference
        source_parts = []
        
        if metadata.get('title'):
            source_parts.append(metadata['title'])
        elif metadata.get('source'):
            source_parts.append(metadata['source'])
        elif metadata.get('document_name'):
            source_parts.append(metadata['document_name'])
        
        if include_page_numbers and metadata.get('start_page'):
            source_parts.append(f"Page {metadata['start_page']}")
        
        source_ref = f"[Source: {', '.join(source_parts)}]" if source_parts else ""
        
        # Add chunk to context
        context_parts.append(f"{source_ref}\n{content}")
    
    return "\n\n".join(context_parts)


# ============================================
# ANALYSIS PROMPTS
# ============================================

DOCUMENT_SUMMARY_PROMPT = """Please provide a concise summary of this document, highlighting:
1. Type of document (e.g., agreement, notice, contract)
2. Main parties involved
3. Key terms and conditions
4. Important dates or deadlines
5. Any notable clauses or obligations

Keep the summary clear and factual."""


RISK_ANALYSIS_PROMPT = """Please analyze this document for potential risks or concerns, such as:
1. Unfavorable terms or one-sided clauses
2. Unclear or ambiguous language
3. Missing important protections
4. Unusual or risky obligations
5. Potential compliance issues

For each risk identified, explain why it might be concerning."""


KEY_CLAUSES_PROMPT = """Please identify and explain the key clauses in this document, including:
1. Payment terms
2. Termination conditions
3. Confidentiality obligations
4. Liability and indemnification
5. Dispute resolution
6. Governing law and jurisdiction

Provide brief explanations of what each clause means."""


# ============================================
# DISCLAIMER
# ============================================

def add_disclaimer(response: str) -> str:
    """Add legal disclaimer to the beginning of a response."""
    return f"{settings.AI_DISCLAIMER}\n\n{response}"


def format_sources(chunks: List[Dict]) -> List[Dict]:
    """
    Format source chunks for display to user.
    
    Args:
        chunks: Retrieved chunks
        
    Returns:
        List of formatted source dicts
    """
    sources = []
    
    for chunk in chunks:
        metadata = chunk.get('metadata', {})
        
        source = {
            "content_preview": chunk.get('content', '')[:200] + "...",
            "similarity": round(chunk.get('similarity', 0) * 100, 1),
        }
        
        if metadata.get('title'):
            source["title"] = metadata['title']
        if metadata.get('source'):
            source["source"] = metadata['source']
        if metadata.get('document_name'):
            source["document"] = metadata['document_name']
        if metadata.get('start_page'):
            source["page"] = metadata['start_page']
        if metadata.get('category'):
            source["category"] = metadata['category']
        
        sources.append(source)
    
    return sources