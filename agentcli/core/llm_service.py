"""Module with base classes for LLM services."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


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
