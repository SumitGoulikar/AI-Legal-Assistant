# backend/app/services/embedding_service.py
"""
Embedding Service
=================
Handles text embedding using sentence-transformers.

This service:
- Loads and manages the embedding model
- Converts text to vector embeddings
- Provides batch embedding for efficiency

Model: all-MiniLM-L6-v2
- Dimensions: 384
- Speed: ~14,000 sentences/sec on GPU, ~1,400 on CPU
- Quality: Good balance of speed and accuracy
- Size: ~90MB
"""

from typing import List, Optional
import numpy as np

from app.config import settings


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Uses sentence-transformers for high-quality semantic embeddings.
    The model is loaded lazily on first use and cached.
    """
    
    _instance = None
    _model = None
    
    def __new__(cls):
        """Singleton pattern to reuse model instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the embedding service."""
        self.model_name = settings.EMBEDDING_MODEL
        self.dimension = 384  # Dimension for all-MiniLM-L6-v2
        self._is_loaded = False
    
    def _load_model(self):
        """
        Lazily load the embedding model.
        
        The model is loaded only when first needed to reduce startup time.
        """
        if EmbeddingService._model is None:
            print(f"📦 Loading embedding model: {self.model_name}...")
            
            try:
                from sentence_transformers import SentenceTransformer
                
                # Load the model
                EmbeddingService._model = SentenceTransformer(self.model_name)
                
                # Get actual dimension from model
                self.dimension = EmbeddingService._model.get_sentence_embedding_dimension()
                self._is_loaded = True
                
                print(f"✅ Embedding model loaded! Dimension: {self.dimension}")
                
            except Exception as e:
                print(f"❌ Failed to load embedding model: {e}")
                raise
        
        return EmbeddingService._model
    
    @property
    def model(self):
        """Get the loaded model."""
        return self._load_model()
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimension
        
        # Generate embedding
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True  # L2 normalize for cosine similarity
        )
        
        return embedding.tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch processing).
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Filter and track empty texts
        non_empty_texts = []
        empty_indices = []
        
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_texts.append(text)
            else:
                empty_indices.append(i)
        
        # Generate embeddings for non-empty texts
        if non_empty_texts:
            embeddings = self.model.encode(
                non_empty_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,  # Process in batches
                show_progress_bar=len(non_empty_texts) > 100
            )
            embeddings_list = embeddings.tolist()
        else:
            embeddings_list = []
        
        # Reconstruct full list with zero vectors for empty texts
        result = []
        non_empty_idx = 0
        
        for i in range(len(texts)):
            if i in empty_indices:
                result.append([0.0] * self.dimension)
            else:
                result.append(embeddings_list[non_empty_idx])
                non_empty_idx += 1
        
        return result
    
    def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float]
    ) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Cosine similarity (vectors are already normalized)
        similarity = np.dot(vec1, vec2)
        
        return float(similarity)
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model."""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "loaded": EmbeddingService._model is not None,
        }


# ============================================
# SINGLETON INSTANCE
# ============================================
# Use this instance throughout the application
embedding_service = EmbeddingService()


def get_embedding_service() -> EmbeddingService:
    """Get the embedding service instance."""
    return embedding_service