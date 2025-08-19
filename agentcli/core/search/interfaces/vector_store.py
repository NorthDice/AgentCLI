"""Module defining interfaces for vector stores."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class VectorStore(ABC):
    """Interface for vector store implementations."""
    
    @abstractmethod
    def add(self, items: List[Dict[str, Any]]) -> None:
        """Add items to the vector store.
        
        Args:
            items: List of dictionaries containing content, metadata, and embeddings.
        """
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in the store.
        
        Args:
            query_embedding: Query embedding vector.
            top_k: Number of top results to return.
            
        Returns:
            List of dictionaries containing found items with relevance scores.
        """
        pass
    
    @abstractmethod
    def delete(self, item_ids: List[str]) -> None:
        """Delete items from the store.
        
        Args:
            item_ids: List of item IDs to delete.
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear the entire store."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get the number of items in the store.
        
        Returns:
            Number of items in the store.
        """
        pass
