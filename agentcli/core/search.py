"""Модуль для поиска в файлах."""

import os
import re
import glob
import fnmatch
from pathlib import Path
from typing import List, Dict, Any, Set, Optional, Union, Pattern as RegexPattern


def get_gitignore_patterns(base_path: str = ".") -> List[str]:
    """Получает шаблоны из файла .gitignore.
    
    Args:
        base_path (str): Базовый путь для поиска .gitignore.
        
    Returns:
        List[str]: Список шаблонов из .gitignore.
    """
    gitignore_path = os.path.join(base_path, ".gitignore")
    patterns = []
    
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                # Пропускаем пустые строки и комментарии
                if line and not line.startswith('#'):
                    patterns.append(line)
    
    return patterns


def should_ignore_file(file_path: str, ignore_patterns: List[str]) -> bool:
    """Проверяет, должен ли файл быть игнорирован согласно шаблонам.
    
    Args:
        file_path (str): Путь к файлу.
        ignore_patterns (List[str]): Шаблоны для игнорирования.
        
    Returns:
        bool: True если файл должен быть игнорирован, иначе False.
    """
    # Нормализуем путь
    norm_path = os.path.normpath(file_path).replace(os.sep, '/')
    
    for pattern in ignore_patterns:
        # Нормализуем шаблон
        norm_pattern = pattern.replace(os.sep, '/')
        
        # Убираем начальный и конечный слэши
        norm_pattern = norm_pattern.strip('/')
        
        # Заменяем ** на специальный маркер
        temp_pattern = norm_pattern.replace('**', '\x00')
        
        # Заменяем * на [^/]* (любая строка кроме /)
        temp_pattern = temp_pattern.replace('*', '[^/]*')
        
        # Восстанавливаем ** как .*
        temp_pattern = temp_pattern.replace('\x00', '.*')
        
        # Компилируем регулярное выражение
        try:
            regex = re.compile(temp_pattern)
            if regex.search(norm_path):
                return True
        except re.error:
            # Если не удалось скомпилировать регулярное выражение, используем fnmatch
            if fnmatch.fnmatch(norm_path, norm_pattern):
                return True
    
    return False


def search_files(
    query: str, 
    path: str = ".", 
    file_pattern: str = "*", 
    ignore_patterns: Optional[List[str]] = None,
    is_regex: bool = False,
    use_gitignore: bool = True,
    case_sensitive: bool = False
) -> List[Dict[str, Any]]:
    """Выполняет поиск по файлам.
    
    Args:
        query (str): Строка или регулярное выражение для поиска.
        path (str): Базовый путь для поиска.
        file_pattern (str): Шаблон для фильтрации файлов.
        ignore_patterns (List[str]): Шаблоны для игнорирования.
        is_regex (bool): Использовать ли query как регулярное выражение.
        use_gitignore (bool): Использовать ли шаблоны из .gitignore.
        case_sensitive (bool): Учитывать ли регистр при поиске.
    
    Returns:
        List[Dict[str, Any]]: Список результатов поиска.
    """
    if ignore_patterns is None:
        ignore_patterns = [
            ".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", 
            "*.exe", ".env", ".venv", "env", "venv"
        ]
    
    # Если указан флаг use_gitignore, добавляем шаблоны из .gitignore
    if use_gitignore:
        gitignore_patterns = get_gitignore_patterns(path)
        if gitignore_patterns:
            ignore_patterns.extend(gitignore_patterns)
    
    # Компилируем регулярное выражение, если используется
    regex_pattern = None
    if is_regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex_pattern = re.compile(query, flags)
        except re.error:
            # Если не удалось скомпилировать регулярное выражение, используем простой поиск
            is_regex = False
    
    results = []
    
    # Рекурсивный поиск файлов
    for root, dirs, files in os.walk(path):
        # Исключаем директории из игнор-списка
        dirs[:] = [d for d in dirs if not should_ignore_file(os.path.join(root, d), ignore_patterns)]
        
        # Ищем в файлах
        for file in files:
            file_path = os.path.join(root, file)
            
            # Пропускаем файлы из игнор-списка
            if should_ignore_file(file_path, ignore_patterns):
                continue
            
            # Проверяем соответствие шаблону файла
            if not fnmatch.fnmatch(file, file_pattern):
                continue
            
            try:
                # Проверяем, что это текстовый файл
                with open(file_path, 'rb') as f:
                    content = f.read(1024)
                    
                    # Пропускаем бинарные файлы
                    if b'\0' in content:
                        continue
                
                # Открываем как текст и ищем
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    line_num = 0
                    matches = []
                    
                    for line in f:
                        line_num += 1
                        
                        if is_regex and regex_pattern:
                            # Поиск по регулярному выражению
                            for match in regex_pattern.finditer(line):
                                matches.append({
                                    "line_num": line_num,
                                    "line": line.rstrip(),
                                    "match_index": match.start(),
                                    "match_length": match.end() - match.start(),
                                    "match_text": match.group(0)
                                })
                        else:
                            # Простой текстовый поиск
                            if case_sensitive:
                                if query in line:
                                    matches.append({
                                        "line_num": line_num,
                                        "line": line.rstrip(),
                                        "match_index": line.find(query),
                                        "match_length": len(query),
                                        "match_text": query
                                    })
                            else:
                                lower_line = line.lower()
                                lower_query = query.lower()
                                if lower_query in lower_line:
                                    idx = lower_line.find(lower_query)
                                    matches.append({
                                        "line_num": line_num,
                                        "line": line.rstrip(),
                                        "match_index": idx,
                                        "match_length": len(query),
                                        "match_text": line[idx:idx+len(query)]
                                    })
                    
                    if matches:
                        results.append({
                            "file": file_path,
                            "matches": matches
                        })
            except Exception as e:
                # Пропускаем файлы, которые не можем прочитать
                continue
    
    return results


def format_search_results(results: List[Dict[str, Any]], format_type: str = "normal", base_path: str = None) -> str:
    """Форматирует результаты поиска в различные форматы.
    
    Args:
        results (List[Dict[str, Any]]): Результаты поиска.
        format_type (str): Формат вывода (normal, compact, links).
        base_path (str): Базовый путь для относительных путей.
    
    Returns:
        str: Отформатированные результаты поиска.
    """
    if not results:
        return "Ничего не найдено."
    
    total_matches = sum(len(result["matches"]) for result in results)
    
    if base_path is None:
        base_path = os.getcwd()
    
    output = []
    
    if format_type == "links":
        # Формат с ссылками file:line
        output.append(f"Найдено {total_matches} совпадений в {len(results)} файлах:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            
            for match in file_result["matches"]:
                line_num = match["line_num"]
                output.append(f"{rel_path}:{line_num}: {match['line'].strip()}")
    
    elif format_type == "compact":
        # Компактный формат
        output.append(f"Найдено {total_matches} совпадений в {len(results)} файлах:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            matches = [str(match["line_num"]) for match in file_result["matches"]]
            
            output.append(f"{rel_path} (строки: {', '.join(matches)})")
    
    else:  # normal
        # Обычный формат
        output.append(f"Найдено {total_matches} совпадений в {len(results)} файлах:\n")
        
        for file_result in results:
            file_path = file_result["file"]
            rel_path = os.path.relpath(file_path, base_path)
            
            output.append(f"\n{rel_path}:")
            
            for match in file_result["matches"]:
                line_num = match["line_num"]
                line = match["line"].rstrip()
                output.append(f"  {line_num}: {line}")
    
    return "\n".join(output)
