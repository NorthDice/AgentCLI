"""Delete command for file deletion with rollback support."""

import os
import click
from pathlib import Path

from agentcli.core.file_ops import read_file
from agentcli.core.logger import Logger
from agentcli.utils.logging import logger


@click.command()
@click.argument("file_path", required=True)
@click.option("--reason", "-r", help="Reason for deletion (optional)")
@click.option("--dry-run", "-d", is_flag=True, help="Preview what would be deleted without actually deleting")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def delete(file_path, reason, dry_run, yes):
    action_logger = Logger()
    
    if not os.path.isabs(file_path):
        file_path = os.path.join(os.getcwd(), file_path)
    
    if not os.path.exists(file_path):
        click.echo(f"❌ File not found: {file_path}", err=True)
        return
    click.echo(f"File to delete: {file_path}")
    if reason:
        click.echo(f"Reason: {reason}")
    
    if dry_run:
        click.echo(f"\nDry run mode: File would be deleted: {file_path}")
        return
    if not yes and not click.confirm(f"Are you sure you want to delete '{file_path}'?", default=False):
        click.echo("File deletion cancelled.")
        return
    
    try:

        file_content = read_file(file_path)
        

        os.remove(file_path)
        

        action_logger.log_action("delete", f"Deleted file: {file_path}" + (f" - {reason}" if reason else ""), {
            "path": file_path,
            "content": file_content,  
            "reason": reason or "Manual deletion"
        })
        
        click.echo(f"✅ File successfully deleted: {file_path}")
        click.echo("💡 Use 'rollback' command to restore if needed")
        
    except Exception as e:
        click.echo(f"❌ Error deleting file: {str(e)}", err=True)
        logger.error(f"Error deleting file {file_path}: {str(e)}")
