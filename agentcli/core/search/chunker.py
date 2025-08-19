"""Module for splitting code into logical chunks with overlap."""

import os
import logging
from typing import Dict, List, Any, Optional

from agentcli.core.search.interfaces import CodeChunker

logger = logging.getLogger(__name__)


class TreeSitterChunker(CodeChunker):
    """Code chunker implementation with overlap support."""
    
    def __init__(self, chunk_size: int = 90, overlap: int = 20):
        """Initialize the chunker.
        
        Args:
            chunk_size: Default number of lines per chunk.
            overlap: Number of lines to overlap between chunks.
        """
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size - 1)  # Ensure overlap is less than chunk_size
        
    def chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Split a file into logical chunks.
        
        Args:
            file_path: Path to the file to chunk.
            
        Returns:
            List of dictionaries containing chunks and their metadata.
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return []
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.chunk_content(content, file_path)
        except Exception as e:
            logger.error(f"Error chunking file {file_path}: {str(e)}")
            return []
    
    def chunk_content(self, content: str, file_path: str = None) -> List[Dict[str, Any]]:
        """Split content into logical chunks with overlap.
        
        Args:
            content: Content to chunk.
            file_path: Optional path for context.
            
        Returns:
            List of dictionaries containing chunks and their metadata.
        """
        if not content.strip():
            return []
        
        # Use line-based chunking with overlap
        return self._chunk_by_lines(content, file_path, self.chunk_size, self.overlap)
    
    def _chunk_by_lines(self, content: str, file_path: str = None, chunk_size: int = 50, overlap: int = 10) -> List[Dict[str, Any]]:
        """Split text content into chunks of fixed size with optional overlap.
        
        Args:
            content: Content to chunk.
            file_path: Optional file path for metadata.
            chunk_size: Number of lines per chunk.
            overlap: Number of lines to overlap between chunks.
            
        Returns:
            List of dictionaries containing chunks and their metadata.
        """
        chunks = []
        lines = content.split("\n")
        
        # Simple fixed size chunking with overlap
        step = chunk_size - overlap if overlap < chunk_size else 1
        for i in range(0, len(lines), step):
            end_idx = min(i + chunk_size, len(lines))
            chunk_lines = lines[i:end_idx]
            chunk_content = "\n".join(chunk_lines)
            
            if not chunk_content.strip():
                continue
                
            chunks.append({
                "content": chunk_content,
                "metadata": {
                    "file_path": file_path or "unknown",
                    "start_line": i + 1,
                    "end_line": end_idx,
                    "type": "text_chunk",
                    "name": f"chunk_{len(chunks) + 1}"
                }
            })
        
        return chunks
