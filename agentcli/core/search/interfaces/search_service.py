"""Module defining interfaces for search services."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class SearchService(ABC):
    """Interface for search service implementations."""
    
    @abstractmethod
    def search(self, query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Search for content matching the query.
        
        Args:
            query: Search query text.
            top_k: Number of top results to return.
            **kwargs: Additional search parameters.
            
        Returns:
            Dictionary containing search results and metadata.
        """
        pass
    
    @abstractmethod
    def index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a file for searching.
        
        Args:
            file_path: Path to the file to index.
            
        Returns:
            Dictionary containing indexing results.
        """
        pass
    
    @abstractmethod
    def index_directory(self, directory: str, patterns: List[str] = None) -> Dict[str, Any]:
        """Index a directory for searching.
        
        Args:
            directory: Path to the directory to index.
            patterns: File patterns to include.
            
        Returns:
            Dictionary containing indexing results.
        """
        pass
    
    @abstractmethod
    def rebuild_index(self) -> Dict[str, Any]:
        """Rebuild the search index.
        
        Returns:
            Dictionary containing rebuild results.
        """
        pass
