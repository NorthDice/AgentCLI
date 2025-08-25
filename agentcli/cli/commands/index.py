"""Command-line interface for search commands."""

import os
import click
from rich.console import Console
from rich.panel import Panel
from typing import List, Dict, Any

from agentcli.core.search.factory import SearchServiceFactory
from agentcli.core.search.formatters import format_semantic_results


@click.group()
def index():
    """Commands for managing the search index."""
    pass


@index.command("build")
@click.option("--path", "-p", default=".", help="Path to index")
@click.option("--patterns", "-f", multiple=True, default=["*.py"], 
              help="File patterns to index (can be specified multiple times)")
def build_index(path, patterns):
    """Build or rebuild the search index."""
    console = Console()
    console.print("[bold]Building search index...[/]")
    
    search_service = SearchServiceFactory.get_default_semantic_search_service()
    stats = search_service.index_directory(path, patterns)
    
    console.print(f"\n[bold green]✓[/] Index build completed")
    console.print(f"  Total files scanned: {stats['total_files']}")
    console.print(f"  Files successfully indexed: {stats['indexed_files']}")
    console.print(f"  Total code chunks created: {stats['total_chunks']}")
    
    if stats["errors"]:
        console.print(f"\n[bold yellow]⚠ Encountered {len(stats['errors'])} errors:[/]")
        for i, error in enumerate(stats["errors"][:10], 1):
            console.print(f"  {i}. {error['file']}: {error['error']}")
        
        if len(stats["errors"]) > 10:
            console.print(f"  ... and {len(stats['errors']) - 10} more errors")


@index.command("info")
def index_info():
    """Display information about the current search index."""
    console = Console()
    
    try:
        from agentcli.core.search.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore()
        count = store.count()
        
        console.print(Panel(
            f"[bold]Search Index Information[/]\n\n"
            f"Status: {'[green]Active[/]' if count > 0 else '[yellow]Empty[/]'}\n"
            f"Documents indexed: {count}\n"
            f"Index location: {os.path.abspath(store.index_dir)}\n",
            title="Semantic Search Index",
            expand=False
        ))
    except Exception as e:
        console.print(f"[bold red]Error retrieving index information:[/] {str(e)}")


@index.command("clear")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def clear_index(yes):
    """Clear the search index."""
    console = Console()
    
    if not yes:
        console.print("[yellow]Warning:[/] This will delete the entire search index.")
        if not click.confirm("Continue?", default=False):
            console.print("Operation cancelled.")
            return
    
    try:
        from agentcli.core.search.vector_store import ChromaVectorStore
        
        store = ChromaVectorStore()
        store.clear()
        
        console.print("[bold green]✓[/] Search index cleared successfully")
    except Exception as e:
        console.print(f"[bold red]Error clearing index:[/] {str(e)}")


def add_commands_to_cli(cli):
    """Add search-related commands to the CLI."""
    cli.add_command(index)
