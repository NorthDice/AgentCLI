"""Search functionality for AgentCLI."""

# Re-export text search functions
from ..text_search import search_files, format_search_results

# Interfaces
from agentcli.core.search.interfaces.chunker import CodeChunker
from agentcli.core.search.interfaces.embedder import Embedder
from agentcli.core.search.interfaces.vector_store import VectorStore
from agentcli.core.search.interfaces.search_service import SearchService

# Components for semantic search
from agentcli.core.search.chunker import TreeSitterChunker as SmartChunker  # Алиас для обратной совместимости
from agentcli.core.search.chunker import TreeSitterChunker
from agentcli.core.search.embedder import SentenceTransformerEmbedder
from agentcli.core.search.vector_store import ChromaVectorStore
from agentcli.core.search.semantic_search import SemanticSearchService
from agentcli.core.search.formatters import format_semantic_results
from agentcli.core.search.factory import SearchServiceFactory

# Helper function to perform semantic search
def perform_semantic_search(query: str, path: str = ".", top_k: int = 5, rebuild_index: bool = False):
    """Perform semantic search."""
    search_service = SearchServiceFactory.get_default_semantic_search_service()
    if rebuild_index:
        search_service.rebuild_index()
    return search_service.search(query=query, top_k=top_k)

__all__ = [
    # Basic search
    'search_files', 'format_search_results',
    
    # Interfaces
    'CodeChunker', 'Embedder', 'VectorStore', 'SearchService',
    
    # Components
    'TreeSitterChunker', 'SentenceTransformerEmbedder', 'ChromaVectorStore', 
    'SemanticSearchService', 'SearchServiceFactory',
    
    # Semantic search functions
    'perform_semantic_search', 'format_semantic_results'
]
