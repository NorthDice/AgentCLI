"""Rollback command for reverting changes."""

import os
import json
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from contextlib import contextmanager

from agentcli.core.executor import Executor

try:
    from agentcli.core.performance.collector import metrics_collector
except ImportError:
    metrics_collector = None


@contextmanager
def performance_tracker(operation: str, **kwargs):
    """Context manager for tracking performance metrics."""
    operation_context = None
    
    if metrics_collector:
        operation_context = metrics_collector.start_operation(operation, **kwargs)
        operation_context = operation_context.__enter__()
    
    try:
        yield operation_context
    finally:
        if operation_context and metrics_collector:
            operation_context.__exit__(None, None, None)


@click.command()
@click.option("--steps", default=1, help="Number of steps to roll back")
@click.option("--last-plan", is_flag=True, help="Roll back the last executed plan")
@click.option("--yes", "-y", is_flag=True, help="Confirm rollback without asking")
def rollback(steps, last_plan, yes):

    console = Console()
    
    with performance_tracker("cli_rollback", 
                           steps=steps, 
                           last_plan=last_plan) as ctx:
        
        if last_plan:
            return handle_last_plan_rollback(yes, console)
        
        if steps < 1:
            console.print("[red]Error:[/] Steps must be a positive number")
            return
        
        if not yes:
            console.print(f"[yellow]Warning:[/] The last {steps} actions will be rolled back.")
            console.print("[yellow]This action cannot be undone![/]")
            
            confirm = click.confirm("Continue?", default=False)
            if not confirm:
                console.print("Rollback canceled.")
                return

        with console.status(f"Rolling back the last {steps} actions..."):
            executor = Executor()
            result = executor.rollback(steps)
        
        if ctx:
            ctx.kwargs.update({
                'actions_rolled_back': len(result.get('actions_rolled_back', [])),
                'rollback_success': result.get('success', False)
            })
        
        if result["success"]:
            console.print(f"\n[bold green]✓[/] Successfully rolled back {len(result['actions_rolled_back'])} actions")
            
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
            
            if result["errors"]:
                console.print("[bold red]Errors:[/]")
                for i, error in enumerate(result["errors"], 1):
                    console.print(f"  {i}. {error}")
            else:
                console.print("  No detailed error information available.")
        
        if result.get("errors"):
            console.print("\n[bold red]Rollback errors:[/]")
            for error in result["errors"]:
                console.print(f"  [red]•[/] {error}")

        if result["success"] and len(result["actions_rolled_back"]) < steps:
            console.print(
                f"\n[yellow]Warning:[/] Rolled back {len(result['actions_rolled_back'])} of {steps} "
                "requested actions. There may be no more actions to roll back."
            )


def handle_last_plan_rollback(yes, console):

    with performance_tracker("cli_rollback_plan") as ctx:

        plans_dir = Path("plans")
        if not plans_dir.exists():
            console.print("[red]Error:[/] Plans directory not found")
            return

        plan_files = sorted(
            [f for f in plans_dir.glob("*.json")],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )
        
        if not plan_files:
            console.print("[red]Error:[/] No plans found")
            return
        
        most_recent_plan = plan_files[0]
    
    try:
        with open(most_recent_plan, 'r') as f:
            plan = json.load(f)
        
        actions = plan.get('actions', [])
        if not actions:
            console.print(f"[yellow]Warning:[/] Most recent plan has no actions to rollback")
            return
        
        plan_id = plan.get('id', most_recent_plan.stem)
        console.print(f"[bold]Rolling back most recent plan:[/] {plan_id}")
        console.print(f"[bold]Actions to rollback:[/] {len(actions)}")
        
        try:
            with open(most_recent_plan, 'r') as f:
                plan = json.load(f)
            
            actions = plan.get('actions', [])
            if not actions:
                console.print(f"[yellow]Warning:[/] Most recent plan has no actions to rollback")
                return
            
            plan_id = plan.get('id', most_recent_plan.stem)
            console.print(f"[bold]Rolling back most recent plan:[/] {plan_id}")
            console.print(f"[bold]Actions to rollback:[/] {len(actions)}")

            if ctx:
                ctx.kwargs.update({
                    'plan_id': plan_id,
                    'actions_count': len(actions)
                })
            

            console.print("\n[bold]Actions in plan:[/]")
            for i, action in enumerate(actions, 1):
                console.print(f"  {i}. {action.get('type', 'unknown')} - {action.get('description', 'No description')}")
            
            if not yes:
                console.print(f"\n[yellow]Warning:[/] All {len(actions)} actions from the most recent plan will be rolled back.")
                console.print("[yellow]This action cannot be undone![/]")
                
                confirm = click.confirm("Continue?", default=False)
                if not confirm:
                    console.print("Plan rollback canceled.")
                    return
            
            with console.status(f"Rolling back plan {plan_id}..."):
                executor = Executor()
                result = executor.rollback(len(actions))
            
            if ctx:
                ctx.kwargs.update({
                    'actions_rolled_back': len(result.get('actions_rolled_back', [])),
                    'rollback_success': result.get('success', False)
                })
            

            if result["success"]:
                console.print(f"\n[bold green]✓[/] Successfully rolled back plan '{plan_id}'")
                console.print(f"[green]Rolled back {len(result['actions_rolled_back'])} actions[/]")
                
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
                
                if result["errors"]:
                    console.print("[bold red]Errors:[/]")
                    for i, error in enumerate(result["errors"], 1):
                        console.print(f"  {i}. {error}")
                else:
                    console.print("  No detailed error information available.")
            
            if result.get("errors"):
                console.print("\n[bold red]Rollback errors:[/]")
                for error in result["errors"]:
                    console.print(f"  [red]•[/] {error}")

            if result["success"] and len(result["actions_rolled_back"]) < len(actions):
                console.print(
                    f"\n[yellow]Warning:[/] Rolled back {len(result['actions_rolled_back'])} of {len(actions)} "
                    "planned actions. Some actions may have already been rolled back or not found."
                )
        
        except Exception as e:
            console.print(f"[red]Error:[/] Failed to process plan rollback: {str(e)}")
    
    except Exception as e:
        console.print(f"[red]Error:[/] Failed to process plan rollback: {str(e)}")
