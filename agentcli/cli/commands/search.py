"""Search command for finding text in the project."""

import os
import click
from rich.console import Console
from rich.syntax import Syntax
from rich.text import Text
from rich.markup import escape

from agentcli.core.search import search_files, format_search_results


@click.command()
@click.argument("query", required=True)
@click.option("--path", "-p", default=".", help="Path to search in")
@click.option("--file-pattern", "-f", default="*", help="File filter pattern (e.g., '*.py')")
@click.option("--max-results", "-m", default=100, help="Maximum number of results to display")
@click.option("--context", "-c", default=1, help="Number of context lines before and after the match")
@click.option("--regex/--no-regex", default=False, help="Use regular expressions for search")
@click.option("--case-sensitive/--ignore-case", default=False, help="Case-sensitive search")
@click.option("--ignore-gitignore/--use-gitignore", default=False, help="Ignore .gitignore rules")
@click.option(
    "--format", "-fmt",
    type=click.Choice(["normal", "compact", "links"]),
    default="normal",
    help="Output format of results"
)
def search(query, path, file_pattern, max_results, context, regex, case_sensitive,
           ignore_gitignore, format):
    """Search through project files.

    QUERY - a string or regular expression to search for.
    """
    console = Console()

    # Normalize path
    if path == ".":
        path = os.getcwd()
    else:
        path = os.path.abspath(path)

    # Info message
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

    # Show results
    if not results:
        console.print(f"[yellow]No results found for '[bold]{escape(query)}[/]'.[/]")
        return

    total_matches = sum(len(result["matches"]) for result in results)
    console.print(f"\n[bold green]Found:[/] {total_matches} matches in {len(results)} files")

    # Use preformatted compact/links formats
    if format in ["links", "compact"]:
        formatted_results = format_search_results(results, format, os.getcwd())
        console.print(formatted_results)
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
                return

    console.print(f"\n[green]Displayed {result_count} of {total_matches} matches.[/]")
