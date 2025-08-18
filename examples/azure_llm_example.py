#!/usr/bin/env python3
"""
Пример использования Azure OpenAI LLM сервиса.
"""
import os
import sys
from pathlib import Path

# Добавляем родительский каталог в путь для импорта
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agentcli.core import (
    create_llm_service,
    AzureOpenAIService,
    LLMServiceError
)


def main():
    """
    Демонстрирует использование Azure OpenAI LLM сервиса.
    """
    try:
        # Загружаем переменные окружения из .env файла
        load_dotenv()
        
        # Выводим информацию о конфигурации
        print("Параметры Azure OpenAI:")
        print(f"- Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"- Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        print(f"- API Version: {os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')}")
        print(f"- Model Name: {os.getenv('AZURE_OPENAI_MODEL_NAME', 'gpt-4')}")
        
        # Создаем LLM сервис
        print("\nСоздаем Azure OpenAI LLM сервис...")
        llm_service = create_llm_service()
        print(f"Тип сервиса: {type(llm_service).__name__}")
        
        # Генерируем план действий
        prompt = "Создай простую функцию для расчета факториала на Python"
        print(f"\nОтправляем запрос: {prompt}")
        
        actions = llm_service.generate_actions(prompt)
        
        print(f"\nПолучен план действий ({len(actions)} действий):")
        
        if len(actions) == 0:
            print("Не удалось получить действия от LLM.")
        
        for i, action in enumerate(actions, 1):
            print(f"\nДействие {i}:")
            print(f"Тип: {action.get('type')}")
            print(f"Путь: {action.get('path')}")
            print(f"Описание: {action.get('description')}")
            if 'content' in action:
                print("Содержимое:")
                print("-" * 40)
                print(action.get('content'))
                print("-" * 40)
        
    except LLMServiceError as e:
        print(f"Ошибка LLM сервиса: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")


if __name__ == "__main__":
    main()
