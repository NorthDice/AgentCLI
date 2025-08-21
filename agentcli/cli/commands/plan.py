"""Plan command for creating an action plan."""

import json
import os
import sys
import traceback
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from contextlib import contextmanager

from agentcli.core.planner import Planner
from agentcli.core.structure_provider import StructureProvider
from agentcli.core.exceptions import PlanError, ValidationError, LLMServiceError
from agentcli.utils.logging import logger

# Import metrics collector with fallback
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
@click.argument("query", required=True)
@click.option("--output", "-o", help="Path to save the plan (YAML/JSON)")
@click.option("--format", "-f", type=click.Choice(["json", "yaml"]), default="json",
              help="Output format of the plan (default: json)")
@click.option("--structure", is_flag=True, help="Include project structure context for better planning")
def plan(query, output, format, structure):
    """Creates an action plan based on a query.
    
    QUERY - natural language query for creating a plan.
    
    Use --structure flag to include project structure context,
    which helps the AI understand your codebase better and create
    more accurate plans with correct file paths and imports.
    """
    console = Console()
    
    with performance_tracker("cli_create_plan", 
                           query=query[:50] + "..." if len(query) > 50 else query,
                           output_format=format,
                           with_structure=structure) as ctx:
        try:
            logger.info(f"Running 'plan' command with parameters: query='{query}', output='{output}', format='{format}', structure={structure}")
            
            # Display process
            status_text = "Creating plan with project context..." if structure else "Creating plan..."
            with console.status(status_text):
                # Create planner and generate plan
                planner = Planner()
                
                # Add project structure context if requested
                enhanced_query = query
                if structure:
                    structure_provider = StructureProvider()
                    project_context = structure_provider.get_structure_summary()
                    
                    # Get current file content if specific file is mentioned
                    file_context = ""
                    if "файл" in query.lower() or "file" in query.lower():
                        # Extract file path from query
                        import re
                        file_matches = re.findall(r'[\w/.-]+\.py', query)
                        if file_matches:
                            file_path = file_matches[0]
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    current_content = f.read()
                                    file_context = f"\n=== Current content of {file_path} ===\n{current_content}\n"
                            except Exception:
                                pass
                    
                    enhanced_query = f"""Project Context:
                    {project_context}
                    {file_context}
                    User Request: {query}

                    IMPORTANT INSTRUCTIONS:
                    1. Use PATCH actions for precise modifications instead of full file replacement
                    2. Available patch types:
                    - "replace_imports": Replace only the import section at the top of file
                    - "replace_function": Replace a specific function by name
                    - "replace_class": Replace a specific class by name  
                    - "replace_line": Replace specific line(s)
                    - "insert_before/after": Insert content before/after target
                    - "delete_lines": Delete specific lines

                    3. Example patch action for fixing imports:
                    {{
                        "type": "patch",
                        "path": "app/crud.py",
                        "description": "Fix imports in crud.py", 
                        "patches": [
                        {{
                            "type": "replace_imports",
                            "content": "from typing import List, Optional\\nfrom models.todo import Todo\\nfrom models.todo_create import TodoCreate"
                        }}
                        ]
                    }}

                    4. Only use "modify" action for complete file rewrites when absolutely necessary
                    5. Preserve ALL existing code - never replace with placeholders
                    6. Consider the project structure when determining correct import paths

                    Generate actions using patch types for surgical code changes."""
                
                try:
                    result_plan = planner.create_plan(enhanced_query)
                except LLMServiceError as e:
                    logger.error(f"LLM service error: {str(e)}")
                    console.print(f"\n[bold red]✗[/] Error while calling LLM service: {str(e)}")
                    return 1
                
                # Update metrics context
                if ctx:
                    ctx.kwargs.update({
                        'items_processed': len(result_plan.get("actions", [])),
                        'plan_id': result_plan.get("id", "unknown"),
                        'actions_count': len(result_plan.get("actions", []))
                    })
                
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
