"""Gen command for code generation."""

import os
import click
from pathlib import Path

from agentcli.core import create_llm_service, LLMServiceError
from agentcli.core.file_ops import write_file
from agentcli.core.logger import Logger
from agentcli.utils.logging import logger


@click.command()
@click.argument("description", required=True)
@click.option("--output", "-o", help="Path to output file")
@click.option("--dry-run", "-d", is_flag=True, help="Preview the generated code without writing to file")
def gen(description, output, dry_run):
    """Generate code based on description.
    
    DESCRIPTION - description of code to generate.
    """
    click.echo(f"Generating code for: {description}")
    
    try:
        llm_service = create_llm_service()
        
        action_logger = Logger()
        
        query = f"Generate code for: {description}. Return only code without surrounding comments."
        
        actions = llm_service.generate_actions(query)
        
        if not actions:
            click.echo("Failed to generate code.", err=True)
            return
        
        code_action = next((a for a in actions if a.get('type') in ['create_file', 'info']), None)
        
        if not code_action:
            click.echo("Failed to extract code from LLM response.", err=True)
            return
        
        code = code_action.get('content', '')
        
        # Always show the generated code
        click.echo("\n--- Generated Code ---\n")
        click.echo(code)
        click.echo("\n-------------------------\n")
        
        # If dry run mode, show message and return
        if dry_run and output:
            click.echo(f"\nDry run mode: Code would be written to {output}")
            return
        elif dry_run:
            click.echo("\nDry run mode: No output file specified")
            return
        
        # Ask for confirmation
        if click.confirm("Does the generated code look good?", default=True):
            if not output:
                # If no output specified, ask for file path
                output = click.prompt("Enter output file path", type=str)
            
            try:
                click.echo(f"Output to file: {output}")
                
                if not os.path.isabs(output):
                    output = os.path.join(os.getcwd(), output)
                    
                directory = os.path.dirname(output)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                
                write_file(output, code)
                
                action_logger.log_action("create", f"Created file: {output}", {"path": output})
                
                click.echo(f"✅ Code successfully generated and saved to file: {output}")
            except Exception as e:
                click.echo(f"❌ Error writing to file: {str(e)}", err=True)
        else:
            click.echo("Code generation cancelled by user.")
    
    except LLMServiceError as e:
        click.echo(f"❌ Error working with LLM service: {str(e)}", err=True)
        logger.error(f"Error generating code: {str(e)}")
