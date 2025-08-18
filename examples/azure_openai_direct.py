#!/usr/bin/env python3
"""
Пример прямого использования Azure OpenAI API.
"""
import os
import sys
import dotenv
from openai import AzureOpenAI

def main():
    """
    Демонстрирует прямое использование Azure OpenAI API.
    """
    try:
        # Загружаем переменные окружения из .env файла
        dotenv.load_dotenv()
        
        # Получаем параметры из переменных окружения
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')
        
        if not all([api_key, endpoint, deployment_name]):
            print("Ошибка: Не все параметры доступны в .env файле.")
            print("Убедитесь, что указаны AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT и AZURE_OPENAI_DEPLOYMENT_NAME.")
            return
        
        print("Параметры Azure OpenAI:")
        print(f"- Endpoint: {endpoint}")
        print(f"- Deployment: {deployment_name}")
        print(f"- API Version: {api_version}")
        
        # Создаем клиент Azure OpenAI
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
        )
        
        # Отправляем запрос к API
        prompt = "Напиши короткую функцию на Python для расчета факториала."
        
        print("\nОтправляем запрос:", prompt)
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "Ты - полезный помощник-программист."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Выводим ответ
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content
            print("\nОтвет от Azure OpenAI:")
            print(answer)
        else:
            print("Ошибка: Пустой ответ от API")
        
    except Exception as e:
        print(f"Ошибка при использовании Azure OpenAI API: {e}")

if __name__ == "__main__":
    main()
