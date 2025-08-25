"""
Background indexing system for AgentCLI.

Handles automatic project indexing and structure analysis in the background.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, Callable
from queue import Queue, Empty
from dataclasses import dataclass
from pathlib import Path

from agentcli.core.cache_manager import CacheManager
from agentcli.core.structure_provider import StructureProvider
from agentcli.core.search.semantic_search import SemanticSearchService
from agentcli.core.chunkers.ast_function_chunker import ASTFunctionChunker
from agentcli.core.search.embedder import SentenceTransformerEmbedder
from agentcli.core.search.vector_store import ChromaVectorStore

logger = logging.getLogger(__name__)


@dataclass
class IndexingTask:
    """Represents an indexing task."""
    task_type: str 
    file_path: Optional[str] = None
    priority: int = 0  
    callback: Optional[Callable] = None


class BackgroundIndexer:
    """Handles background indexing of project files and structure."""
    
    def __init__(self, project_path: str = None):
        """Initialize background indexer.
        
        Args:
            project_path: Path to project to index
        """
        self.project_path = project_path or os.getcwd()
        self.cache_manager = CacheManager(self.project_path)
        self.structure_provider = StructureProvider()

        self._indexing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._task_queue = Queue()
        self._is_running = False
        
        self._indexing_status = "idle"  
        self._last_indexing_time: Optional[float] = None
        self._indexed_files_count = 0
        
        self._status_callbacks = []
        
        try:
            chunker = ASTFunctionChunker()
            embedder = SentenceTransformerEmbedder() 
            vector_store = ChromaVectorStore()
            self.search_engine = SemanticSearchService(chunker, embedder, vector_store)
        except Exception as e:
            logger.warning(f"Failed to initialize semantic search engine: {e}")
            self.search_engine = None
    
    def add_status_callback(self, callback: Callable[[str, Dict[str, Any]], None]):
        """Add callback for status updates."""
        self._status_callbacks.append(callback)
    
    def _notify_status(self, status: str, details: Dict[str, Any] = None):
        """Notify status callbacks."""
        self._indexing_status = status
        details = details or {}
        
        for callback in self._status_callbacks:
            try:
                callback(status, details)
            except Exception as e:
                logger.error(f"Status callback error: {e}")
    
    def start(self):
        """Start background indexing."""
        if self._is_running:
            logger.warning("Background indexer already running")
            return
        
        self._is_running = True
        self._stop_event.clear()
        
        self._indexing_thread = threading.Thread(
            target=self._indexing_worker,
            name="AgentCLI-Indexer",
            daemon=True
        )
        self._indexing_thread.start()
        
        logger.info("Background indexer started")
        
        if not self.cache_manager.is_cache_valid():
            self.queue_full_project_indexing()
        else:
            logger.info("Using existing valid cache")
            self._notify_status("ready", {"using_cache": True})
    
    def stop(self):
        """Stop background indexing."""
        if not self._is_running:
            return
        
        logger.info("Stopping background indexer...")
        self._is_running = False
        self._stop_event.set()
        
        self._task_queue.put(None)
        
        if self._indexing_thread and self._indexing_thread.is_alive():
            self._indexing_thread.join(timeout=5.0)
        
        logger.info("Background indexer stopped")
    
    def queue_full_project_indexing(self, callback: Callable = None):
        """Queue full project indexing."""
        task = IndexingTask(
            task_type="full_project",
            priority=1,
            callback=callback
        )
        self._task_queue.put(task)
        logger.debug("Queued full project indexing")
    
    def queue_file_indexing(self, file_path: str, callback: Callable = None):
        """Queue single file indexing."""
        task = IndexingTask(
            task_type="single_file",
            file_path=file_path,
            priority=0, 
            callback=callback
        )
        self._task_queue.put(task)
        logger.debug(f"Queued file indexing: {file_path}")
    
    def queue_structure_update(self, callback: Callable = None):
        """Queue structure analysis only."""
        task = IndexingTask(
            task_type="structure_only",
            priority=2,
            callback=callback
        )
        self._task_queue.put(task)
        logger.debug("Queued structure update")
    
    def _indexing_worker(self):
        """Main indexing worker thread."""
        logger.debug("Indexing worker started")
        
        while self._is_running and not self._stop_event.is_set():
            try:
                task = self._task_queue.get(timeout=1.0)
                
                if task is None:
                    break
                
                self._process_indexing_task(task)
                
                self._task_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in indexing worker: {e}")
                self._notify_status("error", {"error": str(e)})
        
        logger.debug("Indexing worker stopped")
    
    def _process_indexing_task(self, task: IndexingTask):
        """Process a single indexing task."""
        start_time = time.time()
        
        try:
            if task.task_type == "full_project":
                self._process_full_project_indexing()
            elif task.task_type == "single_file":
                self._process_single_file_indexing(task.file_path)
            elif task.task_type == "structure_only":
                self._process_structure_update()
            
            if task.callback:
                task.callback(True, None)
                
        except Exception as e:
            logger.error(f"Failed to process indexing task {task.task_type}: {e}")
            self._notify_status("error", {"task": task.task_type, "error": str(e)})
            
            if task.callback:
                task.callback(False, str(e))
        
        self._last_indexing_time = time.time() - start_time
    
    def _process_full_project_indexing(self):
        """Process full project indexing."""
        self._notify_status("indexing", {"type": "full_project"})
        logger.info("Starting full project indexing...")
        logger.info(f"[DIAG] Индексируемый путь: {self.project_path}")
        structure_data = self.structure_provider.get_structure_summary(self.project_path)
        logger.info(f"[DIAG] Структура проекта: {structure_data}")
        self.cache_manager.set_structure_cache({
            'summary': structure_data,
            'timestamp': time.time()
        })
        old_hashes = self.cache_manager._metadata.get('file_hashes', {})
        new_hashes = self.cache_manager._get_project_files_hashes()
        changed_files = []
        removed_files = []
        for rel_path, new_hash in new_hashes.items():
            old_hash = old_hashes.get(rel_path)
            if old_hash != new_hash:
                changed_files.append(os.path.join(self.project_path, rel_path))
        for rel_path in old_hashes:
            if rel_path not in new_hashes:
                removed_files.append(os.path.join(self.project_path, rel_path))
        logger.info(f"[DIAG] Изменённые/новые файлы для индексации: {len(changed_files)}")
        logger.info(f"[DIAG] Удалённые файлы: {len(removed_files)}")
        stats = {
            "directory": self.project_path,
            "total_files": len(changed_files),
            "indexed_files": 0,
            "total_chunks": 0,
            "errors": []
        }
        if self.search_engine:
            for file_path in changed_files:
                try:
                    result = self.search_engine.index_file(file_path)
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
        self.cache_manager.set_index_cache({
            'index': stats,
            'timestamp': time.time()
        })
        self._indexed_files_count = stats.get('indexed_files', 0)
        self.cache_manager.finalize_cache()
        logger.info(f"Full project indexing completed. Indexed {self._indexed_files_count} files")
        self._notify_status("ready", {
            "type": "full_project",
            "files_indexed": self._indexed_files_count,
            "duration": self._last_indexing_time
        })
    
    def _process_single_file_indexing(self, file_path: str):
        """Process single file indexing."""
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"File not found for indexing: {file_path}")
            return
        
        self._notify_status("indexing", {"type": "single_file", "file": file_path})
        logger.debug(f"Indexing single file: {file_path}")
        
        self.cache_manager.update_file_in_cache(file_path)

        if self.search_engine:
            self.search_engine.index_file(file_path)
 
        if file_path.endswith('.py'):
            self.queue_structure_update()
        
        logger.debug(f"Single file indexing completed: {file_path}")
        self._notify_status("ready", {"type": "single_file", "file": file_path})
    
    def _process_structure_update(self):
        """Process structure update only."""
        self._notify_status("indexing", {"type": "structure_only"})
        logger.debug("Updating project structure...")

        structure_data = self.structure_provider.get_structure_summary(self.project_path)
        self.cache_manager.set_structure_cache({
            'summary': structure_data,
            'timestamp': time.time()
        })
        
        logger.debug("Structure update completed")
        self._notify_status("ready", {"type": "structure_only"})
    
    def get_status(self) -> Dict[str, Any]:
        """Get current indexing status."""
        return {
            'status': self._indexing_status,
            'is_running': self._is_running,
            'queue_size': self._task_queue.qsize(),
            'last_indexing_time': self._last_indexing_time,
            'indexed_files_count': self._indexed_files_count,
            'cache_stats': self.cache_manager.get_cache_stats()
        }
    
    def get_cached_structure(self) -> Optional[str]:
        """Get cached project structure for LLM context."""
        cache_data = self.cache_manager.get_structure_cache()
        if cache_data:
            return cache_data.get('summary')
        return None
    
    def get_cached_index(self) -> Optional[Dict[str, Any]]:
        """Get cached search index."""
        cache_data = self.cache_manager.get_index_cache()
        if cache_data:
            return cache_data.get('index')
        return None
    
    def search_in_cache(self, query: str, top_k: int = 10) -> Optional[list]:
        """Semantic search in project files."""
        if not self.search_engine:
            return None
        return self.search_engine.search(query, top_k=top_k).get('results', [])
