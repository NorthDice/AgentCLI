"""Команда status для отображения статуса."""

import os
import json
import glob
import click
from datetime import datetime
from rich.console import Console
from rich.table import Table


@click.command()
@click.option("--logs", "-l", is_flag=True, help="Показать журнал изменений")
@click.option("--plans", "-p", is_flag=True, help="Показать доступные планы")
def status(logs, plans):
    """Показывает текущий статус и историю изменений."""
    console = Console()
    
    if not logs and not plans:
        # По умолчанию показываем и логи, и планы
        logs = True
        plans = True
    
    if plans:
        _show_plans(console)
    
    if logs:
        _show_logs(console)


def _show_plans(console):
    """Показывает доступные планы."""
    plans_dir = os.path.join(os.getcwd(), "plans")
    
    if not os.path.exists(plans_dir):
        console.print("[yellow]Директория планов не найдена.[/]")
        return
    
    # Ищем все планы
    plan_files = glob.glob(os.path.join(plans_dir, "*.json"))
    
    if not plan_files:
        console.print("[yellow]Планы не найдены.[/]")
        return
    
    # Создаем таблицу планов
    table = Table(title="Доступные планы")
    table.add_column("ID", style="cyan")
    table.add_column("Запрос", style="green")
    table.add_column("Дата создания", style="magenta")
    table.add_column("Действия", justify="right")
    
    for plan_file in sorted(plan_files, key=os.path.getmtime, reverse=True):
        try:
            with open(plan_file, 'r') as f:
                plan = json.load(f)
            
            plan_id = plan.get("id", os.path.basename(plan_file))
            query = plan.get("query", "Не указан")
            timestamp = plan.get("timestamp", "Неизвестно")
            actions_count = len(plan.get("actions", []))
            
            # Преобразуем timestamp если возможно
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            table.add_row(
                str(plan_id)[:8] + "...",
                query[:50] + "..." if len(query) > 50 else query,
                timestamp,
                str(actions_count)
            )
        except Exception as e:
            table.add_row(
                os.path.basename(plan_file),
                f"[red]Ошибка чтения плана: {str(e)}[/]",
                "",
                ""
            )
    
    console.print(table)


def _show_logs(console):
    """Показывает журнал изменений."""
    logs_dir = os.path.join(os.getcwd(), ".agentcli/logs")
    
    if not os.path.exists(logs_dir):
        console.print("[yellow]Журнал изменений пуст.[/]")
        return
    
    # Ищем все логи
    log_files = glob.glob(os.path.join(logs_dir, "*.json"))
    
    if not log_files:
        console.print("[yellow]Журнал изменений пуст.[/]")
        return
    
    # Создаем таблицу логов
    table = Table(title="История изменений")
    table.add_column("ID", style="cyan")
    table.add_column("Действие", style="green")
    table.add_column("Описание", style="blue")
    table.add_column("Дата", style="magenta")
    
    for log_file in sorted(log_files, key=os.path.getmtime, reverse=True):
        try:
            with open(log_file, 'r') as f:
                log = json.load(f)
            
            log_id = log.get("id", os.path.basename(log_file))
            action = log.get("action", "Неизвестно")
            description = log.get("description", "Нет описания")
            timestamp = log.get("timestamp", "Неизвестно")
            
            # Преобразуем timestamp если возможно
            try:
                dt = datetime.fromisoformat(timestamp)
                timestamp = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                pass
            
            table.add_row(
                str(log_id)[:8] + "...",
                action,
                description[:50] + "..." if len(description) > 50 else description,
                timestamp
            )
        except Exception as e:
            table.add_row(
                os.path.basename(log_file),
                "[red]Ошибка[/]",
                f"[red]Ошибка чтения лога: {str(e)}[/]",
                ""
            )
    
    console.print(table)
