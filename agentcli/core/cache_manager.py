"""
Cache Manager for AgentCLI.

Handles caching of project index and structure for efficient LLM context.
"""

import os
import json
import hashlib
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching of project structure and index data."""
    
    def __init__(self, project_path: str = None):
        """Initialize cache manager.
        
        Args:
            project_path: Path to the project being analyzed
        """
        self.project_path = project_path or os.getcwd()
        self.cache_dir = os.path.join(self.project_path, '.agentcli', 'cache')
        self._ensure_cache_dir()
        
        # Cache files
        self.structure_cache_file = os.path.join(self.cache_dir, 'structure.json')
        self.index_cache_file = os.path.join(self.cache_dir, 'index.json')
        self.metadata_file = os.path.join(self.cache_dir, 'metadata.json')
        
        # In-memory caches
        self._structure_cache: Optional[Dict[str, Any]] = None
        self._index_cache: Optional[Dict[str, Any]] = None
        self._file_hashes: Dict[str, str] = {}
        self._metadata: Dict[str, Any] = self._load_metadata()
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
        
        return {
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'file_hashes': {},
            'cache_version': '1.0'
        }
    
    def _save_metadata(self):
        """Save cache metadata."""
        self._metadata['last_updated'] = datetime.now().isoformat()
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def _get_file_hash(self, file_path: str) -> str:
        """Get hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def _get_project_files_hashes(self) -> Dict[str, str]:
        """Get hashes of all relevant project files."""
        file_hashes = {}
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip cache and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if file.endswith(('.py', '.txt', '.md', '.json', '.yaml', '.yml')):
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, self.project_path)
                    file_hashes[rel_path] = self._get_file_hash(file_path)
        
        return file_hashes
    
    def is_cache_valid(self) -> bool:
        """Check if current cache is valid."""
        if not all([
            os.path.exists(self.structure_cache_file),
            os.path.exists(self.index_cache_file),
            os.path.exists(self.metadata_file)
        ]):
            return False
        
        # Check if any files have changed
        current_hashes = self._get_project_files_hashes()
        cached_hashes = self._metadata.get('file_hashes', {})
        
        return current_hashes == cached_hashes
    
    def get_structure_cache(self) -> Optional[Dict[str, Any]]:
        """Get cached project structure."""
        if self._structure_cache is not None:
            return self._structure_cache
        
        if os.path.exists(self.structure_cache_file):
            try:
                with open(self.structure_cache_file, 'r') as f:
                    self._structure_cache = json.load(f)
                    logger.debug("Loaded structure cache from disk")
                    return self._structure_cache
            except Exception as e:
                logger.warning(f"Failed to load structure cache: {e}")
        
        return None
    
    def set_structure_cache(self, structure_data: Dict[str, Any]):
        """Cache project structure."""
        self._structure_cache = structure_data
        
        try:
            with open(self.structure_cache_file, 'w') as f:
                json.dump(structure_data, f, indent=2)
            logger.debug("Saved structure cache to disk")
        except Exception as e:
            logger.error(f"Failed to save structure cache: {e}")
    
    def get_index_cache(self) -> Optional[Dict[str, Any]]:
        """Get cached project index."""
        if self._index_cache is not None:
            return self._index_cache
        
        if os.path.exists(self.index_cache_file):
            try:
                with open(self.index_cache_file, 'r') as f:
                    self._index_cache = json.load(f)
                    logger.debug("Loaded index cache from disk")
                    return self._index_cache
            except Exception as e:
                logger.warning(f"Failed to load index cache: {e}")
        
        return None
    
    def set_index_cache(self, index_data: Dict[str, Any]):
        """Cache project index."""
        self._index_cache = index_data
        
        try:
            with open(self.index_cache_file, 'w') as f:
                json.dump(index_data, f, indent=2)
            logger.debug("Saved index cache to disk")
        except Exception as e:
            logger.error(f"Failed to save index cache: {e}")
    
    def update_file_in_cache(self, file_path: str):
        """Update single file in cache after modification."""
        rel_path = os.path.relpath(file_path, self.project_path)
        new_hash = self._get_file_hash(file_path)
        
        # Update metadata
        self._metadata['file_hashes'][rel_path] = new_hash
        self._save_metadata()
        
        # Invalidate affected caches
        if self._structure_cache:
            # TODO: Update structure cache incrementally
            logger.debug(f"Structure cache needs update for {rel_path}")
        
        if self._index_cache:
            # TODO: Update index cache incrementally
            logger.debug(f"Index cache needs update for {rel_path}")
    
    def invalidate_cache(self):
        """Invalidate all caches."""
        self._structure_cache = None
        self._index_cache = None
        
        # Remove cache files
        for cache_file in [self.structure_cache_file, self.index_cache_file]:
            if os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    logger.debug(f"Removed cache file: {cache_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove cache file {cache_file}: {e}")
    
    def finalize_cache(self):
        """Finalize cache with current file hashes."""
        current_hashes = self._get_project_files_hashes()
        self._metadata['file_hashes'] = current_hashes
        self._save_metadata()
        logger.debug("Finalized cache with current file hashes")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_dir': self.cache_dir,
            'structure_cached': self._structure_cache is not None,
            'index_cached': self._index_cache is not None,
            'cache_valid': self.is_cache_valid(),
            'last_updated': self._metadata.get('last_updated'),
            'files_tracked': len(self._metadata.get('file_hashes', {}))
        }
