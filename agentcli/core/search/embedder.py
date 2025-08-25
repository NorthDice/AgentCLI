"""Module for creating embeddings from code chunks."""

import logging
from typing import List, Dict, Any, Optional

# Import ML libraries with error handling
try:
    from sentence_transformers import SentenceTransformer
    import torch
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

from agentcli.core.search.interfaces import Embedder

logger = logging.getLogger(__name__)

class SentenceTransformerEmbedder(Embedder):
    """Embedder implementation using sentence-transformers."""
    
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """Initialize the embedder with a model.
        
        Args:
            model_name: Name of the sentence-transformer model to use.
        """
        self.model_name = model_name
        self.model = None
        
    def _load_model(self):
        """Load the sentence-transformer model."""
        if not EMBEDDINGS_AVAILABLE:
            logger.error("sentence-transformers package not installed.")
            raise ImportError("Please install sentence-transformers: pip install sentence-transformers")
            
        if self.model is None:
            try:
                # Check for GPU availability
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading model {self.model_name} on {device}")
                
                self.model = SentenceTransformer(self.model_name, device=device)
            except Exception as e:
                logger.error(f"Error loading model {self.model_name}: {str(e)}")
                raise
    
    def get_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for chunks.
        
        Args:
            chunks: List of dictionaries containing chunks and their metadata.
            
        Returns:
            List of dictionaries containing chunks, their metadata and embeddings.
        """
        if not chunks:
            return []
            
        self._load_model()
        
        # Extract content for batch processing
        texts = [chunk["content"] for chunk in chunks]
        
        try:
            # Generate embeddings
            embeddings = self.model.encode(texts, show_progress_bar=len(texts) > 10)
            
            # Combine results
            result = []
            for i, chunk in enumerate(chunks):
                result.append({
                    "content": chunk["content"],
                    "metadata": chunk["metadata"],
                    "embedding": embeddings[i].tolist()  # Convert numpy array to list
                })
            
            return result
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Return chunks without embeddings in case of error
            return [{"content": chunk["content"], "metadata": chunk["metadata"], "embedding": []} for chunk in chunks]
    
    def get_query_embedding(self, query: str) -> List[float]:
        """Create embedding for a search query.
        
        Args:
            query: Search query text.
            
        Returns:
            Embedding vector as a list of floats.
        """
        if not query.strip():
            return []
            
        self._load_model()
        
        try:
            embedding = self.model.encode(query)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return []
