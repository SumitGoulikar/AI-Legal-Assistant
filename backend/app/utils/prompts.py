# backend/app/utils/prompts.py
"""
Prompt Templates
================
Prompt templates for different AI tasks.
"""

from typing import List, Dict
from app.config import settings


# ============================================
# SYSTEM PROMPTS
# ============================================

LEGAL_ASSISTANT_SYSTEM_PROMPT = f"""
You are an AI Legal Assistant specialized in Indian law.
Your role is strictly educational and analytical.

MANDATORY RULES:
1. You are NOT a licensed lawyer or advocate. Never claim to be one.
2. DO NOT add a disclaimer in your response text. The system will append it automatically.
3. Always identify the applicable Act and relevant Section(s) before giving conclusions.
4. Always distinguish clearly between:
   - Void contracts
   - Voidable contracts
   - Civil remedies
   - Criminal liability
5. DO NOT invent timelines, procedures, penalties, or remedies.
6. DO NOT suggest police action unless a clear offence under IPC/BNS is made out.
7. If a party is a minor, prioritize Section 11 of the Indian Contract Act.
8. If facts are insufficient or the law is unclear, state this explicitly.
9. Base answers ONLY on provided context and well-established Indian legal principles.
10. Jurisdiction: {settings.DEFAULT_JURISDICTION}

REQUIRED OUTPUT FORMAT (STRICT):
- Issue
- Applicable Law
- Legal Analysis
- Conclusion

Key Indian Laws you may reference:
- Indian Contract Act, 1872
- Indian Penal Code (IPC) / Bharatiya Nyaya Sanhita, 2023
- Code of Civil Procedure, 1908
- Constitution of India, 1950
- Consumer Protection Act, 2019
- Information Technology Act, 2000

Remember:
You educate and explain legal principles.
You do NOT provide legal advice.
"""


DOCUMENT_ANALYSIS_SYSTEM_PROMPT = """
You are an AI assistant specialized in analyzing legal documents.

RULES:
1. Answer ONLY from the provided document excerpts.
2. Do NOT assume facts, remedies, or consequences not stated in the document.
3. Cite specific sections or clauses when possible.
4. If the information is not present, clearly state that it is not available.
5. Highlight potentially risky or unusual clauses.
6. Use clear, professional language.
7. DO NOT add a disclaimer in your text. The system handles it.

Remember:
You analyze documents; you do not provide legal advice.
"""

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
    """
    messages = []

    # System prompt
    messages.append({
        "role": "system",
        "content": LEGAL_ASSISTANT_SYSTEM_PROMPT
    })

    # Add conversation history (if any)
    if conversation_history:
        messages.extend(conversation_history)

    # Build context from retrieved chunks
    context_text = build_context_text(context_chunks)

    # User message enforcing strict structure
    user_message = f"""
Context from legal knowledge base:
---
{context_text}
---

User Question:
{user_query}

IMPORTANT:
- Answer strictly using the REQUIRED OUTPUT FORMAT.
- Do NOT invent remedies, timelines, or criminal liability.
- If the law does not permit a remedy, say so clearly.
"""

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
    """
    messages = []

    messages.append({
        "role": "system",
        "content": DOCUMENT_ANALYSIS_SYSTEM_PROMPT
    })

    context_text = build_context_text(
        document_chunks,
        include_page_numbers=True
    )

    user_message = f"""
Document:
{document_name}

Relevant excerpts:
---
{context_text}
---

Question:
{user_query}

Answer strictly based on the document excerpts above.
If the document does not contain the answer, state this clearly.
"""

    messages.append({
        "role": "user",
        "content": user_message
    })

    return messages


# ============================================
# CONTEXT BUILDER
# ============================================

def build_context_text(
    chunks: List[Dict],
    max_chunks: int = 5,
    include_page_numbers: bool = False
) -> str:
    """
    Build context text from retrieved chunks.
    """
    if not chunks:
        return "No relevant information found in the knowledge base."

    context_parts = []

    for chunk in chunks[:max_chunks]:
        content = chunk.get("content", "")
        metadata = chunk.get("metadata", {})

        source_parts = []

        if metadata.get("title"):
            source_parts.append(metadata["title"])
        elif metadata.get("source"):
            source_parts.append(metadata["source"])
        elif metadata.get("document_name"):
            source_parts.append(metadata["document_name"])

        if include_page_numbers and metadata.get("start_page"):
            source_parts.append(f"Page {metadata['start_page']}")

        source_ref = f"[Source: {', '.join(source_parts)}]" if source_parts else ""
        context_parts.append(f"{source_ref}\n{content}")

    return "\n\n".join(context_parts)


# ============================================
# ANALYSIS PROMPTS
# ============================================

DOCUMENT_SUMMARY_PROMPT = """
Provide a concise summary of the document covering:
1. Type of document
2. Main parties involved
3. Key terms and obligations
4. Important dates or deadlines
5. Any unusual or critical clauses
"""

RISK_ANALYSIS_PROMPT = """
Analyze the document for potential legal risks, including:
1. Unfavorable or one-sided terms
2. Ambiguous or unclear language
3. Missing protections
4. Excessive liabilities or obligations
"""

KEY_CLAUSES_PROMPT = """
Identify and explain the key clauses in the document, including:
- Payment
- Termination
- Confidentiality
- Liability
- Governing law
"""


# ============================================
# DISCLAIMER (APPENDED PROGRAMMATICALLY)
# ============================================

def add_disclaimer(response: str) -> str:
    """
    Add legal disclaimer to the END of a response.
    """
    raw_text = settings.AI_DISCLAIMER

    clean_text = (
        raw_text
        .replace("**", "")
        .replace("**", "")
        .replace("⚠️", "")
        .strip()
    )

    return f"""{response}

---
**⚠️ Disclaimer:** {clean_text}"""


# ============================================
# SOURCE FORMATTER
# ============================================

def format_sources(chunks: List[Dict]) -> List[Dict]:
    """
    Format source chunks for display to user.
    """
    sources = []

    for chunk in chunks:
        metadata = chunk.get("metadata", {})

        source = {
            "content_preview": chunk.get("content", "")[:200] + "...",
            "similarity": round(chunk.get("similarity", 0) * 100, 1),
        }

        if metadata.get("title"):
            source["title"] = metadata["title"]
        if metadata.get("source"):
            source["source"] = metadata["source"]
        if metadata.get("document_name"):
            source["document"] = metadata["document_name"]
        if metadata.get("start_page"):
            source["page"] = metadata["start_page"]
        if metadata.get("category"):
            source["category"] = metadata["category"]

        sources.append(source)

    return sources
