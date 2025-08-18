"""Модуль исполнителя для выполнения планов действий."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

from agentcli.core.file_ops import read_file, write_file, delete_file
from agentcli.core.logger import Logger
from agentcli.core.exceptions import ExecutionError, ActionError, RollbackError
from agentcli.utils.logging import logger as app_logger


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
        
    def execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет план действий.
        
        Args:
            plan (dict): План действий для выполнения.
            
        Returns:
            dict: Результат выполнения плана.
            
        Raises:
            ExecutionError: Если произошла ошибка при выполнении плана.
        """
        plan_id = plan.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
        query = plan.get("query", "Неизвестный запрос")
        
        app_logger.info(f"Выполнение плана '{plan_id}'. Запрос: {query}")
        
        result = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "executed_actions": [],
            "failed_actions": []
        }
        
        if not plan.get("actions"):
            app_logger.warning(f"План '{plan_id}' не содержит действий")
            return result
        
        # Выполняем каждое действие из плана
        for i, action in enumerate(plan.get("actions", [])):
            action_type = action.get("type", "unknown")
            description = action.get("description", "Нет описания")
            
            app_logger.info(f"Выполнение действия {i+1}/{len(plan['actions'])}: {action_type} - {description}")
            
            try:
                action_result = self._execute_action(action)
                
                if action_result["success"]:
                    self.executed_actions.append(action)
                    result["executed_actions"].append(action_result)
                    app_logger.info(f"Действие успешно выполнено: {action_result['message']}")
                else:
                    self.failed_actions.append(action)
                    result["failed_actions"].append(action_result)
                    app_logger.error(f"Ошибка при выполнении действия: {action_result['message']}")
                    break  # Останавливаем выполнение при первой ошибке
            except ActionError as e:
                error_msg = f"Ошибка при выполнении действия '{action_type}': {str(e)}"
                app_logger.error(error_msg)
                
                action_result = {
                    "action": action,
                    "success": False,
                    "message": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                
                self.failed_actions.append(action)
                result["failed_actions"].append(action_result)
                break
            except Exception as e:
                error_msg = f"Неожиданная ошибка при выполнении действия '{action_type}': {str(e)}"
                app_logger.exception(error_msg)
                
                action_result = {
                    "action": action,
                    "success": False,
                    "message": error_msg,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
                
                self.failed_actions.append(action)
                result["failed_actions"].append(action_result)
                break
        
        # Если нет ошибок, считаем план успешно выполненным
        result["success"] = len(result["failed_actions"]) == 0
        
        if result["success"]:
            app_logger.info(f"План '{plan_id}' успешно выполнен. Выполнено действий: {len(result['executed_actions'])}")
        else:
            app_logger.error(
                f"План '{plan_id}' выполнен с ошибками. "
                f"Выполнено действий: {len(result['executed_actions'])}, "
                f"Ошибок: {len(result['failed_actions'])}"
            )
        
        return result
    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет одно действие из плана.
        
        Args:
            action (dict): Действие для выполнения.
            
        Returns:
            dict: Результат выполнения действия.
            
        Raises:
            ActionError: Если произошла ошибка при выполнении действия.
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
                if not path:
                    error_msg = "Не указан путь для создания файла"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                if content is None:  # content может быть пустой строкой
                    error_msg = "Не указано содержимое для создания файла"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # Если путь не абсолютный, используем текущую директорию
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Проверяем, существует ли файл
                if os.path.exists(path):
                    error_msg = f"Файл уже существует: {path}"
                    app_logger.warning(error_msg)
                    # Здесь можно либо вызвать исключение, либо перезаписать файл
                    # Решим перезаписать с предупреждением
                
                app_logger.debug(f"Создание файла: {path}")
                write_file(path, content)
                self.logger.log_action("create", f"Создан файл: {path}", {"path": path})
                result["success"] = True
                result["message"] = f"Создан файл: {path}"
            
            elif action_type == "modify":
                # Изменение файла
                if not path:
                    error_msg = "Не указан путь для изменения файла"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                if content is None:  # content может быть пустой строкой
                    error_msg = "Не указано содержимое для изменения файла"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # Если путь не абсолютный, используем текущую директорию
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Проверяем, существует ли файл
                if not os.path.exists(path):
                    error_msg = f"Файл для изменения не найден: {path}"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                app_logger.debug(f"Изменение файла: {path}")
                # Сохраняем предыдущее содержимое для отката
                old_content = read_file(path)
                
                # Записываем новое содержимое
                write_file(path, content)
                
                self.logger.log_action("modify", f"Изменен файл: {path}", {
                    "path": path,
                    "old_content": old_content,
                    "new_content": content
                })
                
                result["success"] = True
                result["message"] = f"Изменен файл: {path}"
            
            elif action_type == "delete":
                # Удаление файла
                if not path:
                    error_msg = "Не указан путь для удаления файла"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # Если путь не абсолютный, используем текущую директорию
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Проверяем, существует ли файл
                if not os.path.exists(path):
                    error_msg = f"Файл для удаления не найден: {path}"
                    app_logger.warning(error_msg)
                    # Здесь можно либо вызвать исключение, либо считать удаление успешным
                    # Решим выдать предупреждение, но считать операцию успешной
                    result["success"] = True
                    result["message"] = f"Файл не найден (уже удален): {path}"
                    return result
                
                app_logger.debug(f"Удаление файла: {path}")
                # Сохраняем содержимое для возможности отката
                old_content = read_file(path)
                
                # Удаляем файл
                delete_file(path)
                
                self.logger.log_action("delete", f"Удален файл: {path}", {
                    "path": path,
                    "content": old_content
                })
                
                result["success"] = True
                result["message"] = f"Удален файл: {path}"
            
            elif action_type == "info":
                # Информационное действие, не требующее изменений
                app_logger.info(f"Информационное действие: {description}")
                self.logger.log_action("info", description, action)
                result["success"] = True
                result["message"] = description
            
            else:
                error_msg = f"Неизвестный тип действия: {action_type}"
                app_logger.error(error_msg)
                raise ActionError(error_msg, action)
        
        except ActionError:
            # Пробрасываем ошибки действий дальше
            raise
        
        except Exception as e:
            error_msg = f"Ошибка при выполнении действия '{action_type}': {str(e)}"
            app_logger.exception(error_msg)
            raise ActionError(error_msg, action, cause=e)
        
        return result
    
    def rollback(self, steps=1):
        """Откатывает последние выполненные действия.
        
        Args:
            steps (int): Количество шагов для отката.
            
        Returns:
            dict: Результат отката.
        """
        result = {
            "success": False,
            "actions_rolled_back": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Получаем логи действий в обратном порядке (от новых к старым)
        log_dir = self.logger.log_dir
        if not os.path.exists(log_dir):
            result["errors"].append("Журнал действий не найден")
            return result
        
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.endswith(".json")],
            key=lambda f: os.path.getmtime(os.path.join(log_dir, f)),
            reverse=True
        )
        
        # Определяем количество логов для отката
        logs_to_rollback = min(steps, len(log_files))
        if logs_to_rollback == 0:
            result["errors"].append("Нет действий для отката")
            return result
        
        rolled_back = 0
        for i in range(logs_to_rollback):
            if i >= len(log_files):
                break
                
            log_path = os.path.join(log_dir, log_files[i])
            
            try:
                # Загружаем лог
                with open(log_path, 'r') as f:
                    log = json.load(f)
                
                # Откатываем действие в зависимости от его типа
                action_type = log.get("action")
                details = log.get("details", {})
                
                if action_type == "create":
                    # Для созданного файла - удаляем его
                    path = details.get("path")
                    if path and os.path.exists(path):
                        os.remove(path)
                        result["actions_rolled_back"].append({
                            "type": "delete",
                            "path": path,
                            "description": f"Удален файл, созданный действием: {log.get('description')}"
                        })
                        rolled_back += 1
                    else:
                        result["errors"].append(f"Файл не найден: {path}")
                
                elif action_type == "modify":
                    # Для измененного файла - возвращаем предыдущее содержимое
                    path = details.get("path")
                    old_content = details.get("old_content")
                    
                    if path and old_content is not None:
                        write_file(path, old_content)
                        result["actions_rolled_back"].append({
                            "type": "restore",
                            "path": path,
                            "description": f"Восстановлено предыдущее состояние файла: {path}"
                        })
                        rolled_back += 1
                    else:
                        result["errors"].append(f"Недостаточно данных для отката изменения файла: {path}")
                
                elif action_type == "delete":
                    # Для удаленного файла - восстанавливаем его
                    path = details.get("path")
                    content = details.get("content")
                    
                    if path and content is not None:
                        write_file(path, content)
                        result["actions_rolled_back"].append({
                            "type": "restore",
                            "path": path,
                            "description": f"Восстановлен удаленный файл: {path}"
                        })
                        rolled_back += 1
                    else:
                        result["errors"].append(f"Недостаточно данных для восстановления файла: {path}")
                
                # Логируем откат действия
                self.logger.log_action(
                    "rollback",
                    f"Откат действия: {log.get('description', 'Неизвестное действие')}",
                    {"original_action": log}
                )
                
                # Удаляем лог откаченного действия
                os.remove(log_path)
                
            except Exception as e:
                result["errors"].append(f"Ошибка отката действия: {str(e)}")
        
        # Обновляем результат
        result["success"] = rolled_back > 0
        
        return result
