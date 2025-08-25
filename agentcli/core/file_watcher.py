"""
File Watcher for automatic indexing of new/modified files.
"""

import os
import time
import logging
from typing import Set, Callable
from threading import Thread, Event
from pathlib import Path

logger = logging.getLogger(__name__)


class FileWatcher:
    """Watches for file changes and triggers indexing."""
    
    def __init__(self, project_path: str, on_file_change: Callable[[str], None]):
        self.project_path = project_path
        self.on_file_change = on_file_change
        self._stop_event = Event()
        self._watch_thread = None
        self._last_scan_time = time.time()
        self._known_files: Set[str] = set()
        
    def start(self):
        """Start file watching."""
        self._scan_initial_files()
        self._watch_thread = Thread(target=self._watch_loop, daemon=True)
        self._watch_thread.start()
        logger.info("File watcher started")
        
    def stop(self):
        """Stop file watching."""
        self._stop_event.set()
        if self._watch_thread:
            self._watch_thread.join(timeout=1.0)
        logger.info("File watcher stopped")
        
    def _scan_initial_files(self):
        """Scan initial files."""
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if self._should_watch_file(file):
                    file_path = os.path.join(root, file)
                    self._known_files.add(file_path)
                    
    def _should_watch_file(self, filename: str) -> bool:
        """Check if file should be watched."""
        extensions = {'.py', '.js', '.ts', '.md', '.json', '.yaml', '.yml', '.txt'}
        return any(filename.endswith(ext) for ext in extensions)
        
    def _watch_loop(self):
        """Main watching loop."""
        while not self._stop_event.is_set():
            try:
                self._check_for_changes()
                time.sleep(2.0)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"File watcher error: {e}")
                
    def _check_for_changes(self):
        """Check for file changes."""
        current_files = set()
        
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if self._should_watch_file(file):
                    file_path = os.path.join(root, file)
                    current_files.add(file_path)
                    
                    # Check if file is new or modified
                    if file_path not in self._known_files:
                        logger.info(f"New file detected: {file_path}")
                        self.on_file_change(file_path)
                    elif os.path.getmtime(file_path) > self._last_scan_time:
                        logger.info(f"Modified file detected: {file_path}")
                        self.on_file_change(file_path)
        
        # Detect deleted files
        deleted_files = self._known_files - current_files
        for deleted_file in deleted_files:
            logger.info(f"Deleted file detected: {deleted_file}")
            # TODO: Remove from ChromaDB
            
        self._known_files = current_files
        self._last_scan_time = time.time()
