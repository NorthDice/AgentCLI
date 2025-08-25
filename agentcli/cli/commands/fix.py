"""
Fix command for running intelligent refactoring via FixManager.
"""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from agentcli.core.fixmanager.fix_manager import FixManager
from agentcli.core import get_llm_service
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
    
    console.print(Panel(f"[bold cyan]Task:[/] {description}\n[bold]Target files:[/]\n" + '\n'.join(str(p) for p in target_paths), title="Fix Command"))
    
    result = fix_manager.fix_with_context(description, target_paths)
    plan = result['plan']
    validation = result['validation']
    
    console.print(Panel(display_plan_safely(result['plan']), title="🔧 Refactoring Plan"))
    if validation['is_valid']:
        console.print("[green]Plan is valid. You can apply the changes.[/]")
        def confirm_change(msg):
            if yes:
                return True
            return click.confirm(msg, default=True)
        apply_result = fix_manager.apply_fix_plan(result, confirm_callback=confirm_change)
        if apply_result['success']:
            console.print(f"[bold green]✓[/] Refactoring applied successfully! Files changed: {len(apply_result['applied_changes'])}")
            if apply_result['import_fixes']:
                console.print(f"[yellow]Imports fixed: {len(apply_result['import_fixes'])}")
            console.print("\n[bold]Applied Changes:[/]")
            for i, change in enumerate(apply_result['applied_changes'], 1):
                result = change.get('result', {})
                path = result.get('path', '')
                status = change.get('status', '')
                description = change.get('description', '')
                content = result.get('content', '')
                action_panel = Panel(
                    f"[bold]Type:[/] {change.get('type', 'unknown')}\n"
                    f"[bold]Path:[/] {path}\n"
                    f"[bold]Status:[/] {status}\n"
                    f"[bold]Description:[/] {description}",
                    title=f"Change #{i}",
                    expand=False
                )
                console.print(action_panel)
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
            console.print("[bold red]✗[/] Error applying refactoring:")
            for error in apply_result['errors']:
                console.print(f"  - {error}")
    else:
        console.print("[bold red]✗[/] Plan did not pass validation:")
        for error in validation['errors']:
            console.print(f"  - {error}")
            
            
def display_plan_safely(plan):
    """Safe display of the plan with structure check"""
    plan_text = []
    
    if 'description' in plan:
        plan_text.append(f"[bold]Description:[/] {plan['description']}")
    
    if 'changes' in plan and plan['changes']:
        plan_text.append("\n[bold]Changes:[/]")
        for i, change in enumerate(plan['changes'], 1):
            plan_text.append(f"  {i}. {change}")
    else:
        plan_text.append("\n[yellow]⚠️ The plan does not contain specific changes[/]")
    
    if 'warnings' in plan and plan['warnings']:
        plan_text.append("\n[bold red]Warnings:[/]")
        for warning in plan['warnings']:
            plan_text.append(f"  ⚠️ {warning}")
    
    if 'estimated_impact' in plan:
        plan_text.append(f"\n[bold]Estimated impact:[/] {plan['estimated_impact']}")
    
    return '\n'.join(plan_text)