

import click

from agentcli import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    pass


# Импорт команд
from agentcli.cli.commands.plan import plan
from agentcli.cli.commands.apply import apply
from agentcli.cli.commands.rollback import rollback
from agentcli.cli.commands.search import search
from agentcli.cli.commands.explain import explain
from agentcli.cli.commands.gen import gen
from agentcli.cli.commands.status import status

# Регистрация команд
cli.add_command(plan)
cli.add_command(apply)
cli.add_command(rollback)
cli.add_command(search)
cli.add_command(explain)
cli.add_command(gen)
cli.add_command(status)


if __name__ == "__main__":
    cli()
