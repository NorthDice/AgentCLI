"""Команда search для поиска в проекте."""

import os
import click
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.text import Text
from rich.markup import escape

from agentcli.core.search import search_files, format_search_results


@click.command()
@click.argument("query", required=True)
@click.option("--path", "-p", default=".", help="Путь для поиска")
@click.option("--file-pattern", "-f", default="*", help="Шаблон для фильтрации файлов (например, '*.py')")
@click.option("--max-results", "-m", default=100, help="Максимальное количество результатов")
@click.option("--context", "-c", default=1, help="Количество строк контекста до и после совпадения")
@click.option("--regex/--no-regex", default=False, help="Использовать регулярные выражения для поиска")
@click.option("--case-sensitive/--ignore-case", default=False, help="Учитывать регистр при поиске")
@click.option("--ignore-gitignore/--use-gitignore", default=False, help="Игнорировать правила .gitignore")
@click.option("--format", "-fmt", type=click.Choice(['normal', 'compact', 'links']), default='normal', 
              help="Формат вывода результатов")
def search(query, path, file_pattern, max_results, context, regex, case_sensitive, 
           ignore_gitignore, format):
    """Выполняет поиск по файлам проекта.
    
    QUERY - строка или регулярное выражение для поиска.
    """
    console = Console()
    
    # Нормализуем путь
    if path == ".":
        path = os.getcwd()
    else:
        path = os.path.abspath(path)
    
    # Определяем что искать
    search_type = "регулярному выражению" if regex else "строке"
    case_info = "с учетом регистра" if case_sensitive else "без учета регистра"
    gitignore_info = "" if not ignore_gitignore else " (игнорируя .gitignore)"
    
    with console.status(f"Поиск по {search_type} '{query}' {case_info} в {path}{gitignore_info}..."):
        # Выполняем поиск с новыми параметрами
        results = search_files(
            query=query,
            path=path,
            file_pattern=file_pattern,
            is_regex=regex,
            use_gitignore=not ignore_gitignore,
            case_sensitive=case_sensitive
        )
    
    # Отображаем результаты
    if not results:
        console.print(f"[yellow]По запросу '[bold]{escape(query)}[/]' ничего не найдено.[/]")
        return
    
    total_matches = sum(len(result["matches"]) for result in results)
    console.print(f"\n[bold green]Найдено:[/] {total_matches} совпадений в {len(results)} файлах")
    
    # Если выбран формат links или compact, используем форматирование из search.py
    if format in ['links', 'compact']:
        formatted_results = format_search_results(results, format, os.getcwd())
        console.print(formatted_results)
        return
    
    # Иначе используем rich форматирование для более красивого вывода
    result_count = 0
    for file_result in results:
        file_path = file_result["file"]
        rel_path = os.path.relpath(file_path, os.getcwd())
        
        console.print(f"\n[bold blue]{rel_path}[/]:")
        
        # Читаем весь файл для контекста
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_lines = f.readlines()
        except Exception:
            console.print(f"  [red]Ошибка чтения файла[/]")
            continue
        
        # Отображаем каждое совпадение с контекстом
        last_line_shown = -1
        
        for match in file_result["matches"]:
            line_num = match["line_num"]
            line = match["line"]
            match_index = match["match_index"]
            match_length = match.get("match_length", len(query))
            
            # Определяем строки для контекста
            start_line = max(1, line_num - context)
            end_line = min(len(file_lines), line_num + context)
            
            # Пропускаем, если этот диапазон уже показан
            if start_line <= last_line_shown:
                start_line = last_line_shown + 1
            
            if start_line > end_line:
                continue
            
            # Текст с подсветкой совпадения уже готов
            
            # Отображаем контекст и строку с совпадением
            if context > 0:
                code_lines = []
                
                # Добавляем строки до совпадения
                for i in range(start_line, line_num):
                    code_lines.append(file_lines[i - 1].rstrip('\n'))
                
                # Добавляем строку с совпадением
                code_lines.append(line)
                
                # Добавляем строки после совпадения
                for i in range(line_num + 1, end_line + 1):
                    code_lines.append(file_lines[i - 1].rstrip('\n'))
                
                # Получаем расширение файла для подсветки синтаксиса
                ext = os.path.splitext(file_path)[1] if os.path.splitext(file_path)[1] else ".txt"
                language = ext.lstrip(".")
                
                # Отображаем код с подсветкой синтаксиса
                console.print(f"  [dim]Строка {line_num}:[/]")
                syntax = Syntax(
                    "\n".join(code_lines),
                    language,
                    theme="monokai",
                    line_numbers=True,
                    start_line=start_line
                )
                console.print(syntax)
            else:
                # Простой вывод без контекста
                highlight_line = Text()
                highlight_line.append(f"  {line_num}: ")
                
                # Добавляем текст до совпадения
                if match_index > 0:
                    highlight_line.append(line[:match_index])
                
                # Добавляем совпадение с подсветкой
                highlight_line.append(line[match_index:match_index + match_length], style="bold reverse")
                
                # Добавляем текст после совпадения
                if match_index + match_length < len(line):
                    highlight_line.append(line[match_index + match_length:])
                
                console.print(highlight_line)
            
            last_line_shown = end_line
            result_count += 1
            
            # Проверяем лимит результатов
            if result_count >= max_results:
                console.print(f"\n[yellow]Показано {result_count} из {total_matches} совпадений. Уточните запрос для более точных результатов.[/]")
                return
    
    console.print(f"\n[green]Показано {result_count} из {total_matches} совпадений.[/]")
