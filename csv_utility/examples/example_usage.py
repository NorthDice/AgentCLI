"""Пример использования CSV утилиты."""

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
