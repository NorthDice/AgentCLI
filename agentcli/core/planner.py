"""Модуль планировщика для создания планов действий."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from agentcli.core.llm_service import MockLLMService
from agentcli.core.exceptions import PlanError, ValidationError, LLMServiceError
from agentcli.utils.logging import logger


class Planner:
    """Класс для создания планов действий на основе запросов."""
    
    def __init__(self, llm_service=None):
        """Инициализация планировщика.
        
        Args:
            llm_service: Сервис для работы с LLM. По умолчанию используется MockLLMService.
        """
        self.llm_service = llm_service or MockLLMService()
        self.plans_dir = os.path.join(os.getcwd(), "plans")
        os.makedirs(self.plans_dir, exist_ok=True)
    
    def create_plan(self, query: str) -> Dict[str, Any]:
        """Создает план действий на основе запроса.
        
        Args:
            query (str): Запрос на естественном языке.
            
        Returns:
            dict: План действий в формате словаря.
            
        Raises:
            PlanError: При ошибке создания плана.
            ValidationError: При ошибке валидации плана.
            LLMServiceError: При ошибке взаимодействия с LLM сервисом.
        """
        if not query or not query.strip():
            error_msg = "Пустой запрос для создания плана"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        logger.info(f"Создание плана для запроса: '{query}'")
        
        try:
            # Получаем план от LLM сервиса
            actions = self.llm_service.generate_actions(query)
            
            if not actions:
                error_msg = "LLM сервис вернул пустой список действий"
                logger.warning(error_msg)
            
            # Формируем план
            plan_id = str(uuid.uuid4())
            plan = {
                "id": plan_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "actions": actions
            }
            
            logger.info(f"План '{plan_id}' создан. Количество действий: {len(actions)}")
            
            return plan
        except Exception as e:
            error_msg = f"Ошибка при создании плана: {str(e)}"
            logger.exception(error_msg)
            raise PlanError(error_msg) from e
    
    def save_plan(self, plan: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Сохраняет план в файл.
        
        Args:
            plan (dict): План действий для сохранения.
            output_path (str, optional): Путь для сохранения плана.
                Если не указан, план сохраняется в plans/<id>.json.
                
        Returns:
            str: Путь к сохраненному файлу плана.
            
        Raises:
            PlanError: Если не удалось сохранить план.
            ValidationError: Если план некорректен.
        """
        if not plan:
            error_msg = "Попытка сохранить пустой план"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if not isinstance(plan, dict):
            error_msg = f"Некорректный тип плана: {type(plan)}, ожидается dict"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if "id" not in plan:
            error_msg = "План не содержит идентификатор (id)"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            if output_path is None:
                # Убедимся, что директория существует
                os.makedirs(self.plans_dir, exist_ok=True)
                output_path = os.path.join(self.plans_dir, f"{plan['id']}.json")
            
            logger.debug(f"Сохранение плана '{plan['id']}' в файл: {output_path}")
            
            with open(output_path, 'w') as f:
                json.dump(plan, f, indent=2)
            
            logger.info(f"План успешно сохранен в файл: {output_path}")
            return output_path
        except Exception as e:
            error_msg = f"Ошибка при сохранении плана: {str(e)}"
            logger.exception(error_msg)
            raise PlanError(error_msg) from e
