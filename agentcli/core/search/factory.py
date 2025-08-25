"""Factory for creating search services."""

import logging
from typing import Dict, Any, Optional
from agentcli.core.search.interfaces import SearchService
from agentcli.core.search.embedder import SentenceTransformerEmbedder
from agentcli.core.search.vector_store import ChromaVectorStore
from agentcli.core.search.semantic_search import SemanticSearchService

logger = logging.getLogger(__name__)

class SearchServiceFactory:
    """Factory for creating search services."""
    
    @staticmethod
    def create_semantic_search_service(config: Dict[str, Any] = None) -> SearchService:
        """Create a semantic search service.
        
        Args:
            config: Optional configuration dictionary.
            
        Returns:
            Configured SearchService instance.
        """
        config = config or {}
        
        from agentcli.core.chunkers.ast_function_chunker import ASTFunctionChunker
        chunker = ASTFunctionChunker()
        embedder = SentenceTransformerEmbedder(
            model_name=config.get("model_name", "all-mpnet-base-v2")
        )
        vector_store = ChromaVectorStore(
            index_dir=config.get("index_dir", ".agentcli/search_index"),
            collection_name=config.get("collection_name", "code_chunks")
        )

        return SemanticSearchService(chunker, embedder, vector_store)
    
    @staticmethod
    def get_default_semantic_search_service() -> SearchService:
        """Get the default semantic search service.
        
        Returns:
            Default SearchService instance.
        """
        return SearchServiceFactory.create_semantic_search_service()
