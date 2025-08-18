"""Модуль планировщика для создания планов действий."""

import json
import os
import uuid
from datetime import datetime

from agentcli.core.llm_service import MockLLMService


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
    
    def create_plan(self, query):
        """Создает план действий на основе запроса.
        
        Args:
            query (str): Запрос на естественном языке.
            
        Returns:
            dict: План действий в формате словаря.
        """
        # Получаем план от LLM сервиса
        actions = self.llm_service.generate_actions(query)
        
        # Формируем план
        plan = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "actions": actions
        }
        
        return plan
    
    def save_plan(self, plan, output_path=None):
        """Сохраняет план в файл.
        
        Args:
            plan (dict): План действий для сохранения.
            output_path (str, optional): Путь для сохранения плана.
                Если не указан, план сохраняется в plans/<id>.json.
                
        Returns:
            str: Путь к сохраненному файлу плана.
        """
        if output_path is None:
            output_path = os.path.join(self.plans_dir, f"{plan['id']}.json")
        
        with open(output_path, 'w') as f:
            json.dump(plan, f, indent=2)
        
        return output_path
