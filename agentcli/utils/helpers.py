"""Вспомогательные функции для AgentCLI."""

import os
import json
import yaml


def load_yaml(file_path):
    """Загружает YAML файл.
    
    Args:
        file_path (str): Путь к YAML файлу.
        
    Returns:
        dict: Содержимое YAML файла.
    """
    with open(file_path, 'r') as f:
        return yaml.safe_load(f)


def save_yaml(data, file_path):
    """Сохраняет данные в YAML файл.
    
    Args:
        data (dict): Данные для сохранения.
        file_path (str): Путь для сохранения.
        
    Returns:
        bool: Успешность операции.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)
    return True


def load_json(file_path):
    """Загружает JSON файл.
    
    Args:
        file_path (str): Путь к JSON файлу.
        
    Returns:
        dict: Содержимое JSON файла.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def save_json(data, file_path):
    """Сохраняет данные в JSON файл.
    
    Args:
        data (dict): Данные для сохранения.
        file_path (str): Путь для сохранения.
        
    Returns:
        bool: Успешность операции.
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2)
    return True
