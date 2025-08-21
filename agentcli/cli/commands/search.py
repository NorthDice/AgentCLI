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

        # For semantic search
        if semantic:
            with console.status(f"Performing semantic search for '{query}' in {path}..."):
                search_results = perform_semantic_search(
                    query=query, 
                    path=path, 
                    top_k=max_results,
                    rebuild_index=rebuild_index
                )
                
            # Update metrics context
            if operation_context:
                operation_context.kwargs['items_processed'] = len(search_results.get('results', []))
                
            format_semantic_results(search_results, console, context, max_results=semantic_results)
            
            # Show metrics if requested
            if show_metrics and operation_context:
                show_search_metrics(console, operation_context)
            return

        # For regular text search
        search_type = "regular expression" if regex else "string"
        case_info = "case-sensitive" if case_sensitive else "case-insensitive"
        gitignore_info = "" if not ignore_gitignore else " (ignoring .gitignore)"

        with console.status(f"Searching by {search_type} '{query}' {case_info} in {path}{gitignore_info}..."):
            results = search_files(
                query=query,
                path=path,
                file_pattern=file_pattern,
                is_regex=regex,
                use_gitignore=not ignore_gitignore,
                case_sensitive=case_sensitive
            )

        # Update metrics context
        if operation_context:
            operation_context.kwargs['items_processed'] = len(results)

        # Show results
        if not results:
            console.print(f"[yellow]No results found for '[bold]{escape(query)}[/]'.[/]")
            # Show metrics if requested
            if show_metrics and operation_context:
                show_search_metrics(console, operation_context)
            return

        total_matches = sum(len(result["matches"]) for result in results)
        console.print(f"\n[bold green]Found:[/] {total_matches} matches in {len(results)} files")

        # Use preformatted compact/links formats
        if format in ["links", "compact"]:
            formatted_results = format_search_results(results, format, os.getcwd())
            console.print(formatted_results)
            # Show metrics if requested
            if show_metrics and operation_context:
                show_search_metrics(console, operation_context)
            return

        # Rich formatted detailed output
        result_count = 0
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, os.getcwd())

            console.print(f"\n[bold blue]{rel_path}[/]:")

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_lines = f.readlines()
            except Exception:
                console.print("  [red]Error reading file[/]")
                continue

            last_line_shown = -1

            for match in file_result["matches"]:
                line_num = match["line_num"]
                line = match["line"]
                match_index = match["match_index"]
                match_length = match.get("match_length", len(query))

                start_line = max(1, line_num - context)
                end_line = min(len(file_lines), line_num + context)

                if start_line <= last_line_shown:
                    start_line = last_line_shown + 1
                if start_line > end_line:
                    continue

                if context > 0:
                    code_lines = []

                    # Context before
                    for i in range(start_line, line_num):
                        code_lines.append(file_lines[i - 1].rstrip("\n"))

                # Matched line
                code_lines.append(line)

                # Context after
                for i in range(line_num + 1, end_line + 1):
                    code_lines.append(file_lines[i - 1].rstrip("\n"))

                ext = os.path.splitext(file_path)[1] or ".txt"
                language = ext.lstrip(".")

                console.print(f"  [dim]Line {line_num}:[/]")
                syntax = Syntax(
                    "\n".join(code_lines),
                    language,
                    theme="monokai",
                    line_numbers=True,
                    start_line=start_line,
                )
                console.print(syntax)
            else:
                highlight_line = Text()
                highlight_line.append(f"  {line_num}: ")

                if match_index > 0:
                    highlight_line.append(line[:match_index])

                highlight_line.append(
                    line[match_index:match_index + match_length],
                    style="bold reverse"
                )

                if match_index + match_length < len(line):
                    highlight_line.append(line[match_index + match_length:])

                console.print(highlight_line)

            last_line_shown = end_line
            result_count += 1

            if result_count >= max_results:
                console.print(
                    f"\n[yellow]Displayed {result_count} of {total_matches} matches. "
                    "Refine your query for more accurate results.[/]"
                )
                # Show metrics if requested before early return
                if show_metrics and operation_context:
                    show_search_metrics(console, operation_context)
                return

        console.print(f"\n[green]Displayed {result_count} of {total_matches} matches.[/]")
        
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
