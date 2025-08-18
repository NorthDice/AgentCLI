"""Модуль для работы с Azure OpenAI API."""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI

from agentcli.core.llm_service import LLMService
from agentcli.core.exceptions import LLMServiceError
from agentcli.utils.logging import logger


class AzureOpenAIService(LLMService):
    """Сервис для работы с Azure OpenAI API."""
    
    def __init__(self):
        """Инициализация сервиса Azure OpenAI."""
        super().__init__()
        
        # Загружаем конфигурацию из переменных окружения
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.model_name = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "10000"))
        
        # Проверяем обязательные параметры
        if not self.api_key or not self.endpoint or not self.deployment:
            missing = []
            if not self.api_key:
                missing.append("AZURE_OPENAI_API_KEY")
            if not self.endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self.deployment:
                missing.append("AZURE_OPENAI_DEPLOYMENT")
                
            error_msg = f"Отсутствуют обязательные параметры для Azure OpenAI: {', '.join(missing)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)
        
        # Настраиваем системный промпт
        self.system_prompt = """
        Ты - помощник для генерации плана действий по файловой системе на основе естественного языка.
        
        Твоя задача - преобразовать запрос пользователя в последовательность действий для выполнения в файловой системе.
        
        Для каждого действия должны быть указаны:
        1. Тип действия (create_file, modify, delete, info)
        2. Путь к файлу (абсолютный или относительный)
        3. Содержимое файла (для create_file и modify)
        4. Описание действия
        
        Выводи результат строго в формате JSON.
        """
        
        # Инициализация клиента Azure OpenAI
        try:
            self.client = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                timeout=60.0,  # Увеличиваем timeout для запросов
            )
            logger.debug("Azure OpenAI клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка при инициализации Azure OpenAI клиента: {str(e)}")
            raise LLMServiceError(f"Не удалось инициализировать Azure OpenAI клиент: {str(e)}")
    
    def _format_actions(self, actions_text: str) -> List[Dict[str, Any]]:
        """Форматирует текст с действиями в структуру данных.
        
        Args:
            actions_text (str): Текст с действиями в формате JSON.
            
        Returns:
            List[Dict[str, Any]]: Список действий.
            
        Raises:
            LLMServiceError: Если не удалось распарсить JSON с действиями.
        """
        try:
            # Сначала попробуем загрузить весь текст как JSON
            try:
                result = json.loads(actions_text.strip())
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and "actions" in result:
                    return result["actions"]
            except json.JSONDecodeError:
                # Если не получилось, пробуем извлечь JSON из ответа
                pass
                
            # Извлекаем JSON из ответа
            # Часто модель может вернуть текст до и после JSON
            json_start = actions_text.find("[")
            json_end = actions_text.rfind("]")
            
            if json_start != -1 and json_end != -1:
                json_str = actions_text[json_start:json_end+1]
                try:
                    actions = json.loads(json_str)
                    if isinstance(actions, list):
                        return actions
                except:
                    pass
            
            # Пробуем найти JSON-объект
            json_start = actions_text.find("{")
            json_end = actions_text.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = actions_text[json_start:json_end+1]
                try:
                    result = json.loads(json_str)
                    if isinstance(result, dict) and "actions" in result:
                        return result["actions"]
                    elif isinstance(result, dict):
                        # Если это один объект действия, обернем его в список
                        return [result]
                except:
                    pass
            
            # В противном случае возвращаем пустой список
            logger.warning(f"Не удалось распарсить JSON из ответа: {actions_text}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка при парсинге JSON ответа от LLM: {str(e)}")
            logger.debug(f"Ответ LLM: {actions_text}")
            raise LLMServiceError(f"Не удалось распарсить JSON с действиями: {str(e)}")
    
    def generate_actions(self, query: str) -> List[Dict[str, Any]]:
        """Генерирует список действий на основе запроса, используя Azure OpenAI API.
        
        Args:
            query (str): Запрос на естественном языке.
            
        Returns:
            List[Dict[str, Any]]: Список действий.
            
        Raises:
            LLMServiceError: При ошибке взаимодействия с Azure OpenAI API.
        """
        try:
            user_prompt = f"""
            Запрос пользователя: {query}
            
            Пожалуйста, создай план действий для выполнения этого запроса.
            
            Формат ответа:
            [
                {{
                    "type": "create_file", // Тип действия (create_file, modify, delete, info)
                    "path": "path/to/file.txt", // Путь к файлу
                    "content": "содержимое файла", // Содержимое файла (для create_file и modify)
                    "description": "Описание действия" // Краткое описание действия
                }},
                // Другие действия...
            ]
            """
            
            logger.debug(f"Отправка запроса в Azure OpenAI: {query}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,  # Для Azure используется deployment
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                raise LLMServiceError("Пустой ответ от Azure OpenAI API")
            
            message_content = response.choices[0].message.content
            
            if not message_content:
                raise LLMServiceError("Пустое содержимое сообщения от Azure OpenAI API")
            
            logger.debug(f"Полученный ответ: {message_content}")
            
            # Парсинг результата
            actions = self._format_actions(message_content)
            logger.debug(f"Сгенерировано {len(actions)} действий от Azure OpenAI")
            
            # Если действий нет, возможно, мы не смогли распарсить JSON
            if len(actions) == 0:
                logger.warning("Не удалось распарсить действия из ответа LLM")
                logger.debug(f"Полный ответ: {message_content}")
                
                # Попробуем вернуть хоть что-то
                return [{
                    "type": "info",
                    "path": "response.txt",
                    "content": message_content,
                    "description": "Ответ от LLM (не удалось распарсить как план действий)"
                }]
            
            return actions
            
        except Exception as e:
            logger.error(f"Ошибка при генерации действий через Azure OpenAI: {str(e)}")
            raise LLMServiceError(f"Не удалось получить ответ от Azure OpenAI API: {str(e)}")


def create_llm_service() -> LLMService:
    """Создает экземпляр LLM сервиса.
    
    Returns:
        LLMService: Экземпляр LLM сервиса.
        
    Raises:
        LLMServiceError: При ошибке создания LLM сервиса.
    """
    try:
        logger.info("Используется Azure OpenAI LLM сервис")
        return AzureOpenAIService()
    except Exception as e:
        error_msg = f"Ошибка при создании Azure OpenAI LLM сервиса: {str(e)}"
        logger.error(error_msg)
        raise LLMServiceError(error_msg)
