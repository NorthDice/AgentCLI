#!/usr/bin/env python
"""Test script for improved code chunking."""

import os
import sys
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agentcli.core.search.chunker import TreeSitterChunker
from agentcli.core.search.parsers.python_parser import PythonParser

def main():
    """Main entry point for testing improved chunker."""
    parser = argparse.ArgumentParser(
        description="Test improved code chunking with sample files."
    )
    
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the file to chunk."
    )
    
    parser.add_argument(
        "--method",
        choices=["smart", "tree-sitter", "basic"],
        default="smart",
        help="Chunking method to use."
    )
    
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.isfile(args.file_path):
        print(f"Error: File {args.file_path} does not exist.")
        sys.exit(1)
    
    # Create chunker based on method
    if args.method == "tree-sitter":
        # Try to use tree-sitter parser
        try:
            chunker = TreeSitterChunker({'.py': PythonParser()})
            method_name = "Tree-sitter based chunking"
        except ImportError:
            print("Warning: Tree-sitter not available. Falling back to smart chunking.")
            chunker = TreeSitterChunker()
            method_name = "Smart line-based chunking (fallback)"
    elif args.method == "smart":
        # Use smart line-based chunking
        chunker = TreeSitterChunker()
        method_name = "Smart line-based chunking"
    else:  # basic
        # Use basic line-based chunking with custom _chunk_by_lines implementation
        chunker = TreeSitterChunker()
        # Override _chunk_by_lines to use basic chunking
        chunker._chunk_by_lines = lambda content, file_path=None, **kwargs: basic_chunk_by_lines(content, file_path)
        method_name = "Basic line-based chunking"
    
    # Chunk the file
    chunks = chunker.chunk_file(args.file_path)
    
    # Display results
    console = Console()
    console.print(Panel(f"[bold]Chunking Results for {os.path.basename(args.file_path)}[/]"))
    console.print(f"Method: {method_name}")
    console.print(f"Total chunks: {len(chunks)}")
    console.print()
    
    # Display each chunk
    for i, chunk in enumerate(chunks, 1):
        metadata = chunk["metadata"]
        content = chunk["content"]
        
        # Determine file extension for syntax highlighting
        ext = os.path.splitext(args.file_path)[1] or ".txt"
        language = ext.lstrip(".")
        
        # Create syntax highlighted content
        syntax = Syntax(
            content,
            language,
            theme="monokai",
            line_numbers=True,
            start_line=metadata["start_line"]
        )
        
        # Create panel title
        title = f"[bold]Chunk {i}: {metadata['name']} (Lines {metadata['start_line']}-{metadata['end_line']}, Type: {metadata['type']})[/]"
        
        # Display
        console.print(Panel(syntax, title=title))
        console.print()

def basic_chunk_by_lines(content, file_path=None, chunk_size=50):
    """Basic line-based chunking for comparison."""
    chunks = []
    lines = content.split("\n")
    
    for i in range(0, len(lines), chunk_size):
        chunk_lines = lines[i:i+chunk_size]
        chunk_content = "\n".join(chunk_lines)
        
        if not chunk_content.strip():
            continue
            
        chunks.append({
            "content": chunk_content,
            "metadata": {
                "file_path": file_path or "unknown",
                "start_line": i + 1,
                "end_line": min(i + chunk_size, len(lines)),
                "type": "basic_chunk",
                "name": f"basic_chunk_{i//chunk_size+1}"
            }
        })
    
    return chunks

if __name__ == "__main__":
    main()
