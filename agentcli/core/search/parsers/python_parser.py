"""Python language parser implementation using Tree-sitter."""

import os
from typing import List, Dict, Any, Optional
import logging

try:
    from tree_sitter import Language, Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False

from agentcli.core.search.interfaces import LanguageParser

logger = logging.getLogger(__name__)

# Path to the tree-sitter libraries
PARSERS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build")

class PythonParser(LanguageParser):
    """Python code parser using Tree-sitter."""
    
    def __init__(self):
        """Initialize the Python parser."""
        self.parser = None
        self.language = None
        self._initialize()
    
    def _initialize(self):
        """Initialize the Tree-sitter parser for Python."""
        if not TREE_SITTER_AVAILABLE:
            logger.error("tree-sitter package not installed.")
            return
            
        try:
            # Create directory for compiled language libraries if it doesn't exist
            os.makedirs(PARSERS_DIR, exist_ok=True)
            
            # Path to compiled Python grammar
            py_lib_path = os.path.join(PARSERS_DIR, "python.so")
            
            # Check if we need to build the language
            if not os.path.exists(py_lib_path):
                logger.info("Building Python grammar for Tree-sitter...")
                # This would normally require cloning and building the grammar
                # For simplicity, we'll just show an error message
                logger.error("Python grammar not found. Please build it first.")
                return
                
            # Load the language
            Language.build_library(
                py_lib_path,
                [os.path.join(PARSERS_DIR, "tree-sitter-python")]
            )
            self.language = Language(py_lib_path, "python")
            
            # Create parser
            self.parser = Parser()
            self.parser.set_language(self.language)
            logger.info("Python Tree-sitter parser initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Python parser: {str(e)}")
            self.parser = None
            self.language = None
    
    def parse_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse a Python file and extract code structures.
        
        Args:
            file_path: Path to the Python file.
            
        Returns:
            List of dictionaries containing parsed structures.
        """
        if not os.path.exists(file_path):
            logger.warning(f"File not found: {file_path}")
            return []
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            return self.parse_content(content, file_path)
        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {str(e)}")
            return []
    
    def parse_content(self, content: str, file_path: str = None) -> List[Dict[str, Any]]:
        """Parse Python content and extract code structures.
        
        Args:
            content: Python code content.
            file_path: Optional path for context.
            
        Returns:
            List of dictionaries containing parsed structures.
        """
        if not content.strip() or not self.parser:
            return []
            
        try:
            # Parse the code
            tree = self.parser.parse(bytes(content, "utf8"))
            root_node = tree.root_node
            
            # Extract code structures
            chunks = []
            
            # Get all top-level definitions (functions, classes)
            top_level_defs = [
                node for node in root_node.children 
                if node.type in ("function_definition", "class_definition")
            ]
            
            # Process imports and module docstring as a single chunk if present
            imports_and_docstring = []
            for node in root_node.children:
                if node.type in ("import_statement", "import_from_statement", "expression_statement"):
                    imports_and_docstring.append(node)
                elif node in top_level_defs:
                    break
            
            if imports_and_docstring:
                start_byte = imports_and_docstring[0].start_byte
                end_byte = imports_and_docstring[-1].end_byte
                imports_chunk = content[start_byte:end_byte].decode("utf8")
                chunks.append({
                    "content": imports_chunk,
                    "metadata": {
                        "file_path": file_path or "unknown",
                        "start_line": imports_and_docstring[0].start_point[0] + 1,
                        "end_line": imports_and_docstring[-1].end_point[0] + 1,
                        "type": "imports_and_docstring",
                        "name": "imports_and_docstring"
                    }
                })
            
            # Process each top-level definition
            for node in top_level_defs:
                # Extract the code for this definition
                start_byte = node.start_byte
                end_byte = node.end_byte
                node_content = content[start_byte:end_byte].decode("utf8")
                
                # Get the name of the definition
                name_node = None
                for child in node.children:
                    if child.type == "identifier":
                        name_node = child
                        break
                
                node_name = name_node.text.decode("utf8") if name_node else node.type
                
                # Create a chunk for this definition
                chunks.append({
                    "content": node_content,
                    "metadata": {
                        "file_path": file_path or "unknown",
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1,
                        "type": node.type,
                        "name": node_name
                    }
                })
            
            # If no chunks were created or file has content not captured in chunks,
            # create a fallback chunk for the entire file
            if not chunks:
                chunks.append({
                    "content": content,
                    "metadata": {
                        "file_path": file_path or "unknown",
                        "start_line": 1,
                        "end_line": content.count('\n') + 1,
                        "type": "file",
                        "name": os.path.basename(file_path) if file_path else "unknown"
                    }
                })
            
            return chunks
        except Exception as e:
            logger.error(f"Error parsing Python content: {str(e)}")
            return []
