# backend/app/services/vector_store_service.py
"""
Vector Store Service
====================
Manages ChromaDB vector database for storing and searching embeddings.

ChromaDB Collections:
1. legal_knowledge - Shared legal knowledge base (admin uploaded)
2. user_documents - User-specific document embeddings

Features:
- Add documents with embeddings and metadata
- Semantic similarity search
- Filter by user_id, document_id, etc.
- Persistent storage
"""

from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path

from app.config import settings
from app.services.embedding_service import get_embedding_service


class VectorStoreService:
    """
    Service for managing vector storage with ChromaDB.
    
    Provides methods for:
    - Adding embeddings
    - Searching by similarity
    - Managing collections
    - Filtering results
    """
    
    _instance = None
    _client = None
    
    # Collection names
    LEGAL_KNOWLEDGE_COLLECTION = "legal_knowledge"
    USER_DOCUMENTS_COLLECTION = "user_documents"
    
    def __new__(cls):
        """Singleton pattern for ChromaDB client."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the vector store service."""
        self.embedding_service = get_embedding_service()
        self.persist_directory = settings.CHROMA_PERSIST_DIR
    
    def _get_client(self) -> chromadb.Client:
        """
        Get or create the ChromaDB client.
        
        Uses persistent storage so data survives restarts.
        """
        if VectorStoreService._client is None:
            print(f"📦 Initializing ChromaDB at: {self.persist_directory}")
            
            # Ensure directory exists
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Create persistent client
            VectorStoreService._client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            
            print("✅ ChromaDB initialized!")
        
        return VectorStoreService._client
    
    @property
    def client(self) -> chromadb.Client:
        """Get the ChromaDB client."""
        return self._get_client()
    
    # ============================================
    # COLLECTION MANAGEMENT
    # ============================================
    
    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict] = None
    ) -> chromadb.Collection:
        """
        Get or create a ChromaDB collection.
        
        Args:
            name: Collection name
            metadata: Optional metadata for the collection
            
        Returns:
            ChromaDB Collection object
        """
        return self.client.get_or_create_collection(
            name=name,
            metadata=metadata or {"description": f"Collection: {name}"},
        )
    
    def get_legal_knowledge_collection(self) -> chromadb.Collection:
        """Get the legal knowledge base collection."""
        return self.get_or_create_collection(
            name=self.LEGAL_KNOWLEDGE_COLLECTION,
            metadata={
                "description": "Shared legal knowledge base for RAG",
                "type": "knowledge_base",
            }
        )
    
    def get_user_documents_collection(self) -> chromadb.Collection:
        """Get the user documents collection."""
        return self.get_or_create_collection(
            name=self.USER_DOCUMENTS_COLLECTION,
            metadata={
                "description": "User-uploaded document embeddings",
                "type": "user_documents",
            }
        )
    
    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            self.client.delete_collection(name)
            return True
        except Exception as e:
            print(f"Error deleting collection {name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """List all collections."""
        collections = self.client.list_collections()
        return [c.name for c in collections]
    
    # ============================================
    # ADD DOCUMENTS
    # ============================================
    
    def add_document_chunks(
        self,
        chunks: List[Dict[str, Any]],
        user_id: str,
        document_id: str,
        document_name: str
    ) -> List[str]:
        """
        Add document chunks to the user documents collection.
        
        Args:
            chunks: List of chunk dictionaries with 'content', 'chunk_index', etc.
            user_id: User's ID
            document_id: Document's ID
            document_name: Original document name
            
        Returns:
            List of generated chunk IDs in ChromaDB
        """
        if not chunks:
            return []
        
        collection = self.get_user_documents_collection()
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            # Generate unique ID for each chunk
            chunk_id = f"{document_id}_{chunk['chunk_index']}"
            ids.append(chunk_id)
            
            # Document text
            documents.append(chunk['content'])
            
            # Metadata for filtering
            metadatas.append({
                "user_id": user_id,
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": chunk['chunk_index'],
                "start_page": chunk.get('start_page', 1),
                "end_page": chunk.get('end_page', 1),
            })
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(documents)
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        print(f"✅ Added {len(chunks)} chunks for document {document_id}")
        
        return ids
    
    def add_knowledge_base_chunks(
        self,
        chunks: List[Dict[str, Any]],
        knowledge_base_id: str,
        title: str,
        source: str,
        category: str
    ) -> List[str]:
        """
        Add knowledge base chunks to the legal knowledge collection.
        
        Args:
            chunks: List of chunk dictionaries
            knowledge_base_id: Knowledge base entry ID
            title: Document title
            source: Source of the document
            category: Category (acts, rules, etc.)
            
        Returns:
            List of generated chunk IDs
        """
        if not chunks:
            return []
        
        collection = self.get_legal_knowledge_collection()
        
        ids = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            chunk_id = f"kb_{knowledge_base_id}_{chunk['chunk_index']}"
            ids.append(chunk_id)
            
            documents.append(chunk['content'])
            
            metadatas.append({
                "knowledge_base_id": knowledge_base_id,
                "title": title,
                "source": source,
                "category": category,
                "chunk_index": chunk['chunk_index'],
                "start_page": chunk.get('start_page', 1),
            })
        
        # Generate embeddings
        embeddings = self.embedding_service.embed_texts(documents)
        
        # Add to collection
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        
        print(f"✅ Added {len(chunks)} chunks to knowledge base: {title}")
        
        return ids
    
    # ============================================
    # SEARCH
    # ============================================
    
    def search_user_documents(
        self,
        query: str,
        user_id: str,
        document_id: Optional[str] = None,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search user's documents by semantic similarity.
        
        Args:
            query: Search query text
            user_id: User's ID (required for filtering)
            document_id: Optional specific document to search
            n_results: Number of results to return
            
        Returns:
            List of matching chunks with scores and metadata
        """
        collection = self.get_user_documents_collection()
        
        # Check if collection has documents
        if collection.count() == 0:
            return []
        
        # Build filter
        where_filter = {"user_id": user_id}
        if document_id:
            where_filter = {
                "$and": [
                    {"user_id": user_id},
                    {"document_id": document_id}
                ]
            }
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        try:
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            return self._format_search_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_legal_knowledge(
        self,
        query: str,
        n_results: int = 5,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the legal knowledge base by semantic similarity.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            category: Optional category filter
            
        Returns:
            List of matching chunks with scores and metadata
        """
        collection = self.get_legal_knowledge_collection()
        
        # Check if collection has documents
        if collection.count() == 0:
            return []
        
        # Build filter
        where_filter = None
        if category:
            where_filter = {"category": category}
        
        # Generate query embedding
        query_embedding = self.embedding_service.embed_text(query)
        
        try:
            # Search
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            return self._format_search_results(results)
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def search_all(
        self,
        query: str,
        user_id: str,
        n_results: int = 5,
        include_knowledge_base: bool = True,
        include_user_docs: bool = True,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search across both knowledge base and user documents.
        
        Args:
            query: Search query text
            user_id: User's ID
            n_results: Total number of results to return
            include_knowledge_base: Whether to search knowledge base
            include_user_docs: Whether to search user documents
            document_id: Optional specific document to search
            
        Returns:
            Combined and ranked search results
        """
        all_results = []
        
        # Search knowledge base
        if include_knowledge_base:
            kb_results = self.search_legal_knowledge(query, n_results=n_results)
            for r in kb_results:
                r['source_type'] = 'knowledge_base'
            all_results.extend(kb_results)
        
        # Search user documents
        if include_user_docs:
            doc_results = self.search_user_documents(
                query, user_id, document_id, n_results=n_results
            )
            for r in doc_results:
                r['source_type'] = 'user_document'
            all_results.extend(doc_results)
        
        # Sort by distance (lower is better) and take top n_results
        all_results.sort(key=lambda x: x.get('distance', 1.0))
        
        return all_results[:n_results]
    
    def _format_search_results(self, results: Dict) -> List[Dict[str, Any]]:
        """
        Format ChromaDB results into a cleaner structure.
        
        Args:
            results: Raw ChromaDB query results
            
        Returns:
            List of formatted result dictionaries
        """
        formatted = []
        
        if not results or not results.get('ids') or not results['ids'][0]:
            return formatted
        
        ids = results['ids'][0]
        documents = results.get('documents', [[]])[0]
        metadatas = results.get('metadatas', [[]])[0]
        distances = results.get('distances', [[]])[0]
        
        for i in range(len(ids)):
            formatted.append({
                'id': ids[i],
                'content': documents[i] if i < len(documents) else "",
                'metadata': metadatas[i] if i < len(metadatas) else {},
                'distance': distances[i] if i < len(distances) else 1.0,
                'similarity': 1 - distances[i] if i < len(distances) else 0.0,
            })
        
        return formatted
    
    # ============================================
    # DELETE
    # ============================================
    
    def delete_document_chunks(
        self,
        document_id: str,
        user_id: str
    ) -> bool:
        """
        Delete all chunks for a specific document.
        
        Args:
            document_id: Document's ID
            user_id: User's ID (for verification)
            
        Returns:
            True if successful
        """
        try:
            collection = self.get_user_documents_collection()
            
            # Get IDs to delete
            results = collection.get(
                where={
                    "$and": [
                        {"document_id": document_id},
                        {"user_id": user_id}
                    ]
                },
                include=[]
            )
            
            if results and results.get('ids'):
                collection.delete(ids=results['ids'])
                print(f"✅ Deleted {len(results['ids'])} chunks for document {document_id}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting chunks: {e}")
            return False
    
    def delete_knowledge_base_chunks(self, knowledge_base_id: str) -> bool:
        """
        Delete all chunks for a knowledge base entry.
        
        Args:
            knowledge_base_id: Knowledge base entry ID
            
        Returns:
            True if successful
        """
        try:
            collection = self.get_legal_knowledge_collection()
            
            # Get IDs to delete
            results = collection.get(
                where={"knowledge_base_id": knowledge_base_id},
                include=[]
            )
            
            if results and results.get('ids'):
                collection.delete(ids=results['ids'])
                print(f"✅ Deleted chunks for knowledge base {knowledge_base_id}")
            
            return True
            
        except Exception as e:
            print(f"Error deleting knowledge base chunks: {e}")
            return False
    
    # ============================================
    # STATISTICS
    # ============================================
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Get statistics for a collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = self.client.get_or_create_collection(collection_name)
            count = collection.count()
            
            return {
                "name": collection_name,
                "count": count,
                "metadata": collection.metadata or {},
            }
        except Exception as e:
            return {
                "name": collection_name,
                "count": 0,
                "error": str(e),
            }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all collections."""
        return {
            "legal_knowledge": self.get_collection_stats(self.LEGAL_KNOWLEDGE_COLLECTION),
            "user_documents": self.get_collection_stats(self.USER_DOCUMENTS_COLLECTION),
            "embedding_model": self.embedding_service.get_model_info(),
        }
    
    def get_user_document_count(self, user_id: str) -> int:
        """Get count of embeddings for a specific user."""
        try:
            collection = self.get_user_documents_collection()
            
            if collection.count() == 0:
                return 0
            
            results = collection.get(
                where={"user_id": user_id},
                include=[]
            )
            return len(results.get('ids', []))
        except Exception as e:
            print(f"Error getting user document count: {e}")
            return 0


# ============================================
# SINGLETON INSTANCE
# ============================================
vector_store_service = VectorStoreService()


def get_vector_store_service() -> VectorStoreService:
    """Get the vector store service instance."""
    return vector_store_service