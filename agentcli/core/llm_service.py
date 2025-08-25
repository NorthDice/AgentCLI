"""Module with base classes for LLM services."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class LLMService(ABC):
    """Abstract base class for LLM services."""
    
    def __init__(self):
        """Initialize service."""
        pass
    
    @abstractmethod
    def generate_actions(self, query: str) -> List[Dict[str, Any]]:
        """Generate list of actions based on query.
        
        Args:
            query (str): Natural language query.
            
        Returns:
            List[Dict[str, Any]]: List of actions.
        """
        pass


def create_llm_service() -> LLMService:
    """Create LLM service instance.
    
    Returns:
        LLMService: LLM service instance.
        
    Raises:
        ImportError: When Azure OpenAI service cannot be imported.
    """
    try:
        from agentcli.core.azure_llm import get_llm_service as create_azure_service
        return create_azure_service()
    except Exception as e:
        logger.error(f"Failed to create LLM service: {e}")
        raise ImportError(f"Cannot create LLM service: {e}")
