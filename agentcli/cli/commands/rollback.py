"""Команда rollback для отката изменений."""

import click
from rich.console import Console
from rich.panel import Panel

from agentcli.core.executor import Executor


@click.command()
@click.option("--steps", default=1, help="Количество шагов для отката")
@click.option("--yes", "-y", is_flag=True, help="Подтверждение отката без запроса")
def rollback(steps, yes):
    """Откатывает последние изменения.
    
    По умолчанию откатывается последнее действие. Используйте --steps, чтобы указать количество шагов для отката.
    """
    console = Console()
    
    if steps < 1:
        console.print("[red]Ошибка:[/] Количество шагов должно быть положительным числом")
        return
    
    # Подтверждение отката, если не указан флаг --yes
    if not yes:
        console.print(f"[yellow]Внимание:[/] Будут откачены последние {steps} действий.")
        console.print("[yellow]Это действие нельзя отменить![/]")
        
        confirm = click.confirm("Продолжить?", default=False)
        if not confirm:
            console.print("Отмена отката.")
            return
    
    # Выполнение отката
    with console.status(f"Откат последних {steps} действий..."):
        executor = Executor()
        result = executor.rollback(steps)
    
    # Отображение результата
    if result["success"]:
        console.print(f"\n[bold green]✓[/] Успешно откачено {len(result['actions_rolled_back'])} действий")
        
        # Отображаем откаченные действия
        for i, action in enumerate(result["actions_rolled_back"], 1):
            panel = Panel(
                f"[bold]Тип:[/] {action['type']}\n"
                f"[bold]Путь:[/] {action['path']}\n"
                f"[bold]Описание:[/] {action['description']}",
                title=f"Откачено #{i}",
                expand=False
            )
            console.print(panel)
    else:
        console.print("[bold red]✗[/] Ошибка при откате изменений")
    
    # Отображаем ошибки, если они есть
    if result.get("errors"):
        console.print("\n[bold red]Ошибки при откате:[/]")
        for error in result["errors"]:
            console.print(f"  [red]•[/] {error}")
    
    # Отображаем предупреждение, если откачено меньше действий, чем запрошено
    if result["success"] and len(result["actions_rolled_back"]) < steps:
        console.print(
            f"\n[yellow]Предупреждение:[/] Откачено {len(result['actions_rolled_back'])} из {steps} "
            "запрошенных действий. Возможно, нет больше действий для отката."
        )
