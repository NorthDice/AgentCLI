"""Gen command for code generation."""

import os
import click
from pathlib import Path
from contextlib import contextmanager

from agentcli.core import get_llm_service, LLMServiceError
from agentcli.core.file_ops import write_file, read_file
from agentcli.core.logger import Logger
from agentcli.utils.logging import logger

try:
    from agentcli.core.performance.collector import metrics_collector
except ImportError:
    metrics_collector = None


@contextmanager
def performance_tracker(operation: str, **kwargs):
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
@click.argument("description", required=True)
@click.option("--output", "-o", help="Path to output file")
@click.option("--dry-run", "-d", is_flag=True, help="Preview the generated code without writing to file")
def gen(description, output, dry_run):

    with performance_tracker("cli_generate_code", 
                           description=description[:50] + "..." if len(description) > 50 else description,
                           output=output or "no_output",
                           dry_run=dry_run) as ctx:
        
        click.echo(f"Generating code for: {description}")
        
        try:
            llm_service = get_llm_service()
            
            action_logger = Logger()
            
            current_content = ""
            if output and os.path.exists(output):
                try:
                    current_content = read_file(output)
                    query = f"""
                    I have an existing file with the following content:
                    
                    ```
                    {current_content}
                    ```
                    
                    Task: {description}
                    
                    Please modify or extend this code to fulfill the task. Return only the complete updated code without any surrounding comments or explanations.
                    """
                except Exception as e:
                    logger.warning(f"Could not read existing file {output}: {e}")
                    query = f"Generate code for: {description}. Return only code without surrounding comments."
            else:
                query = f"Generate code for: {description}. Return only code without surrounding comments."
            
            actions = llm_service.generate_actions(query)
            
            if not actions:
                click.echo("Failed to generate code.", err=True)
                return
            
            code_action = next((a for a in actions if a.get('type') in ['create_file', 'modify', 'info']), None)
            
            if not code_action:
                click.echo("Failed to extract code from LLM response.", err=True)
                return
            
            code = code_action.get('content', '')

            if ctx:
                ctx.kwargs.update({
                    'items_processed': len(actions),
                    'code_length': len(code),
                    'file_exists': bool(current_content),
                    'output_file': output or "none"
                })
            
            click.echo("\n--- Generated Code ---\n")
            click.echo(code)
            click.echo("\n-------------------------\n")

            if dry_run and output:
                click.echo(f"\nDry run mode: Code would be written to {output}")
                return
            elif dry_run:
                click.echo("\nDry run mode: No output file specified")
                return
            
            if click.confirm("Does the generated code look good?", default=True):
                if not output:
                    output = click.prompt("Enter output file path", type=str)
                
                try:
                    click.echo(f"Output to file: {output}")
                    
                    if not os.path.isabs(output):
                        output = os.path.join(os.getcwd(), output)
                        
                    directory = os.path.dirname(output)
                    if directory and not os.path.exists(directory):
                        os.makedirs(directory, exist_ok=True)
                    
                    write_file(output, code)

                    try:
                        from agentcli.core.chroma_indexer import ChromaIndexer
                        indexer = ChromaIndexer(os.getcwd())
                        
                        indexer.queue_file_indexing(output)
                        
                        indexer.start()
                        import time
                        time.sleep(1)  
                        indexer.stop()
                        
                        click.echo("🔄 File indexed successfully!")
                    except Exception as e:
                        logger.warning(f"Failed to queue file for indexing: {e}")
                    
                    if current_content:
                        action_logger.log_action("modify", f"Modified file: {output}", {
                            "path": output,
                            "old_content": current_content,
                            "new_content": code
                        })
                    else:
                        action_logger.log_action("create", f"Created file: {output}", {
                            "path": output,
                            "content": code 
                        })
                    
                    click.echo(f"✅ Code successfully generated and saved to file: {output}")
                except Exception as e:
                    click.echo(f"❌ Error writing to file: {str(e)}", err=True)
            else:
                click.echo("Code generation cancelled by user.")
        
        except LLMServiceError as e:
            click.echo(f"❌ Error working with LLM service: {str(e)}", err=True)
            logger.error(f"Error generating code: {str(e)}")
