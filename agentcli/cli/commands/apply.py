"""Команда apply для выполнения плана действий."""

import json
import os
import yaml
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from agentcli.core.executor import Executor


@click.command()
@click.argument("plan_file", type=click.Path(exists=True), required=True)
@click.option("--dry-run", is_flag=True, help="Показать, какие действия будут выполнены, без фактического выполнения")
def apply(plan_file, dry_run):
    """Выполняет план действий из файла.
    
    PLAN_FILE - путь к файлу плана (JSON/YAML).
    """
    console = Console()
    
    # Загружаем план из файла
    try:
        with open(plan_file, 'r') as f:
            if plan_file.endswith('.yaml') or plan_file.endswith('.yml'):
                plan = yaml.safe_load(f)
            else:
                plan = json.load(f)
    except Exception as e:
        console.print(f"[bold red]Ошибка при загрузке плана:[/] {str(e)}")
        return
    
    # Отображаем информацию о плане
    console.print(f"[bold]План действий:[/] {plan.get('query', 'Без описания')}")
    console.print(f"[bold]ID плана:[/] {plan.get('id', 'Не указан')}")
    console.print(f"[bold]Количество действий:[/] {len(plan.get('actions', []))}")
    
    # В режиме dry-run только показываем действия
    if dry_run:
        console.print("\n[bold yellow]Режим предварительного просмотра (--dry-run)[/]")
        console.print("[bold]Действия, которые будут выполнены:[/]")
        
        for i, action in enumerate(plan.get("actions", []), 1):
            action_type = action.get("type", "unknown")
            description = action.get("description", "Нет описания")
            path = action.get("path", "")
            
            panel = Panel(
                f"[bold]Тип:[/] {action_type}\n"
                f"[bold]Путь:[/] {path}\n"
                f"[bold]Описание:[/] {description}",
                title=f"Действие #{i}",
                expand=False
            )
            console.print(panel)
            
            # Если есть содержимое, отображаем его с подсветкой синтаксиса
            if action.get("content") and path:
                ext = os.path.splitext(path)[1] if path else ".txt"
                syntax = Syntax(
                    action["content"],
                    ext.lstrip(".") if ext else "text",
                    theme="monokai",
                    line_numbers=True
                )
                console.print(syntax)
        
        return
    
    # Выполняем план
    with console.status("[bold green]Выполнение плана...[/]"):
        executor = Executor()
        result = executor.execute_plan(plan)
    
    # Отображаем результат выполнения
    if result["success"]:
        console.print("\n[bold green]✓ План успешно выполнен![/]")
    else:
        console.print("\n[bold red]✗ Выполнение плана завершилось с ошибками[/]")
    
    # Отображаем выполненные действия
    if result["executed_actions"]:
        console.print("\n[bold green]Выполненные действия:[/]")
        for i, action_result in enumerate(result["executed_actions"], 1):
            action = action_result["action"]
            message = action_result["message"]
            
            console.print(f"{i}. [green]✓[/] {message}")
    
    # Отображаем действия с ошибками
    if result["failed_actions"]:
        console.print("\n[bold red]Действия с ошибками:[/]")
        for i, action_result in enumerate(result["failed_actions"], 1):
            action = action_result["action"]
            message = action_result["message"]
            
            console.print(f"{i}. [red]✗[/] {message}")
