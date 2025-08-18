"""
Команда для проверки конфигурации LLM сервисов
"""
import os
import click
import json
from typing import Optional

from dotenv import load_dotenv
from agentcli.core import create_llm_service, LLMServiceError


@click.command()
@click.option('--test', is_flag=True, help='Проверить соединение с LLM сервисом')
def llm_config(test):
    """Проверка конфигурации LLM сервиса."""
    # Загружаем .env файл
    load_dotenv()
    
    # Собираем конфигурацию из переменных окружения
    config = {
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
        "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION"),
        "deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        "model_name": os.environ.get("AZURE_OPENAI_MODEL_NAME")
    }
    
    click.echo("Текущая конфигурация Azure OpenAI:")
    # Не показываем API ключ полностью
    if config["api_key"]:
        config["api_key"] = f"{config['api_key'][:5]}...{config['api_key'][-5:]}"
    click.echo(json.dumps(config, indent=2, ensure_ascii=False))
    
    if test:
        click.echo("\nПроверяем соединение с Azure OpenAI...")
        try:
            service = create_llm_service()
            
            test_query = "Ответь коротко 'OK' если ты работаешь."
            click.echo(f"Запрос: {test_query}")
            
            actions = service.generate_actions(test_query)
            
            click.echo(f"\nПолучено {len(actions)} действий от LLM")
            for i, action in enumerate(actions, 1):
                click.echo(f"Действие {i}: {action.get('type')} - {action.get('description')}")
            
            click.echo("\n✅ Соединение успешно установлено!")
        except LLMServiceError as e:
            click.echo(f"\n❌ Ошибка при подключении к LLM сервису: {e}", err=True)
