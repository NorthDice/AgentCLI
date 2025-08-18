"""Модуль исполнителя для выполнения планов действий."""

import os
import json
from datetime import datetime

from agentcli.core.file_ops import read_file, write_file
from agentcli.core.logger import Logger


class Executor:
    """Класс для выполнения планов действий."""
    
    def __init__(self, logger=None):
        """Инициализация исполнителя.
        
        Args:
            logger: Логгер для записи действий. Если не указан, создается новый.
        """
        self.logger = logger or Logger()
        self.executed_actions = []
        self.failed_actions = []
        
    def execute_plan(self, plan):
        """Выполняет план действий.
        
        Args:
            plan (dict): План действий для выполнения.
            
        Returns:
            dict: Результат выполнения плана.
        """
        plan_id = plan.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
        
        result = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "executed_actions": [],
            "failed_actions": []
        }
        
        # Выполняем каждое действие из плана
        for action in plan.get("actions", []):
            action_result = self._execute_action(action)
            
            if action_result["success"]:
                self.executed_actions.append(action)
                result["executed_actions"].append(action_result)
            else:
                self.failed_actions.append(action)
                result["failed_actions"].append(action_result)
                break  # Останавливаем выполнение при первой ошибке
        
        # Если нет ошибок, считаем план успешно выполненным
        result["success"] = len(result["failed_actions"]) == 0
        
        return result
    
    def _execute_action(self, action):
        """Выполняет одно действие из плана.
        
        Args:
            action (dict): Действие для выполнения.
            
        Returns:
            dict: Результат выполнения действия.
        """
        action_type = action.get("type", "unknown")
        path = action.get("path")
        description = action.get("description", "Без описания")
        content = action.get("content")
        
        result = {
            "action": action,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if action_type == "create":
                # Создание файла
                if path and content:
                    write_file(path, content)
                    self.logger.log_action("create", f"Создан файл: {path}", {"path": path})
                    result["success"] = True
                    result["message"] = f"Создан файл: {path}"
                else:
                    result["message"] = "Отсутствует путь или содержимое для создания файла"
            
            elif action_type == "modify":
                # Изменение файла
                if path and content:
                    # Сохраняем предыдущее содержимое для отката
                    old_content = read_file(path) if os.path.exists(path) else ""
                    
                    # Записываем новое содержимое
                    write_file(path, content)
                    
                    self.logger.log_action("modify", f"Изменен файл: {path}", {
                        "path": path,
                        "old_content": old_content,
                        "new_content": content
                    })
                    
                    result["success"] = True
                    result["message"] = f"Изменен файл: {path}"
                else:
                    result["message"] = "Отсутствует путь или содержимое для изменения файла"
            
            elif action_type == "delete":
                # Удаление файла
                if path and os.path.exists(path):
                    # Сохраняем содержимое для возможности отката
                    old_content = read_file(path)
                    
                    # Удаляем файл
                    os.remove(path)
                    
                    self.logger.log_action("delete", f"Удален файл: {path}", {
                        "path": path,
                        "content": old_content
                    })
                    
                    result["success"] = True
                    result["message"] = f"Удален файл: {path}"
                else:
                    result["message"] = f"Файл не существует или путь не указан: {path}"
            
            elif action_type == "info":
                # Информационное действие, не требующее изменений
                self.logger.log_action("info", description, action)
                result["success"] = True
                result["message"] = description
            
            else:
                result["message"] = f"Неизвестный тип действия: {action_type}"
        
        except Exception as e:
            result["success"] = False
            result["message"] = f"Ошибка: {str(e)}"
            result["error"] = str(e)
        
        return result
    
    def rollback(self, steps=1):
        """Откатывает последние выполненные действия.
        
        Args:
            steps (int): Количество шагов для отката.
            
        Returns:
            dict: Результат отката.
        """
        # TODO: Реализовать откат действий
        return {"success": False, "message": "Функция отката пока не реализована"}
