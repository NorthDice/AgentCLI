"""Модуль для валидации планов перед выполнением."""

import os
import stat
from typing import Dict, List, Any, Tuple

from agentcli.core.exceptions import ValidationError
from agentcli.utils.logging import logger


class PlanValidator:
    """Класс для валидации плана перед выполнением."""

    def __init__(self):
        """Инициализация валидатора плана."""
        pass

    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Валидирует план перед выполнением.
        
        Args:
            plan (dict): План для валидации.
            
        Returns:
            tuple: (success, issues) - успешность валидации и список проблем.
            
        Raises:
            ValidationError: Если валидация не может быть выполнена.
        """
        if not plan or not isinstance(plan, dict):
            logger.error("Некорректный формат плана")
            raise ValidationError("Некорректный формат плана")
        
        if not plan.get("actions"):
            logger.warning("План не содержит действий")
            return True, []
        
        issues = []
        
        # Валидация каждого действия
        for i, action in enumerate(plan.get("actions", [])):
            action_issues = self._validate_action(action, i + 1)
            issues.extend(action_issues)
        
        # Проверка зависимостей между действиями
        dependency_issues = self._validate_dependencies(plan.get("actions", []))
        issues.extend(dependency_issues)
        
        # План валиден, если нет критических проблем
        success = not any(issue.get("critical", False) for issue in issues)
        
        if issues:
            logger.warning(f"Найдено {len(issues)} проблем при валидации плана")
        else:
            logger.info("План успешно прошел валидацию")
        
        return success, issues

    def _validate_action(self, action: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
        """Валидирует отдельное действие.
        
        Args:
            action (dict): Действие для валидации.
            index (int): Индекс действия в плане.
            
        Returns:
            list: Список проблем с действием.
        """
        issues = []
        
        # Проверяем обязательные поля
        required_fields = ["type"]
        for field in required_fields:
            if field not in action:
                issues.append({
                    "action_index": index,
                    "type": "missing_field",
                    "message": f"Отсутствует обязательное поле '{field}'",
                    "critical": True
                })
        
        # Проверяем поле path для действий, которые работают с файлами
        file_actions = ["create_file", "update_file", "delete_file", "read_file"]
        if action.get("type") in file_actions and not action.get("path"):
            issues.append({
                "action_index": index,
                "type": "missing_path",
                "message": f"Действие типа '{action.get('type')}' требует указания пути",
                "critical": True
            })
        
        # Если действие работает с файлом, проверяем права доступа и конфликты
        if action.get("path") and action.get("type") in file_actions:
            path_issues = self._validate_path(action, index)
            issues.extend(path_issues)
        
        return issues

    def _validate_path(self, action: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
        """Валидирует путь к файлу.
        
        Args:
            action (dict): Действие для валидации.
            index (int): Индекс действия в плане.
            
        Returns:
            list: Список проблем с путем.
        """
        issues = []
        path = action.get("path")
        action_type = action.get("type")
        
        # Проверка абсолютного пути
        if not os.path.isabs(path):
            issues.append({
                "action_index": index,
                "type": "relative_path",
                "message": f"Путь '{path}' должен быть абсолютным",
                "critical": False  # Не критично, можно преобразовать
            })
        
        # Проверка прав доступа
        if action_type in ["create_file", "update_file"] and os.path.dirname(path):
            parent_dir = os.path.dirname(path)
            if os.path.exists(parent_dir) and not os.access(parent_dir, os.W_OK):
                issues.append({
                    "action_index": index,
                    "type": "permission_denied",
                    "message": f"Нет прав на запись в директорию '{parent_dir}'",
                    "critical": True
                })
        elif action_type == "read_file" and os.path.exists(path):
            if not os.access(path, os.R_OK):
                issues.append({
                    "action_index": index,
                    "type": "permission_denied",
                    "message": f"Нет прав на чтение файла '{path}'",
                    "critical": True
                })
        
        # Проверка конфликтов
        if action_type == "create_file" and os.path.exists(path):
            issues.append({
                "action_index": index,
                "type": "file_exists",
                "message": f"Файл '{path}' уже существует и будет перезаписан",
                "critical": False  # Не критично, но требует внимания
            })
        elif action_type == "delete_file" and not os.path.exists(path):
            issues.append({
                "action_index": index,
                "type": "file_not_exists",
                "message": f"Файл '{path}' не существует и не может быть удален",
                "critical": True
            })
        
        return issues

    def _validate_dependencies(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Проверяет зависимости между действиями.
        
        Args:
            actions (list): Список действий для проверки.
            
        Returns:
            list: Список проблем с зависимостями.
        """
        issues = []
        file_states = {}  # Отслеживание состояния файлов
        
        for i, action in enumerate(actions):
            action_type = action.get("type")
            path = action.get("path")
            
            if not path or action_type not in ["create_file", "update_file", "delete_file", "read_file"]:
                continue
            
            # Проверка логических зависимостей
            if action_type == "read_file" and path not in file_states:
                # Чтение файла, который еще не создан в плане
                if not os.path.exists(path):
                    issues.append({
                        "action_index": i + 1,
                        "type": "dependency_error",
                        "message": f"Чтение файла '{path}', который не существует и не создан в плане",
                        "critical": True
                    })
            elif action_type == "delete_file" and path in file_states and file_states[path] == "deleted":
                # Удаление уже удаленного файла
                issues.append({
                    "action_index": i + 1,
                    "type": "dependency_error",
                    "message": f"Повторное удаление файла '{path}'",
                    "critical": True
                })
            
            # Обновляем состояние файла
            if action_type in ["create_file", "update_file"]:
                file_states[path] = "exists"
            elif action_type == "delete_file":
                file_states[path] = "deleted"
        
        return issues
