"""Module for text-based search."""

import os
import re
from typing import List, Dict, Any

# Import core search functions if they exist
try:
    from agentcli.core.search import search_files as existing_search_files
    CORE_SEARCH_AVAILABLE = True
except ImportError:
    CORE_SEARCH_AVAILABLE = False

def search_files(query: str, path: str, file_pattern: str = "*", is_regex: bool = False,
                use_gitignore: bool = True, case_sensitive: bool = False) -> List[Dict[str, Any]]:
    """Search for text in files.
    
    Args:
        query: Text to search for.
        path: Path to search in.
        file_pattern: File pattern to match.
        is_regex: Whether to use regex for searching.
        use_gitignore: Whether to respect .gitignore rules.
        case_sensitive: Whether to perform case-sensitive search.
        
    Returns:
        List of dictionaries with search results.
    """
    # This is an existing function that we're not modifying
    # It should be already implemented in the AgentCLI project
    # We're just creating a stub here to avoid import errors
    if CORE_SEARCH_AVAILABLE:
        return existing_search_files(
            query=query,
            path=path,
            file_pattern=file_pattern,
            is_regex=is_regex,
            use_gitignore=use_gitignore,
            case_sensitive=case_sensitive
        )
    else:
        # Simple implementation if the original function is not available
        return []

def format_search_results(results: List[Dict[str, Any]], format_type: str = "normal", base_path: str = ".") -> str:
    """Format search results.
    
    Args:
        results: List of search results.
        format_type: Type of formatting to apply.
        base_path: Base path for relative paths.
        
    Returns:
        Formatted search results.
    """
    # This is an existing function that we're not modifying
    # It should be already implemented in the AgentCLI project
    # We're just creating a stub here to avoid import errors
    if CORE_SEARCH_AVAILABLE:
        try:
            from agentcli.core.search import format_search_results as existing_format_results
            return existing_format_results(results, format_type, base_path)
        except (ImportError, AttributeError):
            pass
    
    # Simple implementation if the original function is not available
    return "\n".join([f"{r.get('file', 'unknown')}: {len(r.get('matches', []))} matches" for r in results])
