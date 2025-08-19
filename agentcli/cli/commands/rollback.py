"""Rollback command for reverting changes."""

import click
from rich.console import Console
from rich.panel import Panel

from agentcli.core.executor import Executor


@click.command()
@click.option("--steps", default=1, help="Number of steps to roll back")
@click.option("--yes", "-y", is_flag=True, help="Confirm rollback without asking")
def rollback(steps, yes):
    """Rolls back recent changes.
    
    By default, the last action is rolled back. Use --steps to specify how many steps to roll back.
    """
    console = Console()
    
    if steps < 1:
        console.print("[red]Error:[/] Steps must be a positive number")
        return
    
    # Confirm rollback if --yes is not provided
    if not yes:
        console.print(f"[yellow]Warning:[/] The last {steps} actions will be rolled back.")
        console.print("[yellow]This action cannot be undone![/]")
        
        confirm = click.confirm("Continue?", default=False)
        if not confirm:
            console.print("Rollback canceled.")
            return
    
    # Perform rollback
    with console.status(f"Rolling back the last {steps} actions..."):
        executor = Executor()
        result = executor.rollback(steps)
    
    # Display result
    if result["success"]:
        console.print(f"\n[bold green]✓[/] Successfully rolled back {len(result['actions_rolled_back'])} actions")
        
        # Display rolled back actions
        for i, action in enumerate(result["actions_rolled_back"], 1):
            panel = Panel(
                f"[bold]Type:[/] {action['type']}\n"
                f"[bold]Path:[/] {action['path']}\n"
                f"[bold]Description:[/] {action['description']}",
                title=f"Rolled back #{i}",
                expand=False
            )
            console.print(panel)
    else:
        console.print("[bold red]✗[/] Error during rollback")
        
        # Display detailed errors
        if result["errors"]:
            console.print("[bold red]Errors:[/]")
            for i, error in enumerate(result["errors"], 1):
                console.print(f"  {i}. {error}")
        else:
            console.print("  No detailed error information available.")
    
    # Display errors if any
    if result.get("errors"):
        console.print("\n[bold red]Rollback errors:[/]")
        for error in result["errors"]:
            console.print(f"  [red]•[/] {error}")
    
    # Show warning if fewer actions were rolled back than requested
    if result["success"] and len(result["actions_rolled_back"]) < steps:
        console.print(
            f"\n[yellow]Warning:[/] Rolled back {len(result['actions_rolled_back'])} of {steps} "
            "requested actions. There may be no more actions to roll back."
        )
