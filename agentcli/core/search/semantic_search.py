"""Module providing semantic search functionality."""

import os
import logging
import glob
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

from agentcli.core.search.interfaces import SearchService, CodeChunker, Embedder, VectorStore

logger = logging.getLogger(__name__)

class SemanticSearchService(SearchService):
    """Service for semantic search in code repositories."""
    
    def __init__(self, chunker: CodeChunker, embedder: Embedder, vector_store: VectorStore):
        """Initialize the search service.
        
        Args:
            chunker: Implementation for code chunking.
            embedder: Implementation for creating embeddings.
            vector_store: Implementation for storing vectors.
        """
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
    
    def search(self, query: str, top_k: int = 5, **kwargs) -> Dict[str, Any]:
        """Search for content matching the query.
        
        Args:
            query: Search query text.
            top_k: Number of top results to return.
            **kwargs: Additional search parameters.
            
        Returns:
            Dictionary containing search results and metadata.
        """
        logger.info(f"Performing semantic search for: '{query}'")
        
        # Create query embedding
        query_embedding = self.embedder.get_query_embedding(query)
        
        # Search in vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)
        
        return {
            "query": query,
            "results": results,
            "total_results": len(results)
        }
    
    def index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a file for searching.
        
        Args:
            file_path: Path to the file to index.
            
        Returns:
            Dictionary containing indexing results.
        """
        logger.info(f"Indexing file: {file_path}")
        
        result = {
            "file_path": file_path,
            "chunks_created": 0,
            "success": False,
            "error": None
        }
        
        try:
            # Skip if file doesn't exist or is a directory
            if not os.path.isfile(file_path):
                result["error"] = f"Not a file or doesn't exist: {file_path}"
                return result
            
            # Skip if file should be ignored
            if self._should_ignore(file_path):
                result["error"] = f"File ignored: {file_path}"
                return result
                
            # Create chunks
            chunks = self.chunker.chunk_file(file_path)
            
            if not chunks:
                result["error"] = f"No chunks created from file: {file_path}"
                return result
                
            # Create embeddings
            chunks_with_embeddings = self.embedder.get_embeddings(chunks)
            
            # Add to vector store
            self.vector_store.add(chunks_with_embeddings)
            
            result["chunks_created"] = len(chunks)
            result["success"] = True
            
            return result
        except Exception as e:
            logger.error(f"Error indexing file {file_path}: {str(e)}")
            result["error"] = str(e)
            return result
    
    def index_directory(self, directory: str, patterns: List[str] = None) -> Dict[str, Any]:
        """Index a directory for searching.
        
        Args:
            directory: Path to the directory to index.
            patterns: File patterns to include.
            
        Returns:
            Dictionary containing indexing results.
        """
        if not patterns:
            patterns = ["*.py", "*.js", "*.html", "*.css", "*.md"]
        
        logger.info(f"Indexing directory: {directory} with patterns: {patterns}")
        
        stats = {
            "total_files": 0,
            "indexed_files": 0,
            "total_chunks": 0,
            "errors": []
        }
        
        # Find all files matching the patterns
        all_files = []
        for pattern in patterns:
            pattern_files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
            all_files.extend(pattern_files)
        
        stats["total_files"] = len(all_files)
        
        # Index each file
        for file_path in all_files:
            try:
                result = self.index_file(file_path)
                
                if result["success"]:
                    stats["indexed_files"] += 1
                    stats["total_chunks"] += result["chunks_created"]
                else:
                    stats["errors"].append({
                        "file": file_path,
                        "error": result["error"]
                    })
            except Exception as e:
                logger.error(f"Error indexing {file_path}: {str(e)}")
                stats["errors"].append({
                    "file": file_path,
                    "error": str(e)
                })
        
        return stats
    
    def rebuild_index(self) -> Dict[str, Any]:
        """Rebuild the search index.
        
        Returns:
            Dictionary containing rebuild results.
        """
        logger.info("Rebuilding search index")
        
        # Clear existing index
        self.vector_store.clear()
        
        # Index from current directory
        return self.index_directory(".")
        
    def _should_ignore(self, path: str) -> bool:
        """Check if a file should be ignored.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the file should be ignored, False otherwise.
        """
        # Ignore hidden files and directories (but not the current directory ".")
        parts = path.split(os.sep)
        for i, part in enumerate(parts):
            # Skip the first part if it's "." (current directory)
            if i == 0 and part == ".":
                continue
            if part.startswith("."):
                return True
        
        # Ignore virtual environments
        if ".venv" in parts or "venv" in parts:
            return True
            
        # Ignore cache and other temporary files
        ignore_patterns = ["__pycache__", ".git", ".pytest_cache", ".mypy_cache", 
                           ".tox", ".eggs", "*.pyc", "*.pyo", "*.pyd"]
                           
        for pattern in ignore_patterns:
            if pattern.startswith("*."):
                if Path(path).suffix == pattern[1:]:
                    return True
            elif pattern in parts:
                return True
        
        return False
