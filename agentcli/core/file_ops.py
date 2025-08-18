"""Модуль для операций с файлами."""

import os


def read_file(file_path):
    """Читает содержимое файла.
    
    Args:
        file_path (str): Путь к файлу.
        
    Returns:
        str: Содержимое файла.
    """
    with open(file_path, 'r') as f:
        return f.read()


def write_file(file_path, content):
    """Записывает содержимое в файл.
    
    Args:
        file_path (str): Путь к файлу.
        content (str): Содержимое для записи.
        
    Returns:
        bool: Успешность операции.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    return True
