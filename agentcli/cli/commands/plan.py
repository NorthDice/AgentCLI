"""Команда plan для создания плана действий."""

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
@click.option("--output", "-o", help="Путь для сохранения плана (YAML/JSON)")
@click.option("--format", "-f", type=click.Choice(["json", "yaml"]), default="json",
              help="Формат вывода плана (по умолчанию: json)")
def plan(query, output, format):
    """Создает план действий на основе запроса.
    
    QUERY - запрос на естественном языке для создания плана.
    """
    console = Console()
    
    try:
        logger.info(f"Запуск команды plan с параметрами: query='{query}', output='{output}', format='{format}'")
        
        # Отображаем процесс
        with console.status("Создание плана..."):
            # Создаем планировщик и генерируем план
            planner = Planner()
            
            try:
                result_plan = planner.create_plan(query)
            except LLMServiceError as e:
                logger.error(f"Ошибка LLM сервиса: {str(e)}")
                console.print(f"\n[bold red]✗[/] Ошибка при обращении к LLM сервису: {str(e)}")
                return 1
            
            # Сохраняем план в файл
            try:
                if output:
                    if not output.lower().endswith(f".{format}"):
                        output = f"{output}.{format}"
                    # Если путь указан явно, используем его
                    output = planner.save_plan(result_plan, output)
                else:
                    # По умолчанию сохраняем в директорию plans
                    os.makedirs("plans", exist_ok=True)
                    output = planner.save_plan(result_plan)
            except Exception as e:
                logger.error(f"Ошибка при сохранении плана: {str(e)}")
                console.print(f"\n[bold red]✗[/] Ошибка при сохранении плана: {str(e)}")
                
                # В режиме отладки показываем стектрейс
                if os.environ.get("AGENTCLI_LOG_LEVEL") == "DEBUG":
                    console.print("\n[bold red]Стектрейс:[/]")
                    console.print(traceback.format_exc())
                return 1
    
        # Отображаем результат
        console.print(f"\n[bold green]✓[/] План создан и сохранен в: [bold]{output}[/]")
        
        # Отображаем действия плана
        console.print("\n[bold]Действия плана:[/]")
        for i, action in enumerate(result_plan["actions"], 1):
            action_type = action.get("type", "unknown")
            description = action.get("description", "Нет описания")
            path = action.get("path", "")
            
            # Создаем панель с описанием действия
            action_panel = Panel(
                f"[bold]Тип:[/] {action_type}\n"
                f"[bold]Путь:[/] {path}\n"
                f"[bold]Описание:[/] {description}",
                title=f"Действие #{i}",
                expand=False
            )
            console.print(action_panel)
            
            # Если есть содержимое, отображаем его с подсветкой синтаксиса
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
        logger.error(f"Ошибка валидации: {str(e)}")
        console.print(f"\n[bold red]✗[/] Ошибка валидации: {str(e)}")
        return 1
        
    except PlanError as e:
        logger.error(f"Ошибка при создании плана: {str(e)}")
        console.print(f"\n[bold red]✗[/] Ошибка при создании плана: {str(e)}")
        return 1
        
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {str(e)}")
        console.print(f"\n[bold red]✗[/] Произошла ошибка: {str(e)}")
        
        # В режиме отладки показываем стектрейс
        if os.environ.get("AGENTCLI_LOG_LEVEL") == "DEBUG":
            console.print("\n[bold red]Стектрейс:[/]")
            console.print(traceback.format_exc())
        return 1
