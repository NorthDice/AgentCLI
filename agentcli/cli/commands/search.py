"""Search command for finding text in the project."""

import os
import click
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
from rich.markup import escape

from agentcli.core.search import (
    perform_semantic_search, format_semantic_results,
    search_files, format_search_results
)
from agentcli.core.enhanced_search import enhanced_search, format_enhanced_results


def show_search_metrics(console: Console, operation_context) -> None:
    """Show performance metrics for search operation."""
    try:
        from agentcli.core.performance.collector import metrics_collector
        
        # Get the last recorded metric (our current operation)
        recent_metrics = metrics_collector.get_recent_metrics(1)
        if not recent_metrics:
            return
            
        metric = recent_metrics[0]
        
        console.print("\n[bold]⚡ Performance Metrics:[/bold]")
        console.print(f"  Duration: [cyan]{metric.duration:.3f}s[/cyan]")
        console.print(f"  Memory Delta: [cyan]{metric.memory_delta_mb:+.2f} MB[/cyan]")
        console.print(f"  Items Processed: [cyan]{metric.items_processed}[/cyan]")
        console.print(f"  CPU Usage: [cyan]{metric.cpu_percent:.1f}%[/cyan]")
        
        # Additional context from operation
        if hasattr(operation_context, 'kwargs'):
            kwargs = operation_context.kwargs
            if 'embedding_time' in kwargs:
                console.print(f"  Embedding Time: [cyan]{kwargs['embedding_time']:.3f}s[/cyan]")
            if 'vector_search_time' in kwargs:
                console.print(f"  Vector Search Time: [cyan]{kwargs['vector_search_time']:.3f}s[/cyan]")
        
        # Performance rating
        if metric.duration < 0.5:
            rating = "[green]Excellent[/green]"
        elif metric.duration < 2.0:
            rating = "[yellow]Good[/yellow]"
        else:
            rating = "[red]Slow[/red]"
        console.print(f"  Performance: {rating}")
        
    except Exception as e:
        console.print(f"[red]Error showing metrics: {e}[/red]")


@click.command()
@click.argument("query", required=True)
@click.option("--path", "-p", default=".", help="Path to search in")
@click.option("--file-pattern", "-f", default="*", help="File filter pattern (e.g., '*.py')")
@click.option("--max-results", "-m", default=100, help="Maximum number of results to display")
@click.option("--context", "-c", default=1, help="Number of context lines before and after the match")
@click.option("--regex/--no-regex", default=False, help="Use regular expressions for search")
@click.option("--case-sensitive/--ignore-case", default=False, help="Case-sensitive search")
@click.option("--ignore-gitignore/--use-gitignore", default=False, help="Ignore .gitignore rules")
@click.option("--semantic/--literal", default=False, help="Use semantic search instead of literal text matching")
@click.option("--semantic-results", "-sr", default=3, help="Number of semantic search results to display")
@click.option("--rebuild-index", is_flag=True, help="Rebuild the search index before searching")
@click.option("--show-metrics", is_flag=True, help="Show performance metrics after search")
@click.option(
    "--format", "-fmt",
    type=click.Choice(["normal", "compact", "links"]),
    default="normal",
    help="Output format of results"
)
def search(query, path, file_pattern, max_results, context, regex, case_sensitive,
           ignore_gitignore, semantic, semantic_results, rebuild_index, show_metrics, format):
    """Search through project files.

    QUERY - a string or regular expression to search for.
    
    Use --semantic flag to perform semantic search that understands the meaning of your query,
    not just literal text matches. Use --semantic-results to control how many semantic results to show.
    """
    # Import metrics collector (delayed to avoid issues)
    try:
        from agentcli.core.performance.collector import metrics_collector
    except ImportError:
        metrics_collector = None
    
    console = Console()

    # Start performance measurement
    operation_context = None
    if metrics_collector:
        operation_type = "cli_semantic_search" if semantic else "cli_text_search"
        operation_context = metrics_collector.start_operation(
            operation_type, 
            query=query,
            semantic=semantic
        ).__enter__()

    try:
        # Normalize path
        if path == ".":
            path = os.getcwd()
        else:
            path = os.path.abspath(path)

        # Use enhanced search that includes filename matching
        with console.status(f"Searching for '{query}' in {path}..."):
            results = enhanced_search(
                query=query,
                path=path,
                semantic=semantic,
                max_results=max_results
            )

        # Update metrics context
        if operation_context:
            operation_context.kwargs['items_processed'] = len(results)

        # Show results with enhanced formatter
        formatted_output = format_enhanced_results(results, query)
        console.print(formatted_output)
        
        # Show metrics if requested
        if show_metrics and operation_context:
            show_search_metrics(console, operation_context)
            
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
        raise
    finally:
        # Complete performance measurement
        if operation_context and metrics_collector:
            operation_context.__exit__(None, None, None)
