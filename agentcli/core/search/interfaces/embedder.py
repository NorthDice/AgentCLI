"""Module defining interfaces for embedders."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Embedder(ABC):
    """Interface for embedding implementations."""
    
    @abstractmethod
    def get_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create embeddings for chunks.
        
        Args:
            chunks: List of dictionaries containing chunks and their metadata.
            
        Returns:
            List of dictionaries containing chunks, their metadata and embeddings.
            Each item should have 'content', 'metadata', and 'embedding' keys.
        """
        pass
    
    @abstractmethod
    def get_query_embedding(self, query: str) -> List[float]:
        """Create embedding for a search query.
        
        Args:
            query: Search query text.
            
        Returns:
            Embedding vector as a list of floats.
        """
        pass
