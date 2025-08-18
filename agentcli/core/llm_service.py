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
