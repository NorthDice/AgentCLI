
import os
import click
from dotenv import load_dotenv

from agentcli import __version__
from agentcli.utils.logging import setup_logging
from agentcli.cli.commands.plan import plan
from agentcli.cli.commands.apply import apply
from agentcli.cli.commands.rollback import rollback
from agentcli.cli.commands.search import search
from agentcli.cli.commands.ask import ask
from agentcli.cli.commands.explain import explain
from agentcli.cli.commands.gen import gen
from agentcli.cli.commands.delete import delete
from agentcli.cli.commands.status import status
from agentcli.cli.commands.llm_config import llm_config
from agentcli.cli.commands.index import index, add_commands_to_cli
from agentcli.cli.commands.metrics import metrics

@click.group()
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--log-file', help='Path to log file')
def cli(debug, log_file):
    """AgentCLI - a developer tool for autonomous code operations in Python."""
    load_dotenv()
    
    log_level = "DEBUG" if debug else os.environ.get("AGENTCLI_LOG_LEVEL", "INFO")
    
    if log_file:
        os.environ["AGENTCLI_LOG_FILE"] = log_file
    
    os.environ["AGENTCLI_LOG_LEVEL"] = log_level
    
    setup_logging(log_level=log_level, 
                  log_file=os.environ.get("AGENTCLI_LOG_FILE"))



cli.add_command(plan)
cli.add_command(apply)
cli.add_command(rollback)
cli.add_command(search)
cli.add_command(ask)
cli.add_command(explain)
cli.add_command(gen)
cli.add_command(delete)
cli.add_command(status)
cli.add_command(llm_config)
cli.add_command(index) 
cli.add_command(metrics)

add_commands_to_cli(cli)


if __name__ == "__main__":
    cli()
