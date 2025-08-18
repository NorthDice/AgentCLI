"""Команда apply для выполнения плана действий."""

import json
import os
import yaml
import click
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.prompt import Confirm
from rich.table import Table

from agentcli.core.executor import Executor
from agentcli.core.exceptions import ValidationError
from agentcli.utils.logging import logger


@click.command()
@click.argument("plan_file", type=click.Path(exists=True), required=True)
@click.option("--dry-run", is_flag=True, help="Показать, какие действия будут выполнены, без фактического выполнения")
@click.option("--skip-validation", is_flag=True, help="Пропустить валидацию плана перед выполнением")
@click.option("--yes", "-y", is_flag=True, help="Автоматически подтверждать действия без запроса")
def apply(plan_file, dry_run, skip_validation, yes):
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
    
    # Создаем исполнитель
    executor = Executor()
    
    try:
        # Запускаем валидацию, если не задано --skip-validation
        if not skip_validation and not dry_run:
            with console.status("[bold blue]Валидация плана...[/]"):
                is_valid, issues = executor.validator.validate_plan(plan)
            
            # Если есть проблемы, показываем их
            if issues:
                console.print("\n[bold yellow]Результаты валидации:[/]")
                
                # Создаем таблицу с проблемами
                table = Table(title="Найденные проблемы")
                table.add_column("№", style="dim")
                table.add_column("Действие")
                table.add_column("Тип")
                table.add_column("Сообщение")
                table.add_column("Критичность", style="bold")
                
                for i, issue in enumerate(issues, 1):
                    action_idx = issue.get("action_index", "N/A")
                    issue_type = issue.get("type", "unknown")
                    message = issue.get("message", "Нет описания")
                    criticality = "[bold red]Критическая[/]" if issue.get("critical", False) else "[green]Некритическая[/]"
                    
                    table.add_row(
                        str(i),
                        str(action_idx),
                        issue_type,
                        message,
                        criticality
                    )
                
                console.print(table)
                
                # Если есть критические проблемы, запрашиваем подтверждение
                critical_issues = [issue for issue in issues if issue.get("critical", False)]
                if critical_issues and not yes:
                    if not Confirm.ask("\n[bold red]План содержит критические проблемы. Продолжить выполнение?[/]"):
                        console.print("[yellow]Выполнение плана отменено пользователем[/]")
                        return
        
        # В режиме dry-run только показываем действия
        if dry_run:
            return
        
        # Запрашиваем подтверждение перед выполнением плана
        if not yes:
            action_count = len(plan.get("actions", []))
            if not Confirm.ask(f"\n[bold]Будет выполнено {action_count} действий. Продолжить?[/]"):
                console.print("[yellow]Выполнение плана отменено пользователем[/]")
                return
        
        # Выполняем план
        with console.status("[bold green]Выполнение плана...[/]"):
            result = executor.execute_plan(plan, skip_validation=True)  # Пропускаем повторную валидацию
        
        # Отображаем результат выполнения
        if result["success"]:
            console.print("\n[bold green]✓ План успешно выполнен![/]")
        else:
            console.print("\n[bold red]✗ Выполнение плана завершилось с ошибками[/]")
    
    except ValidationError as e:
        logger.error(f"Ошибка валидации: {str(e)}")
        console.print(f"\n[bold red]✗ Ошибка валидации: {str(e)}[/]")
        return
    
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
