"""
Команда fix для запуска интеллектуального рефакторинга через FixManager.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from agentcli.core.fix_manager import FixManager
from agentcli.core import get_llm_service
from agentcli.utils.logging import logger as app_logger
from rich.syntax import Syntax
import os

@click.command()
@click.argument('description', required=True)
@click.argument('targets', nargs=-1, required=True)
@click.option('--yes', '-y', is_flag=True, help='Подтвердить все изменения автоматически')
def fix(description, targets, yes):
    """Выполнить интеллектуальный рефакторинг с анализом зависимостей и автоматическим исправлением импортов.
    
    DESCRIPTION — описание задачи рефакторинга
    TARGETS — файлы или директории для рефакторинга
    """
    console = Console()
    root_path = Path.cwd()
    llm_service = get_llm_service()
    fix_manager = FixManager(root_path, llm_service)
    target_paths = [root_path / Path(t) for t in targets]
    
    console.print(Panel(f"[bold cyan]Задача:[/] {description}\n[bold]Целевые файлы:[/]\n" + '\n'.join(str(p) for p in target_paths), title="Fix Command"))
    
    # 1. Анализ и создание плана
    result = fix_manager.fix_with_context(description, target_paths)
    plan = result['plan']
    validation = result['validation']
    
    console.print(Panel(display_plan_safely(result['plan']), title="🔧 План рефакторинга"))
    if validation['is_valid']:
        console.print("[green]План валиден. Можно применять изменения.[/]")
        def confirm_change(msg):
            if yes:
                return True
            return click.confirm(msg, default=True)
        apply_result = fix_manager.apply_fix_plan(result, confirm_callback=confirm_change)
        if apply_result['success']:
            console.print(f"[bold green]✓[/] Рефакторинг успешно применен! Изменено файлов: {len(apply_result['applied_changes'])}")
            if apply_result['import_fixes']:
                console.print(f"[yellow]Исправлено импортов: {len(apply_result['import_fixes'])}")
            # Beautiful output for applied changes
            console.print("\n[bold]Applied Changes:[/]")
            for i, change in enumerate(apply_result['applied_changes'], 1):
                result = change.get('result', {})
                path = result.get('path', '')
                status = change.get('status', '')
                description = change.get('description', '')
                content = result.get('content', '')
                panel = Panel(
                    f"[bold]Path:[/] {path}\n"
                    f"[bold]Status:[/] {status}\n"
                    f"[bold]Description:[/] {description}",
                    title=f"Change #{i}",
                    expand=False
                )
                console.print(panel)
                if content:
                    ext = os.path.splitext(path)[1] if path else ".txt"
                    syntax = Syntax(
                        content,
                        ext.lstrip(".") if ext else "text",
                        theme="monokai",
                        line_numbers=True
                    )
                    console.print(syntax)
        else:
            console.print("[bold red]✗[/] Ошибка при применении рефакторинга:")
            for error in apply_result['errors']:
                console.print(f"  - {error}")
    else:
        console.print("[bold red]✗[/] План не прошел валидацию:")
        for error in validation['errors']:
            console.print(f"  - {error}")
            
            
def display_plan_safely(plan):
    """Безопасное отображение плана с проверкой структуры"""
    plan_text = []
    
    if 'description' in plan:
        plan_text.append(f"[bold]Описание:[/] {plan['description']}")
    
    if 'changes' in plan and plan['changes']:
        plan_text.append("\n[bold]Изменения:[/]")
        for i, change in enumerate(plan['changes'], 1):
            plan_text.append(f"  {i}. {change}")
    else:
        plan_text.append("\n[yellow]⚠️ План не содержит конкретных изменений[/]")
    
    if 'warnings' in plan and plan['warnings']:
        plan_text.append("\n[bold red]Предупреждения:[/]")
        for warning in plan['warnings']:
            plan_text.append(f"  ⚠️ {warning}")
    
    if 'estimated_impact' in plan:
        plan_text.append(f"\n[bold]Ожидаемое воздействие:[/] {plan['estimated_impact']}")
    
    return '\n'.join(plan_text)