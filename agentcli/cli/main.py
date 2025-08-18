
import os
import click
from dotenv import load_dotenv

from agentcli import __version__
from agentcli.utils.logging import setup_logging
from agentcli.cli.commands.plan import plan
from agentcli.cli.commands.apply import apply
from agentcli.cli.commands.rollback import rollback
from agentcli.cli.commands.search import search
from agentcli.cli.commands.explain import explain
from agentcli.cli.commands.gen import gen
from agentcli.cli.commands.status import status
from agentcli.cli.commands.llm_config import llm_config

@click.group()
@click.version_option(version=__version__)
@click.option('--debug', is_flag=True, help='Включить режим отладки')
@click.option('--log-file', help='Путь к файлу логов')
@click.option('--llm', type=click.Choice(['openai', 'azure']), help='Сервис LLM для использования')
def cli(debug, log_file, llm):
    """AgentCLI - инструмент разработчика для автономной работы с кодом на Python."""
    # Загружаем конфигурацию из .env файла
    load_dotenv()
    
    # Устанавливаем уровень логирования
    log_level = "DEBUG" if debug else os.environ.get("AGENTCLI_LOG_LEVEL", "INFO")
    
    # Если указан файл логов, перенаправляем логи в него
    if log_file:
        os.environ["AGENTCLI_LOG_FILE"] = log_file
    
    # Устанавливаем уровень логирования через переменную окружения
    os.environ["AGENTCLI_LOG_LEVEL"] = log_level
    
    # Если указан LLM сервис, перезаписываем переменную окружения
    if llm:
        os.environ["LLM_SERVICE"] = llm
    
    # Перенастраиваем логгер
    setup_logging(log_level=log_level, 
                  log_file=os.environ.get("AGENTCLI_LOG_FILE"))




# Регистрация команд
cli.add_command(plan)
cli.add_command(apply)
cli.add_command(rollback)
cli.add_command(search)
cli.add_command(explain)
cli.add_command(gen)
cli.add_command(status)
cli.add_command(llm_config)


if __name__ == "__main__":
    cli()
