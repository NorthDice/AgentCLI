"""Module providing semantic search functionality."""

import os
import logging
import glob
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager

from agentcli.core.search.interfaces import SearchService, CodeChunker, Embedder, VectorStore

# Import metrics collector at module level with fallback
try:
    from agentcli.core.performance.collector import metrics_collector
except ImportError:
    metrics_collector = None

logger = logging.getLogger(__name__)


@contextmanager
def performance_tracker(operation: str, **kwargs):
    """Context manager for tracking performance metrics.
    
    Args:
        operation: Name of the operation being tracked.
        **kwargs: Additional operation metadata.
        
    Yields:
        Context object for updating metrics during operation.
    """
    operation_context = None
    
    if metrics_collector:
        operation_context = metrics_collector.start_operation(operation, **kwargs)
        operation_context = operation_context.__enter__()
    
    try:
        yield operation_context
    finally:
        if operation_context and metrics_collector:
            operation_context.__exit__(None, None, None)


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
        with performance_tracker("semantic_search", query=query, top_k=top_k) as ctx:
            logger.info(f"Performing semantic search for: '{query}'")
            
            # Measure embedding time
            embed_start = time.time()
            query_embedding = self.embedder.get_query_embedding(query)
            embed_time = time.time() - embed_start
            
            # Measure search time
            search_start = time.time()
            results = self.vector_store.search(query_embedding, top_k=top_k)
            search_time = time.time() - search_start
            
            # Update context with metrics
            if ctx:
                ctx.kwargs.update({
                    'items_processed': len(results),
                    'embedding_time': embed_time,
                    'vector_search_time': search_time,
                    'results_found': len(results)
                })
            
            logger.info(f"Search completed: {len(results)} results in {embed_time + search_time:.3f}s")
            
            return {
                "query": query,
                "results": results,
                "total_results": len(results),
                "performance": {
                    "embedding_time": embed_time,
                    "search_time": search_time,
                    "total_time": embed_time + search_time
                }
            }
    
    def index_file(self, file_path: str) -> Dict[str, Any]:
        """Index a file for searching.
        
        Args:
            file_path: Path to the file to index.
            
        Returns:
            Dictionary containing indexing results.
        """
        with performance_tracker("index_file", file_path=file_path) as ctx:
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
                    
                # Measure chunking time
                chunk_start = time.time()
                chunks = self.chunker.chunk_file(file_path)
                chunk_time = time.time() - chunk_start
                
                if not chunks:
                    result["error"] = f"No chunks created from file: {file_path}"
                    return result
                    
                # Measure embedding time
                embed_start = time.time()
                chunks_with_embeddings = self.embedder.get_embeddings(chunks)
                embed_time = time.time() - embed_start
                
                # Measure vector store time
                store_start = time.time()
                self.vector_store.add(chunks_with_embeddings)
                store_time = time.time() - store_start
                
                result["chunks_created"] = len(chunks)
                result["success"] = True
                
                # Update metrics context
                if ctx:
                    ctx.kwargs.update({
                        'items_processed': len(chunks),
                        'chunks_created': len(chunks),
                        'chunking_time': chunk_time,
                        'embedding_time': embed_time,
                        'vector_store_time': store_time
                    })
                
                logger.info(f"Successfully indexed {file_path}: {len(chunks)} chunks in {chunk_time + embed_time + store_time:.3f}s")
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
        with performance_tracker("index_directory", directory=directory) as ctx:
            if not patterns:
                patterns = ["*.py", "*.js", "*.html", "*.css", "*.md"]
            
            logger.info(f"Indexing directory: {directory} with patterns: {patterns}")
            
            stats = {
                "directory": directory,
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
            
            # Update metrics context
            if ctx:
                ctx.kwargs.update({
                    'items_processed': stats["indexed_files"],
                    'files_processed': stats["indexed_files"],
                    'chunks_created': stats["total_chunks"]
                })
            
            logger.info(f"Directory indexing completed: {stats['indexed_files']}/{stats['total_files']} files, {stats['total_chunks']} chunks")
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
