"""Модуль для поиска в файлах."""

import os
import re
import glob
from typing import List, Dict, Any


def search_files(query: str, path: str = ".", file_pattern: str = "*", ignore_patterns: List[str] = None) -> List[Dict[str, Any]]:
    """Выполняет поиск по файлам.
    
    Args:
        query (str): Строка для поиска.
        path (str): Базовый путь для поиска.
        file_pattern (str): Шаблон для фильтрации файлов.
        ignore_patterns (List[str]): Шаблоны для игнорирования.
    
    Returns:
        List[Dict[str, Any]]: Список результатов поиска.
    """
    if ignore_patterns is None:
        ignore_patterns = [
            ".git", "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.so", "*.dll", 
            "*.exe", ".env", ".venv", "env", "venv"
        ]
    
    results = []
    
    # Рекурсивный поиск файлов
    for root, dirs, files in os.walk(path):
        # Исключаем директории из игнор-списка
        dirs[:] = [d for d in dirs if not any(glob.fnmatch.fnmatch(d, pattern) for pattern in ignore_patterns)]
        
        # Ищем в файлах
        for file in files:
            # Пропускаем файлы из игнор-списка
            if any(glob.fnmatch.fnmatch(file, pattern) for pattern in ignore_patterns):
                continue
            
            # Проверяем соответствие шаблону файла
            if not glob.fnmatch.fnmatch(file, file_pattern):
                continue
            
            file_path = os.path.join(root, file)
            
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
                        
                        if query.lower() in line.lower():
                            matches.append({
                                "line_num": line_num,
                                "line": line.rstrip(),
                                "match_index": line.lower().find(query.lower())
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
