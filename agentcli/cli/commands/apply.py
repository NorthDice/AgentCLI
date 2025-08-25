"""Apply command for executing an action plan."""

import json
import os
import yaml
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.table import Table
from contextlib import contextmanager

from agentcli.core.executor import Executor
from agentcli.core.planner import Planner
from agentcli.core.exceptions import ValidationError
from agentcli.utils.logging import logger

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
@click.argument("plan_file", type=click.Path(exists=True), required=False)
@click.option("--last", is_flag=True, help="Apply the last created plan")
@click.option("--dry-run", is_flag=True, help="Show actions without executing them")
@click.option("--skip-validation", is_flag=True, help="Skip validation before execution")
@click.option("--yes", "-y", is_flag=True, help="Automatically confirm actions without asking")
def apply(plan_file, last, dry_run, skip_validation, yes):
    console = Console()

    with performance_tracker("cli_apply_plan", 
                           plan_file=plan_file or "last", 
                           dry_run=dry_run,
                           skip_validation=skip_validation) as ctx:

        if last:
            if plan_file:
                console.print("[bold yellow]Warning:[/] Both plan file and --last option provided. Using --last.")
            
            planner = Planner()
            plan_file = planner.get_latest_plan_path()
            
            if not plan_file:
                console.print("[bold red]Error:[/] No plans found. Create a plan first with 'agentcli plan'.")
                return
            
            console.print(f"[bold]Using latest plan:[/] {os.path.basename(plan_file)}")
        elif not plan_file:
            console.print("[bold red]Error:[/] Plan file is required unless --last option is used.")
            console.print("Usage: agentcli apply <plan_file> or agentcli apply --last")
            return

        try:
            with open(plan_file, 'r') as f:
                if plan_file.endswith('.yaml') or plan_file.endswith('.yml'):
                    plan = yaml.safe_load(f)
                else:
                    plan = json.load(f)
        except Exception as e:
            console.print(f"[bold red]Error while loading plan:[/] {str(e)}")
            return
        
        console.print(f"[bold]Plan description:[/] {plan.get('query', 'No description')}")
        console.print(f"[bold]Plan ID:[/] {plan.get('id', 'Not specified')}")
        console.print(f"[bold]Number of actions:[/] {len(plan.get('actions', []))}")
        
        if ctx:
            ctx.kwargs.update({
                'items_processed': len(plan.get('actions', [])),
                'plan_id': plan.get('id', 'unknown'),
                'plan_file': os.path.basename(plan_file) if plan_file else 'unknown'
            })
        
        if dry_run:
            console.print("\n[bold yellow]Dry-run mode (--dry-run)[/]")
            console.print("[bold]Actions to be executed:[/]")
            
            for i, action in enumerate(plan.get("actions", []), 1):
                action_type = action.get("type", "unknown")
                description = action.get("description", "No description")
                path = action.get("path", "")
                
                panel = Panel(
                    f"[bold]Type:[/] {action_type}\n"
                    f"[bold]Path:[/] {path}\n"
                    f"[bold]Description:[/] {description}",
                    title=f"Action #{i}",
                    expand=False
                )
                console.print(panel)
                if action.get("content") and path:
                    ext = os.path.splitext(path)[1] if path else ".txt"
                    syntax = Syntax(
                        action["content"],
                        ext.lstrip(".") if ext else "text",
                        theme="monokai",
                        line_numbers=True
                    )
                    console.print(syntax)
            
            return

        executor = Executor()
        
        try:
            if not skip_validation and not dry_run:
                with console.status("[bold blue]Validating plan...[/]"):
                    is_valid, issues = executor.validator.validate_plan(plan)
                
                if issues:
                    console.print("\n[bold yellow]Validation results:[/]")
                    
                    table = Table(title="Found issues")
                    table.add_column("№", style="dim")
                    table.add_column("Action")
                    table.add_column("Type")
                    table.add_column("Message")
                    table.add_column("Severity", style="bold")
                    
                    for i, issue in enumerate(issues, 1):
                        action_idx = issue.get("action_index", "N/A")
                        issue_type = issue.get("type", "unknown")
                        message = issue.get("message", "No description")
                        criticality = "[bold red]Critical[/]" if issue.get("critical", False) else "[green]Non-critical[/]"
                        
                        table.add_row(
                            str(i),
                            str(action_idx),
                            issue_type,
                            message,
                            criticality
                        )
                    
                    console.print(table)
                    
                    critical_issues = [issue for issue in issues if issue.get("critical", False)]
                    if critical_issues and not yes:
                        if not Confirm.ask("\n[bold red]The plan contains critical issues. Continue anyway?[/]"):
                            console.print("[yellow]Execution canceled by user[/]")
                            return
            
            if not yes:
                action_count = len(plan.get("actions", []))
                if not Confirm.ask(f"\n[bold]A total of {action_count} actions will be executed. Continue?[/]"):
                    console.print("[yellow]Execution canceled by user[/]")
                    return
            
            with console.status("[bold green]Executing plan...[/]"):
                result = executor.execute_plan(plan, skip_validation=True)
            
            if ctx:
                ctx.kwargs.update({
                    'executed_actions': len(result.get("executed_actions", [])),
                    'failed_actions': len(result.get("failed_actions", [])),
                    'execution_success': result.get("success", False)
                })
            
            if result["success"]:
                console.print("\n[bold green]✓ Plan executed successfully![/]")
            else:
                console.print("\n[bold red]✗ Plan execution finished with errors[/]")
        
        except ValidationError as e:
            logger.error(f"Validation error: {str(e)}")
            console.print(f"\n[bold red]✗ Validation error: {str(e)}[/]")
            return

        if result["executed_actions"]:
            console.print("\n[bold green]Executed actions:[/]")
            for i, action_result in enumerate(result["executed_actions"], 1):
                action = action_result["action"]
                message = action_result["message"]
                
                console.print(f"{i}. [green]✓[/] {message}")
        
        if result["failed_actions"]:
            console.print("\n[bold red]Failed actions:[/]")
            for i, action_result in enumerate(result["failed_actions"], 1):
                action = action_result["action"]
                message = action_result["message"]
                
                console.print(f"{i}. [red]✗[/] {message}")
