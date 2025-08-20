"""Rollback command for reverting changes."""

import os
import json
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from agentcli.core.executor import Executor


@click.command()
@click.option("--steps", default=1, help="Number of steps to roll back")
@click.option("--last-plan", is_flag=True, help="Roll back the last executed plan")
@click.option("--yes", "-y", is_flag=True, help="Confirm rollback without asking")
def rollback(steps, last_plan, yes):
    """Rolls back recent changes.
    
    By default, the last action is rolled back. Use --steps to specify how many steps to roll back,
    or --last-plan to rollback the most recent plan.
    """
    console = Console()
    
    # Handle last plan rollback
    if last_plan:
        return handle_last_plan_rollback(yes, console)
    
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


def handle_last_plan_rollback(yes, console):
    """Handle rollback of the last executed plan.
    
    Args:
        yes (bool): Skip confirmation if True
        console: Rich console for output
    """
    # Find the most recent plan that was executed
    plans_dir = Path("plans")
    if not plans_dir.exists():
        console.print("[red]Error:[/] Plans directory not found")
        return
    
    # Get all plan files sorted by modification time (most recent first)
    plan_files = sorted(
        [f for f in plans_dir.glob("*.json")],
        key=lambda f: f.stat().st_mtime,
        reverse=True
    )
    
    if not plan_files:
        console.print("[red]Error:[/] No plans found")
        return
    
    # Use the most recent plan
    most_recent_plan = plan_files[0]
    
    try:
        # Load the plan
        with open(most_recent_plan, 'r') as f:
            plan = json.load(f)
        
        actions = plan.get('actions', [])
        if not actions:
            console.print(f"[yellow]Warning:[/] Most recent plan has no actions to rollback")
            return
        
        plan_id = plan.get('id', most_recent_plan.stem)
        console.print(f"[bold]Rolling back most recent plan:[/] {plan_id}")
        console.print(f"[bold]Actions to rollback:[/] {len(actions)}")
        
        # Show actions that will be rolled back
        console.print("\n[bold]Actions in plan:[/]")
        for i, action in enumerate(actions, 1):
            console.print(f"  {i}. {action.get('type', 'unknown')} - {action.get('description', 'No description')}")
        
        # Confirm rollback if --yes is not provided
        if not yes:
            console.print(f"\n[yellow]Warning:[/] All {len(actions)} actions from the most recent plan will be rolled back.")
            console.print("[yellow]This action cannot be undone![/]")
            
            confirm = click.confirm("Continue?", default=False)
            if not confirm:
                console.print("Plan rollback canceled.")
                return
        
        # Perform rollback - roll back the number of actions in the plan
        with console.status(f"Rolling back plan {plan_id}..."):
            executor = Executor()
            result = executor.rollback(len(actions))
        
        # Display result
        if result["success"]:
            console.print(f"\n[bold green]✓[/] Successfully rolled back plan '{plan_id}'")
            console.print(f"[green]Rolled back {len(result['actions_rolled_back'])} actions[/]")
            
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
            console.print(f"[bold red]✗[/] Error rolling back plan '{plan_id}'")
            
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
        
        # Show warning if fewer actions were rolled back than expected
        if result["success"] and len(result["actions_rolled_back"]) < len(actions):
            console.print(
                f"\n[yellow]Warning:[/] Rolled back {len(result['actions_rolled_back'])} of {len(actions)} "
                "planned actions. Some actions may have already been rolled back or not found."
            )
    
    except Exception as e:
        console.print(f"[red]Error:[/] Failed to process plan rollback: {str(e)}")
