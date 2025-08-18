"""Команда gen для генерации кода."""

import os
import click
from pathlib import Path

from agentcli.core import create_llm_service, LLMServiceError
from agentcli.core.file_ops import write_file
from agentcli.core.logger import Logger
from agentcli.utils.logging import logger


@click.command()
@click.argument("description", required=True)
@click.option("--output", "-o", help="Путь к выходному файлу")
def gen(description, output):
    """Генерирует код на основе описания.
    
    DESCRIPTION - описание кода для генерации.
    """
    click.echo(f"Генерация кода по описанию: {description}")
    
    # Создаем LLM сервис
    try:
        # Инициализируем LLM сервис
        llm_service = create_llm_service()
        
        # Инициализируем логгер для регистрации действий (для возможности отката)
        action_logger = Logger()
        
        # Формируем запрос для генерации кода
        query = f"Сгенерируй код для: {description}. Верни только код без комментариев вокруг."
        
        # Получаем результат от LLM
        actions = llm_service.generate_actions(query)
        
        if not actions:
            click.echo("Не удалось сгенерировать код.", err=True)
            return
        
        # Ищем действие с кодом (create_file или info)
        code_action = next((a for a in actions if a.get('type') in ['create_file', 'info']), None)
        
        if not code_action:
            click.echo("Не удалось получить код из ответа LLM.", err=True)
            return
        
        code = code_action.get('content', '')
        
        if output:
            # Записываем результат в файл
            try:
                click.echo(f"Вывод в файл: {output}")
                # Если путь не абсолютный, делаем его абсолютным
                if not os.path.isabs(output):
                    output = os.path.join(os.getcwd(), output)
                    
                # Создаем директории, если они не существуют
                directory = os.path.dirname(output)
                if directory and not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    
                # Записываем файл
                write_file(output, code)
                
                # Регистрируем действие в логгере (для возможности отката)
                action_logger.log_action("create", f"Создан файл: {output}", {"path": output})
                
                click.echo(f"✅ Код успешно сгенерирован и сохранен в файл: {output}")
            except Exception as e:
                click.echo(f"❌ Ошибка при записи файла: {str(e)}", err=True)
        else:
            # Выводим результат в консоль
            click.echo("\n--- Сгенерированный код ---\n")
            click.echo(code)
            click.echo("\n-------------------------\n")
    
    except LLMServiceError as e:
        click.echo(f"❌ Ошибка при работе с LLM сервисом: {str(e)}", err=True)
        logger.error(f"Ошибка при генерации кода: {str(e)}")
