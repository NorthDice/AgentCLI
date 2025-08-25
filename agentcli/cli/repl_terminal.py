import os
import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
import click_repl

from agentcli.cli.main import cli
from agentcli.core.background_indexer import BackgroundIndexer

console = Console()

background_indexer = BackgroundIndexer(os.getcwd())
background_indexer.start()

@cli.command()
def clear():
    """Clear the terminal screen."""
    import os
    os.system('clear')

@cli.command()
def repl_shell():
    """Start AgentCLI REPL shell."""
    console.print(
        Panel(
            Text(
                "🚀 AgentCLI REPL Terminal Started\n"
                "Type 'help' for commands, 'status' for indexer status, 'cache' for cache info."
            ),
            title="AgentCLI REPL",
            border_style="magenta",
        )
    )
    click_repl.repl(click.get_current_context(), prompt_kwargs={"completer": None})


@cli.command()
def status():
    """Show background indexer status."""
    status = background_indexer.get_status()
    console.print(Panel(str(status), title="Indexer Status", border_style="blue"))


@cli.command()
def cache():
    """Show cache info."""
    cache_stats = background_indexer.cache_manager.get_cache_stats()
    console.print(Panel(str(cache_stats), title="Cache Info", border_style="green"))


if __name__ == "__main__":
    cli()
