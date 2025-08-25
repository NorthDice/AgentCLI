"""Status command to display current state."""

import os
import json
import glob
import click
from datetime import datetime
from rich.console import Console
from rich.table import Table


@click.command()
@click.option("--logs", "-l", is_flag=True, help="Show the change log")
@click.option("--plans", "-p", is_flag=True, help="Show available plans")
def status(logs, plans):
    """Displays the current status and change history."""
    console = Console()
    
    if not logs and not plans:
        logs = True
        plans = True
    
    if plans:
        _show_plans(console)
    
    if logs:
        _show_logs(console)


def _show_plans(console):
    """Shows available plans."""
    plans_dir = os.path.join(os.getcwd(), "plans")
    
    if not os.path.exists(plans_dir):
        console.print("[yellow]Plans directory not found.[/]")
        return

    plan_files = glob.glob(os.path.join(plans_dir, "*.json"))
    
    if not plan_files:
        console.print("[yellow]No plans found.[/]")
        return
    
    table = Table(title="Available Plans")
    table.add_column("ID", style="cyan")
    table.add_column("Query", style="green")
    table.add_column("Created At", style="magenta")
    table.add_column("Actions", justify="right")
    
    for plan_file in sorted(plan_files, key=os.path.getmtime, reverse=True):
        try:
            with open(plan_file, 'r') as f:
                plan = json.load(f)
            
            plan_id = plan.get("id", os.path.basename(plan_file))
            query = plan.get("query", "Not specified")
            timestamp = plan.get("timestamp", "Unknown")
            actions_count = len(plan.get("actions", []))
            
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            table.add_row(
                str(plan_id)[:8] + "...",
                query[:50] + "..." if len(query) > 50 else query,
                timestamp,
                str(actions_count)
            )
        except Exception as e:
            table.add_row(
                os.path.basename(plan_file),
                f"[red]Error reading plan: {str(e)}[/]",
                "",
                ""
            )
    
    console.print(table)


def _show_logs(console):
    """Shows the change log."""
    logs_dir = os.path.join(os.getcwd(), ".agentcli/logs")
    
    if not os.path.exists(logs_dir):
        console.print("[yellow]Change log is empty.[/]")
        return
    
    log_files = glob.glob(os.path.join(logs_dir, "*.json"))
    
    if not log_files:
        console.print("[yellow]Change log is empty.[/]")
        return

    table = Table(title="Change History")
    table.add_column("ID", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Description", style="blue")
    table.add_column("Date", style="magenta")
    
    for log_file in sorted(log_files, key=os.path.getmtime, reverse=True):
        try:
            with open(log_file, 'r') as f:
                log = json.load(f)
            
            log_id = log.get("id", os.path.basename(log_file))
            action = log.get("action", "Unknown")
            description = log.get("description", "No description")
            timestamp = log.get("timestamp", "Unknown")
            
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            table.add_row(
                str(log_id)[:8] + "...",
                action,
                description[:50] + "..." if len(description) > 50 else description,
                timestamp
            )
        except Exception as e:
            table.add_row(
                os.path.basename(log_file),
                "[red]Error[/]",
                f"[red]Error reading log: {str(e)}[/]",
                ""
            )
    
    console.print(table)
