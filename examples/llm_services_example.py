#!/usr/bin/env python3
"""
Пример использования LLM сервисов в AgentCLI.
"""
import os
import sys
from pathlib import Path

# Добавляем родительский каталог в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentcli.core import (
    create_llm_service,
    load_config,
    get_llm_config,
    LLMServiceError
)

def main():
    """
    Демонстрирует использование LLM сервисов в AgentCLI.
    """
    try:
        # Загружаем конфигурацию из .env файла
        load_config()
        
        # Получаем конфигурацию LLM
        llm_config = get_llm_config()
        
        # Выводим информацию о конфигурации
        print(f"Используем LLM сервис: {llm_config.get('service', 'openai')}")
        
        if llm_config.get('service') == 'azure':
            print(f"Эндпоинт Azure: {llm_config.get('azure_endpoint')}")
            print(f"Имя деплоя: {llm_config.get('azure_deployment')}")
        else:
            print(f"Модель OpenAI: {llm_config.get('model', 'gpt-4o')}")
        
        # Создаем LLM сервис
        llm_service = create_llm_service()
        
        # Генерируем ответ на простой запрос
        prompt = "Напиши короткую функцию на Python для расчета факториала."
        print("\nЗапрос к LLM:", prompt)
        
        # Используем метод generate_actions для получения списка действий
        actions = llm_service.generate_actions(prompt)
        
        print("\nОтвет от LLM (план действий):")
        for i, action in enumerate(actions, 1):
            print(f"\nДействие {i}:")
            print(f"Тип: {action.get('type')}")
            print(f"Путь: {action.get('path')}")
            print(f"Описание: {action.get('description')}")
            if 'content' in action:
                print(f"Содержимое:\n{action.get('content')}")
        
    except LLMServiceError as e:
        print(f"Ошибка LLM сервиса: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")

if __name__ == "__main__":
    main()
