"""Module defining interfaces for code chunking."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class CodeChunker(ABC):
    """Interface for code chunking implementations."""
    
    @abstractmethod
    def chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Split a file into logical chunks.
        
        Args:
            file_path: Path to the file to chunk.
            
        Returns:
            List of dictionaries containing chunks and their metadata.
            Each chunk should have at least 'content' and 'metadata' keys.
        """
        pass
    
    @abstractmethod
    def chunk_content(self, content: str, file_path: str = None) -> List[Dict[str, Any]]:
        """Split content into logical chunks.
        
        Args:
            content: Content to chunk.
            file_path: Optional path for context.
            
        Returns:
            List of dictionaries containing chunks and their metadata.
        """
        pass
    
    def parse_content(self, content: str) -> List[Dict[str, Any]]:
        """Parse content and extract code structures.
        
        Args:
            content: Content to parse.
            
        Returns:
            List of dictionaries containing parsed structures.
        """
        ...
