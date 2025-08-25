"""Utility for formatting search results."""

import os
from typing import Dict, Any, List
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
import pygments
from pygments.lexers import get_lexer_for_filename, TextLexer
from pygments.util import ClassNotFound


def format_semantic_results(results: Dict[str, Any], console: Console, context_lines: int = 2, max_results: int = 3):
    """Format semantic search results for display.
    
    Args:
        results: Search results dictionary.
        console: Rich console instance.
        context_lines: Number of context lines to display.
        max_results: Maximum number of results to display (default: 3).
    """
    console.print(f"\n[bold]Search results for:[/] {results['query']}")
    console.print(f"Found {results['total_results']} results (showing top {min(max_results, results['total_results'])})\n")
    
    # Sort results by relevance
    sorted_results = sorted(results['results'], key=lambda x: x['relevance'], reverse=True)
    
    # Limit to max_results
    sorted_results = sorted_results[:max_results]
    
    for i, result in enumerate(sorted_results, 1):
        metadata = result['metadata']
        file_path = metadata.get('file_path', 'unknown')
        rel_path = os.path.relpath(file_path, os.getcwd()) if os.path.exists(file_path) else file_path
        function_name = metadata.get('function_name', metadata.get('name', ''))
        start_line = metadata.get('start_line', 1)
        end_line = metadata.get('end_line', 1)
        relevance = result.get('relevance', 0.0)
        content_to_display = result.get('content', metadata.get('content', ''))
        docstring = metadata.get('docstring', None)

        # Determine language for syntax highlighting
        try:
            lexer = get_lexer_for_filename(file_path)
        except ClassNotFound:
            lexer = TextLexer()

        # Create panel title
        title = f"[{i}] {rel_path}"
        if function_name:
            title += f" :: {function_name}"
        title += f"\nRelevance: {relevance:.2f}"

        # Add docstring to content if present
        if docstring:
            content_to_display = f'"""{docstring}"""\n' + content_to_display

        # Create syntax-highlighted content
        syntax = Syntax(
            content_to_display,
            lexer.name,
            line_numbers=True,
            start_line=start_line,
            theme="monokai",
            highlight_lines=range(start_line, end_line + 1)
        )

        # Display result
        console.print(Panel(syntax, title=title, expand=False))
        console.print("")
