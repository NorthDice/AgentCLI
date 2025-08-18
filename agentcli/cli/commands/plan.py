"""Plan command for creating an action plan."""

import json
import os
import sys
import traceback
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agentcli.core.planner import Planner
from agentcli.core.exceptions import PlanError, ValidationError, LLMServiceError
from agentcli.utils.logging import logger


@click.command()
@click.argument("query", required=True)
@click.option("--output", "-o", help="Path to save the plan (YAML/JSON)")
@click.option("--format", "-f", type=click.Choice(["json", "yaml"]), default="json",
              help="Output format of the plan (default: json)")
def plan(query, output, format):
    """Creates an action plan based on a query.
    
    QUERY - natural language query for creating a plan.
    """
    console = Console()
    
    try:
        logger.info(f"Running 'plan' command with parameters: query='{query}', output='{output}', format='{format}'")
        
        # Display process
        with console.status("Creating plan..."):
            # Create planner and generate plan
            planner = Planner()
            
            try:
                result_plan = planner.create_plan(query)
            except LLMServiceError as e:
                logger.error(f"LLM service error: {str(e)}")
                console.print(f"\n[bold red]✗[/] Error while calling LLM service: {str(e)}")
                return 1
            
            # Save plan to file
            try:
                if output:
                    if not output.lower().endswith(f".{format}"):
                        output = f"{output}.{format}"
                    # Save to specified path
                    output = planner.save_plan(result_plan, output)
                else:
                    # By default save into 'plans' directory
                    os.makedirs("plans", exist_ok=True)
                    output = planner.save_plan(result_plan)
            except Exception as e:
                logger.error(f"Error while saving plan: {str(e)}")
                console.print(f"\n[bold red]✗[/] Error while saving plan: {str(e)}")
                
                # Show traceback in debug mode
                if os.environ.get("AGENTCLI_LOG_LEVEL") == "DEBUG":
                    console.print("\n[bold red]Traceback:[/]")
                    console.print(traceback.format_exc())
                return 1
    
        # Show result
        console.print(f"\n[bold green]✓[/] Plan created and saved to: [bold]{output}[/]")
        
        # Show plan actions
        console.print("\n[bold]Plan actions:[/]")
        for i, action in enumerate(result_plan["actions"], 1):
            action_type = action.get("type", "unknown")
            description = action.get("description", "No description")
            path = action.get("path", "")
            
            # Create panel with action description
            action_panel = Panel(
                f"[bold]Type:[/] {action_type}\n"
                f"[bold]Path:[/] {path}\n"
                f"[bold]Description:[/] {description}",
                title=f"Action #{i}",
                expand=False
            )
            console.print(action_panel)
            
            # Show content with syntax highlighting if present
            if action.get("content"):
                ext = os.path.splitext(path)[1] if path else ".txt"
                syntax = Syntax(
                    action["content"],
                    ext.lstrip(".") if ext else "text",
                    theme="monokai",
                    line_numbers=True
                )
                console.print(syntax)
        
        return 0
    
    except ValidationError as e:
        logger.error(f"Validation error: {str(e)}")
        console.print(f"\n[bold red]✗[/] Validation error: {str(e)}")
        return 1
        
    except PlanError as e:
        logger.error(f"Error while creating plan: {str(e)}")
        console.print(f"\n[bold red]✗[/] Error while creating plan: {str(e)}")
        return 1
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        console.print(f"\n[bold red]✗[/] Unexpected error: {str(e)}")
        
        # Show traceback in debug mode
        if os.environ.get("AGENTCLI_LOG_LEVEL") == "DEBUG":
            console.print("\n[bold red]Traceback:[/]")
            console.print(traceback.format_exc())
        return 1 
