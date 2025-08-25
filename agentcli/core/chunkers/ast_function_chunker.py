"""
AST-based chunker for Python functions.
Splits .py files into function-level chunks for semantic search.
"""

import ast
from typing import List, Dict, Any

class ASTFunctionChunker:
    """Chunker that extracts functions from Python files using AST."""
    def chunk_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Chunk a Python file into functions.
        Returns list of dicts: {'content', 'metadata'}
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        tree = ast.parse(source, filename=file_path)
        chunks = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', None)
                if not end_line:
                    if node.body:
                        end_line = node.body[-1].lineno
                    else:
                        end_line = start_line
                func_source = '\n'.join(source.splitlines()[start_line-1:end_line])
                docstring = ast.get_docstring(node)
                chunks.append({
                    "content": func_source,
                    "metadata": {
                        "function_name": node.name,
                        "file_path": file_path,
                        "start_line": start_line,
                        "end_line": end_line,
                        "docstring": docstring,
                        "chunk_type": "function"
                    }
                })
        return chunks
