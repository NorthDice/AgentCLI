"""
ChromaDB Indexer for AgentCLI.

Handles indexing project files into ChromaDB with intelligent caching.
"""

import os
import time
import logging
import threading
from typing import Dict, Any, Optional, List
from queue import Queue, Empty
from dataclasses import dataclass
from pathlib import Path

import chromadb
from chromadb.config import Settings

from agentcli.core.cache_manager import CacheManager
from agentcli.core.structure_provider import StructureProvider
from agentcli.core.file_watcher import FileWatcher

logger = logging.getLogger(__name__)


@dataclass
class IndexingTask:
    """Represents an indexing task."""
    task_type: str  # 'full_project', 'single_file', 'structure_only'
    file_path: Optional[str] = None
    priority: int = 0  # Lower number = higher priority


class ChromaIndexer:
    """Handles ChromaDB indexing of project files and structure."""
    
    def __init__(self, project_path: str = None):
        """Initialize ChromaDB indexer.
        
        Args:
            project_path: Path to project to index
        """
        self.project_path = project_path or os.getcwd()
        self.cache_manager = CacheManager(self.project_path)
        self.structure_provider = StructureProvider()
        
        # ChromaDB setup
        self.chroma_db_path = os.path.join(self.project_path, '.agentcli', 'chromadb')
        os.makedirs(self.chroma_db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Collections
        self.code_collection = None
        self.structure_collection = None
        self._init_collections()
        
        # Threading components
        self._indexing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._task_queue = Queue()
        self._is_running = False
        
        # State
        self._indexing_status = "idle"  # idle, indexing, ready, error
        self._last_indexing_time: Optional[float] = None
        self._indexed_files_count = 0
        
        # Callbacks
        self._status_callbacks = []
        
        # File watcher for automatic indexing
        self._file_watcher: Optional[FileWatcher] = None
    
    def _init_collections(self):
        """Initialize ChromaDB collections."""
        try:
            # Code files collection
            self.code_collection = self.client.get_or_create_collection(
                name="code_files",
                metadata={"description": "Code files and content"}
            )
            
            # Project structure collection
            self.structure_collection = self.client.get_or_create_collection(
                name="project_structure",
                metadata={"description": "Project structure and metadata"}
            )
            
            logger.info("ChromaDB collections initialized")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB collections: {e}")
            raise
    
    def add_status_callback(self, callback):
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
            logger.warning("ChromaDB indexer already running")
            return
        
        self._is_running = True
        self._stop_event.clear()
        
        self._indexing_thread = threading.Thread(
            target=self._indexing_worker,
            name="AgentCLI-ChromaIndexer",
            daemon=True
        )
        self._indexing_thread.start()
        
        logger.info("ChromaDB indexer started")
        
        # Start file watcher for automatic indexing
        self._file_watcher = FileWatcher(
            project_path=self.project_path,
            on_file_change=self._on_file_change
        )
        self._file_watcher.start()
        
        # Queue initial full project indexing if needed
        if not self._is_project_indexed():
            self.queue_full_project_indexing()
        else:
            logger.info("Project already indexed in ChromaDB")
            self._notify_status("ready", {"using_existing_index": True})
    
    def stop(self):
        """Stop background indexing."""
        if not self._is_running:
            return
        
        logger.info("Stopping ChromaDB indexer...")
        self._is_running = False
        self._stop_event.set()
        
        # Stop file watcher
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None
        
        # Add stop sentinel
        self._task_queue.put(None)
        
        if self._indexing_thread and self._indexing_thread.is_alive():
            self._indexing_thread.join(timeout=5.0)
        
        logger.info("ChromaDB indexer stopped")
    
    def _is_project_indexed(self) -> bool:
        """Check if project is already indexed."""
        try:
            count = self.code_collection.count()
            return count > 0
        except:
            return False
    
    def queue_full_project_indexing(self):
        """Queue full project indexing."""
        task = IndexingTask(task_type="full_project", priority=1)
        self._task_queue.put(task)
        logger.debug("Queued full project indexing")
    
    def queue_file_indexing(self, file_path: str):
        """Queue single file indexing."""
        task = IndexingTask(
            task_type="single_file", 
            file_path=file_path, 
            priority=0
        )
        self._task_queue.put(task)
        logger.debug(f"Queued file indexing: {file_path}")
    
    def queue_structure_update(self):
        """Queue structure analysis update."""
        task = IndexingTask(task_type="structure_only", priority=2)
        self._task_queue.put(task)
        logger.debug("Queued structure update")
    
    def _indexing_worker(self):
        """Main indexing worker thread."""
        logger.debug("ChromaDB indexing worker started")
        
        while self._is_running and not self._stop_event.is_set():
            try:
                task = self._task_queue.get(timeout=1.0)
                
                if task is None:  # Stop sentinel
                    break
                
                self._process_indexing_task(task)
                self._task_queue.task_done()
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error in indexing worker: {e}")
                self._notify_status("error", {"error": str(e)})
        
        logger.debug("ChromaDB indexing worker stopped")
    
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
                
        except Exception as e:
            logger.error(f"Failed to process indexing task {task.task_type}: {e}")
            self._notify_status("error", {"task": task.task_type, "error": str(e)})
        
        self._last_indexing_time = time.time() - start_time
    
    def _process_full_project_indexing(self):
        """Process full project indexing."""
        self._notify_status("indexing", {"type": "full_project"})
        logger.info("Starting full project indexing to ChromaDB...")
        
        indexed_count = 0
        
        for root, dirs, files in os.walk(self.project_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if not self._should_index_file(file):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    self._index_single_file(file_path)
                    indexed_count += 1
                except Exception as e:
                    logger.warning(f"Failed to index {file_path}: {e}")
        
        # Index project structure
        self._index_project_structure()
        
        self._indexed_files_count = indexed_count
        logger.info(f"Indexed {indexed_count} files to ChromaDB")
        self._notify_status("ready", {
            "type": "full_project",
            "files_indexed": indexed_count,
            "duration": self._last_indexing_time
        })
    
    def _should_index_file(self, filename: str) -> bool:
        """Check if file should be indexed."""
        # Index code files, docs, configs
        extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', 
                     '.md', '.rst', '.txt', '.json', '.yaml', '.yml', 
                     '.toml', '.ini', '.cfg', '.conf'}
        return any(filename.endswith(ext) for ext in extensions)
    
    def _index_single_file(self, file_path: str):
        """Index single file to ChromaDB. For .py files, index each function as a separate chunk."""
        try:
            rel_path = os.path.relpath(file_path, self.project_path)
            ext = os.path.splitext(file_path)[1]
            if ext == ".py":
                # AST chunking for Python files
                from agentcli.core.chunkers.ast_function_chunker import ASTFunctionChunker
                chunker = ASTFunctionChunker()
                chunks = chunker.chunk_file(file_path)
                for chunk in chunks:
                    func_id = f"{rel_path}:{chunk['function_name']}:{chunk['start_line']}"
                    # Remove existing entry if exists
                    try:
                        self.code_collection.delete(ids=[func_id])
                    except:
                        pass
                    self.code_collection.add(
                        documents=[chunk['content']],
                        metadatas=[{
                            "file_path": rel_path,
                            "full_path": file_path,
                            "file_type": ext,
                            "function_name": chunk['function_name'],
                            "start_line": chunk['start_line'],
                            "end_line": chunk['end_line'],
                            "docstring": chunk['docstring'],
                            "indexed_at": time.time()
                        }],
                        ids=[func_id]
                    )
            else:
                # Non-Python files: index whole file as one chunk
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if len(content.strip()) == 0:
                    return
                file_id = f"file_{hash(rel_path)}"
                try:
                    self.code_collection.delete(ids=[file_id])
                except:
                    pass
                self.code_collection.add(
                    documents=[content],
                    metadatas=[{
                        "file_path": rel_path,
                        "full_path": file_path,
                        "file_type": ext,
                        "size": len(content),
                        "indexed_at": time.time()
                    }],
                    ids=[file_id]
                )
        except Exception as e:
            logger.error(f"Failed to index file {file_path}: {e}")
            raise
    
    def _index_project_structure(self):
        """Index project structure."""
        try:
            structure_data = self.structure_provider.get_structure_summary(self.project_path)
            
            structure_id = "project_structure"
            
            # Remove existing
            try:
                self.structure_collection.delete(ids=[structure_id])
            except:
                pass
            
            # Add structure
            self.structure_collection.add(
                documents=[structure_data],
                metadatas=[{
                    "project_path": self.project_path,
                    "indexed_at": time.time(),
                    "type": "project_structure"
                }],
                ids=[structure_id]
            )
            
        except Exception as e:
            logger.error(f"Failed to index project structure: {e}")
    
    def _process_single_file_indexing(self, file_path: str):
        """Process single file indexing."""
        if not file_path or not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return
        
        self._notify_status("indexing", {"type": "single_file", "file": file_path})
        logger.debug(f"Indexing file to ChromaDB: {file_path}")
        
        self._index_single_file(file_path)
        
        # Update structure if Python file
        if file_path.endswith('.py'):
            self.queue_structure_update()
        
        logger.debug(f"File indexed: {file_path}")
        self._notify_status("ready", {"type": "single_file", "file": file_path})
    
    def _process_structure_update(self):
        """Process structure update."""
        self._notify_status("indexing", {"type": "structure_only"})
        logger.debug("Updating project structure in ChromaDB...")
        
        self._index_project_structure()
        
        logger.debug("Structure updated")
        self._notify_status("ready", {"type": "structure_only"})
    
    def search_code(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search code in ChromaDB."""
        try:
            results = self.code_collection.query(
                query_texts=[query],
                n_results=max_results,
                include=["documents", "metadatas", "distances"]
            )
            
            search_results = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0],
                results['metadatas'][0], 
                results['distances'][0]
            )):
                search_results.append({
                    'file': metadata['file_path'],
                    'content': doc[:500] + "..." if len(doc) > 500 else doc,
                    'score': 1 - distance,  # Convert distance to similarity
                    'metadata': metadata
                })
            
            return search_results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_project_structure(self) -> Optional[str]:
        """Get cached project structure from ChromaDB."""
        try:
            results = self.structure_collection.get(
                ids=["project_structure"],
                include=["documents"]
            )
            
            if results['documents']:
                return results['documents'][0]
            return None
            
        except Exception as e:
            logger.error(f"Failed to get project structure: {e}")
            return None
    
    def get_status(self) -> Dict[str, Any]:
        """Get current indexing status."""
        try:
            code_count = self.code_collection.count()
            structure_count = self.structure_collection.count()
        except:
            code_count = 0
            structure_count = 0
        
        return {
            'status': self._indexing_status,
            'is_running': self._is_running,
            'queue_size': self._task_queue.qsize(),
            'last_indexing_time': self._last_indexing_time,
            'indexed_files_count': self._indexed_files_count,
            'chromadb_stats': {
                'code_files': code_count,
                'structure_entries': structure_count,
                'db_path': self.chroma_db_path
            }
        }
    
    def _on_file_change(self, file_path: str):
        """Handle file change event from FileWatcher."""
        logger.info(f"Auto-indexing file change: {file_path}")
        self.queue_file_indexing(file_path)
        
        # Update cache for the changed file
        if self.cache_manager:
            self.cache_manager.update_file_in_cache(file_path)
