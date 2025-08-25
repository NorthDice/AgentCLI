"""
Simple search engine for AgentCLI background indexer.
"""

import os
import re
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class SimpleSearchEngine:
    """Simple text-based search engine for project files."""
    
    def __init__(self):
        """Initialize simple search engine."""
        self.supported_extensions = {'.py', '.txt', '.md', '.json', '.yaml', '.yml', '.rst'}
    
    def build_index(self, project_path: str) -> Dict[str, Any]:
        """Build search index for project.
        
        Args:
            project_path: Path to project directory
            
        Returns:
            Search index data
        """
        index_data = {
            'files': [],
            'content_map': {},
            'timestamp': time.time()
        }
        
        try:
            for root, dirs, files in os.walk(project_path):
                # Skip hidden directories and cache
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if file should be indexed
                    if not self._should_index_file(file_path):
                        continue
                    
                    try:
                        # Read file content
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        # Store file info
                        rel_path = os.path.relpath(file_path, project_path)
                        index_data['files'].append({
                            'path': rel_path,
                            'full_path': file_path,
                            'size': len(content),
                            'lines': content.count('\n') + 1
                        })
                        
                        # Store content for searching
                        index_data['content_map'][rel_path] = content
                        
                    except Exception as e:
                        logger.warning(f"Failed to index file {file_path}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to build index: {e}")
        
        logger.info(f"Built search index with {len(index_data['files'])} files")
        return index_data
    
    def _should_index_file(self, file_path: str) -> bool:
        """Check if file should be indexed."""
        # Check extension
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.supported_extensions:
            return False
        
        # Check file size (skip very large files)
        try:
            if os.path.getsize(file_path) > 1024 * 1024:  # 1MB limit
                return False
        except:
            return False
        
        return True
    
    def update_file_index(self, file_path: str):
        """Update index for single file."""
        # For simple implementation, we'll just log this
        # In a full implementation, this would update the cached index
        logger.debug(f"File index update requested: {file_path}")
    
    def search_with_index(self, query: str, index_data: Dict[str, Any], max_results: int = 10) -> List[Dict[str, Any]]:
        """Search using pre-built index.
        
        Args:
            query: Search query
            index_data: Pre-built index data
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not index_data or 'content_map' not in index_data:
            return []
        
        results = []
        query_lower = query.lower()
        
        for file_path, content in index_data['content_map'].items():
            content_lower = content.lower()
            
            # Simple text search
            if query_lower in content_lower:
                # Find context around match
                match_index = content_lower.find(query_lower)
                
                # Get surrounding context
                start = max(0, match_index - 100)
                end = min(len(content), match_index + len(query) + 100)
                context = content[start:end].strip()
                
                results.append({
                    'file': file_path,
                    'content': context,
                    'match_position': match_index,
                    'score': self._calculate_score(query, content, file_path)
                })
        
        # Sort by score (higher is better)
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results[:max_results]
    
    def _calculate_score(self, query: str, content: str, file_path: str) -> float:
        """Calculate relevance score for search result."""
        score = 0.0
        query_lower = query.lower()
        content_lower = content.lower()
        
        # Count occurrences
        occurrences = content_lower.count(query_lower)
        score += occurrences * 10
        
        # Boost Python files
        if file_path.endswith('.py'):
            score += 5
        
        # Boost if query appears in filename
        if query_lower in os.path.basename(file_path).lower():
            score += 20
        
        return score


class SearchEngineFactory:
    """Factory for creating search engines."""
    
    @staticmethod
    def create_search_engine() -> SimpleSearchEngine:
        """Create search engine instance."""
        return SimpleSearchEngine()
