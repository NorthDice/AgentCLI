"""Модуль для работы с LLM сервисами."""

import json


class MockLLMService:
    """Заглушка для LLM сервиса.
    
    В реальной реализации этот класс будет использовать API внешнего LLM
    для генерации действий на основе запроса пользователя.
    """
    
    def __init__(self):
        """Инициализация сервиса."""
        pass
    
    def generate_actions(self, query):
        """Генерирует список действий на основе запроса.
        
        Args:
            query (str): Запрос на естественном языке.
            
        Returns:
            list: Список действий.
        """
        # Заглушка с примерами действий в зависимости от запроса
        if "функция" in query.lower() and ("факториал" in query.lower() or "factorial" in query.lower()):
            return [
                {
                    "type": "create",
                    "path": "factorial.py",
                    "content": "def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)",
                    "description": "Создание функции для вычисления факториала"
                },
                {
                    "type": "create",
                    "path": "test_factorial.py",
                    "content": "import unittest\nfrom factorial import factorial\n\nclass TestFactorial(unittest.TestCase):\n    def test_factorial(self):\n        self.assertEqual(factorial(0), 1)\n        self.assertEqual(factorial(1), 1)\n        self.assertEqual(factorial(5), 120)",
                    "description": "Создание тестов для функции факториала"
                }
            ]
        elif "фибоначчи" in query.lower() or "fibonacci" in query.lower():
            return [
                {
                    "type": "create",
                    "path": "fibonacci.py",
                    "content": "def fibonacci(n):\n    if n <= 0:\n        return 0\n    elif n == 1:\n        return 1\n    else:\n        return fibonacci(n-1) + fibonacci(n-2)",
                    "description": "Создание функции для вычисления чисел Фибоначчи"
                }
            ]
        elif "hello world" in query.lower():
            return [
                {
                    "type": "create",
                    "path": "hello_world.py",
                    "content": "print('Hello, World!')",
                    "description": "Создание простой программы Hello World"
                }
            ]
        elif "csv" in query.lower() or "csv-утиліту" in query.lower() or "csv утиліту" in query.lower():
            return [
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/csv_reader.py",
                    "content": '''"""Модуль для чтения CSV файлов."""

import csv
from typing import List, Dict, Any, Optional


def read_csv(file_path: str, delimiter: str = ',', has_header: bool = True, encoding: str = 'utf-8') -> List[Dict[str, Any]]:
    """Чтение CSV файла и возврат данных в виде списка словарей.
    
    Args:
        file_path (str): Путь к CSV файлу
        delimiter (str): Разделитель полей
        has_header (bool): Имеет ли файл заголовок
        encoding (str): Кодировка файла
        
    Returns:
        List[Dict[str, Any]]: Данные из CSV файла
    """
    result = []
    
    try:
        with open(file_path, 'r', encoding=encoding) as csv_file:
            if has_header:
                reader = csv.DictReader(csv_file, delimiter=delimiter)
                result = list(reader)
            else:
                reader = csv.reader(csv_file, delimiter=delimiter)
                data = list(reader)
                # Создаем словари с числовыми ключами
                result = [dict(enumerate(row)) for row in data]
                
        return result
    except Exception as e:
        print(f"Ошибка при чтении CSV файла: {str(e)}")
        return []
''',
                    "description": "Создание модуля для чтения CSV файлов"
                },
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/csv_writer.py",
                    "content": '''"""Модуль для записи CSV файлов."""

import csv
from typing import List, Dict, Any


def write_csv(file_path: str, data: List[Dict[str, Any]], delimiter: str = ',', encoding: str = 'utf-8') -> bool:
    """Запись данных в CSV файл.
    
    Args:
        file_path (str): Путь к CSV файлу
        data (List[Dict[str, Any]]): Данные для записи
        delimiter (str): Разделитель полей
        encoding (str): Кодировка файла
        
    Returns:
        bool: True если запись успешна, False в противном случае
    """
    try:
        if not data:
            print("Предупреждение: Передан пустой список данных для записи")
            return False
            
        # Получаем заголовки из первого словаря
        fieldnames = data[0].keys()
        
        with open(file_path, 'w', encoding=encoding, newline='') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
            
        return True
    except Exception as e:
        print(f"Ошибка при записи CSV файла: {str(e)}")
        return False
''',
                    "description": "Создание модуля для записи CSV файлов"
                },
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/csv_validator.py",
                    "content": '''"""Модуль для валидации CSV файлов."""

import csv
from typing import List, Dict, Any, Tuple, Callable, Optional


def validate_csv_format(file_path: str, delimiter: str = ',', encoding: str = 'utf-8') -> Tuple[bool, str]:
    """Проверяет формат CSV файла.
    
    Args:
        file_path (str): Путь к CSV файлу
        delimiter (str): Разделитель полей
        encoding (str): Кодировка файла
        
    Returns:
        Tuple[bool, str]: Результат проверки и сообщение об ошибке
    """
    try:
        with open(file_path, 'r', encoding=encoding) as csv_file:
            # Проверяем, можно ли прочитать файл как CSV
            reader = csv.reader(csv_file, delimiter=delimiter)
            rows = list(reader)
            
            if not rows:
                return False, "CSV файл пуст"
            
            # Проверяем, одинаковое ли количество полей в каждой строке
            field_count = len(rows[0])
            for i, row in enumerate(rows[1:], 2):
                if len(row) != field_count:
                    return False, f"Несогласованное количество полей в строке {i}"
            
            return True, "CSV файл имеет правильный формат"
    except Exception as e:
        return False, f"Ошибка при проверке формата CSV: {str(e)}"


def validate_data(data: List[Dict[str, Any]], validations: Dict[str, Callable]) -> List[Dict[str, Any]]:
    """Проверяет данные на соответствие правилам валидации.
    
    Args:
        data (List[Dict[str, Any]]): Данные для проверки
        validations (Dict[str, Callable]): Словарь правил валидации
            Ключи - имена полей, значения - функции проверки
            
    Returns:
        List[Dict[str, Any]]: Список ошибок валидации
    """
    errors = []
    
    for i, row in enumerate(data, 1):
        row_errors = {}
        
        for field, validation_func in validations.items():
            if field in row:
                is_valid, message = validation_func(row[field])
                if not is_valid:
                    row_errors[field] = message
        
        if row_errors:
            errors.append({
                "row": i,
                "errors": row_errors
            })
    
    return errors
''',
                    "description": "Создание модуля для валидации CSV файлов"
                },
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/csv_transform.py",
                    "content": '''"""Модуль для трансформации данных CSV."""

from typing import List, Dict, Any, Callable


def map_columns(data: List[Dict[str, Any]], mapping: Dict[str, str]) -> List[Dict[str, Any]]:
    """Переименовывает столбцы по указанному отображению.
    
    Args:
        data (List[Dict[str, Any]]): Исходные данные
        mapping (Dict[str, str]): Отображение {старое_имя: новое_имя}
        
    Returns:
        List[Dict[str, Any]]: Данные с переименованными столбцами
    """
    result = []
    
    for row in data:
        new_row = {}
        for old_key, value in row.items():
            new_key = mapping.get(old_key, old_key)
            new_row[new_key] = value
        result.append(new_row)
    
    return result


def filter_rows(data: List[Dict[str, Any]], condition: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
    """Фильтрует строки по указанному условию.
    
    Args:
        data (List[Dict[str, Any]]): Исходные данные
        condition (Callable): Функция-предикат для фильтрации
        
    Returns:
        List[Dict[str, Any]]: Отфильтрованные данные
    """
    return [row for row in data if condition(row)]


def transform_values(data: List[Dict[str, Any]], column: str, transformer: Callable) -> List[Dict[str, Any]]:
    """Преобразует значения в указанном столбце.
    
    Args:
        data (List[Dict[str, Any]]): Исходные данные
        column (str): Имя столбца для преобразования
        transformer (Callable): Функция преобразования
        
    Returns:
        List[Dict[str, Any]]: Данные с преобразованными значениями
    """
    result = []
    
    for row in data:
        new_row = dict(row)
        if column in new_row:
            new_row[column] = transformer(new_row[column])
        result.append(new_row)
    
    return result
''',
                    "description": "Создание модуля для трансформации CSV данных"
                },
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/__init__.py",
                    "content": '''"""CSV утилита для работы с CSV файлами."""

from csv_utility.csv_reader import read_csv
from csv_utility.csv_writer import write_csv
from csv_utility.csv_validator import validate_csv_format, validate_data
from csv_utility.csv_transform import map_columns, filter_rows, transform_values

__all__ = [
    'read_csv',
    'write_csv',
    'validate_csv_format',
    'validate_data',
    'map_columns',
    'filter_rows',
    'transform_values'
]
''',
                    "description": "Создание инициализационного файла для пакета CSV утилиты"
                },
                {
                    "type": "create_file",
                    "path": "/home/kyoto/PythonProjects/AgentCLI/csv_utility/examples/example_usage.py",
                    "content": '''"""Пример использования CSV утилиты."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from csv_utility.csv_reader import read_csv
from csv_utility.csv_writer import write_csv
from csv_utility.csv_validator import validate_csv_format, validate_data
from csv_utility.csv_transform import map_columns, filter_rows, transform_values


# Пример создания тестового CSV файла
def create_sample_csv(file_path: str):
    """Создает тестовый CSV файл."""
    data = [
        {'name': 'John', 'age': '30', 'city': 'New York'},
        {'name': 'Alice', 'age': '25', 'city': 'Boston'},
        {'name': 'Bob', 'age': '35', 'city': 'Chicago'},
        {'name': 'Eve', 'age': '28', 'city': 'Miami'}
    ]
    write_csv(file_path, data)
    print(f"Создан тестовый CSV файл: {file_path}")


def main():
    """Основная функция с примерами использования."""
    # Создаем директорию для примеров, если она не существует
    examples_dir = os.path.dirname(os.path.abspath(__file__))
    sample_file = os.path.join(examples_dir, "sample_data.csv")
    
    # Создаем тестовый CSV файл
    create_sample_csv(sample_file)
    
    # Проверяем формат CSV
    is_valid, message = validate_csv_format(sample_file)
    print(f"Валидация формата: {message}")
    
    # Читаем данные из CSV
    data = read_csv(sample_file)
    print("Прочитанные данные:")
    for row in data:
        print(row)
    
    # Преобразуем возраст в числа
    transformed_data = transform_values(data, 'age', lambda x: int(x))
    print("\nВозраст преобразован в числа:")
    for row in transformed_data:
        print(row)
    
    # Фильтруем по возрасту
    filtered_data = filter_rows(transformed_data, lambda row: row['age'] > 28)
    print("\nФильтрация по возрасту > 28:")
    for row in filtered_data:
        print(row)
    
    # Переименовываем столбцы
    mapped_data = map_columns(filtered_data, {'name': 'имя', 'age': 'возраст', 'city': 'город'})
    print("\nПереименованные столбцы:")
    for row in mapped_data:
        print(row)
    
    # Записываем результат в новый файл
    result_file = os.path.join(examples_dir, "transformed_data.csv")
    write_csv(result_file, mapped_data)
    print(f"\nРезультат записан в файл: {result_file}")


if __name__ == "__main__":
    main()
''',
                    "description": "Создание примера использования CSV утилиты"
                }
            ]
        else:
            # Для неизвестных запросов возвращаем заглушку
            return [
                {
                    "type": "info",
                    "path": None,
                    "content": None,
                    "description": f"Анализ запроса: {query}"
                }
            ]
