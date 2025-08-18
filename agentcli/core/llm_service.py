"""Модуль с базовыми классами для LLM сервисов."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMService(ABC):
    """Абстрактный базовый класс для LLM сервисов."""
    
    def __init__(self):
        """Инициализация сервиса."""
        pass
    
    @abstractmethod
    def generate_actions(self, query: str) -> List[Dict[str, Any]]:
        """Генерирует список действий на основе запроса.
        
        Args:
            query (str): Запрос на естественном языке.
            
        Returns:
            List[Dict[str, Any]]: Список действий.
        """
        pass
