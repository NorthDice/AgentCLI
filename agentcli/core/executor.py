"""Executor module for executing action plans."""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from agentcli.core.file_ops import read_file, write_file, delete_file
from agentcli.core.logger import Logger
from agentcli.core.validator import PlanValidator
from agentcli.core.exceptions import ExecutionError, ActionError, RollbackError, ValidationError
from agentcli.utils.logging import logger as app_logger


class Executor:
    """Class for executing action plans."""
    
    def __init__(self, logger=None):
        """Initialize the executor.
        
        Args:
            logger: Logger for recording actions. If not specified, a new one will be created.
        """
        self.logger = logger or Logger()
        self.validator = PlanValidator()
        self.executed_actions = []
        self.failed_actions = []
        
    def execute_plan(self, plan: Dict[str, Any], skip_validation: bool = False) -> Dict[str, Any]:
        """Executes an action plan.
        
        Args:
            plan (dict): The action plan to execute.
            skip_validation (bool): Skip plan validation.
            
        Returns:
            dict: Execution result of the plan.
            
        Raises:
            ExecutionError: If an error occurs during plan execution.
            ValidationError: If the plan fails validation.
        """
        plan_id = plan.get("id", datetime.now().strftime("%Y%m%d%H%M%S"))
        query = plan.get("query", "Unknown query")
        
        app_logger.info(f"Executing plan '{plan_id}'. Query: {query}")
        
        result = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "executed_actions": [],
            "failed_actions": [],
            "validation_issues": []
        }
        
        if not plan.get("actions"):
            app_logger.warning(f"Plan '{plan_id}' does not contain actions")
            return result
            
        # Validate the plan before execution
        if not skip_validation:
            try:
                app_logger.info(f"Validating plan '{plan_id}'")
                is_valid, issues = self.validator.validate_plan(plan)
                result["validation_issues"] = issues
                
                if not is_valid:
                    critical_issues = [issue for issue in issues if issue.get("critical", False)]
                    app_logger.error(f"Plan '{plan_id}' failed validation. Found {len(critical_issues)} critical issues")
                    error_msg = f"Plan contains critical issues and cannot be executed. Number of issues: {len(critical_issues)}"
                    raise ValidationError(error_msg)
                    
                app_logger.info(f"Plan '{plan_id}' validation successful. Found {len(issues)} non-critical issues")
            except ValidationError as e:
                app_logger.error(f"Validation error: {str(e)}")
                raise
        
        # Execute each action in the plan
        for i, action in enumerate(plan.get("actions", [])):
            action_type = action.get("type", "unknown")
            description = action.get("description", "No description")
            
            app_logger.info(f"Executing action {i+1}/{len(plan['actions'])}: {action_type} - {description}")
            
            try:
                action_result = self._execute_action(action)
                
                if action_result["success"]:
                    self.executed_actions.append(action)
                    result["executed_actions"].append(action_result)
                    app_logger.info(f"Action executed successfully: {action_result['message']}")
                else:
                    self.failed_actions.append(action)
                    result["failed_actions"].append(action_result)
                    app_logger.error(f"Action execution error: {action_result['message']}")
                    break  # Stop execution on first error
            except ActionError as e:
                error_msg = f"Error executing action '{action_type}': {str(e)}"
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
                error_msg = f"Unexpected error executing action '{action_type}': {str(e)}"
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
        
        # If no errors, mark the plan as successful
        result["success"] = len(result["failed_actions"]) == 0
        
        if result["success"]:
            app_logger.info(f"Plan '{plan_id}' executed successfully. Actions executed: {len(result['executed_actions'])}")
        else:
            app_logger.error(
                f"Plan '{plan_id}' executed with errors. "
                f"Executed actions: {len(result['executed_actions'])}, "
                f"Errors: {len(result['failed_actions'])}"
            )
        
        return result
    
    def _execute_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a single action from the plan.
        
        Args:
            action (dict): The action to execute.
            
        Returns:
            dict: Execution result of the action.
            
        Raises:
            ActionError: If an error occurs while executing the action.
        """
        action_type = action.get("type", "unknown")
        path = action.get("path")
        description = action.get("description", "No description")
        content = action.get("content")
        
        result = {
            "action": action,
            "success": False,
            "message": "",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            if action_type in ["create", "create_file"]:
                # Create file
                if not path:
                    error_msg = "File path not specified for creation"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                if content is None:  # content may be an empty string
                    error_msg = "No content specified for file creation"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # If path is not absolute, use current directory
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Check if file already exists
                if os.path.exists(path):
                    error_msg = f"File already exists: {path}"
                    app_logger.warning(error_msg)
                    # Could raise an error or overwrite the file
                    # Decide to overwrite with a warning
                
                # Create directories if they don't exist
                directory = os.path.dirname(path)
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                    app_logger.debug(f"Directory created: {directory}")
                
                app_logger.debug(f"Creating file: {path}")
                write_file(path, content)
                self.logger.log_action("create", f"File created: {path}", {
                    "path": path,
                    "content": content  # Сохраняем содержимое для возможности восстановления
                })
                result["success"] = True
                result["message"] = f"File created: {path}"
            
            elif action_type == "modify":
                # Modify file
                if not path:
                    error_msg = "File path not specified for modification"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                if content is None:  # content may be an empty string
                    error_msg = "No content specified for file modification"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # If path is not absolute, use current directory
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Check if file exists
                if not os.path.exists(path):
                    error_msg = f"File not found for modification: {path}"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                app_logger.debug(f"Modifying file: {path}")
                # Save old content for rollback
                old_content = read_file(path)
                
                # Write new content
                write_file(path, content)
                
                self.logger.log_action("modify", f"File modified: {path}", {
                    "path": path,
                    "old_content": old_content,
                    "new_content": content
                })
                
                result["success"] = True
                result["message"] = f"File modified: {path}"
            
            elif action_type == "delete":
                # Delete file
                if not path:
                    error_msg = "File path not specified for deletion"
                    app_logger.error(error_msg)
                    raise ActionError(error_msg, action)
                
                # If path is not absolute, use current directory
                if not os.path.isabs(path):
                    path = os.path.join(os.getcwd(), path)
                
                # Check if file exists
                if not os.path.exists(path):
                    error_msg = f"File not found for deletion: {path}"
                    app_logger.warning(error_msg)
                    # Could raise error or treat as successful deletion
                    # Decide to warn but treat as successful
                    result["success"] = True
                    result["message"] = f"File not found (already deleted): {path}"
                    return result
                
                app_logger.debug(f"Deleting file: {path}")
                # Save content for rollback
                old_content = read_file(path)
                
                # Delete file
                delete_file(path)
                
                self.logger.log_action("delete", f"File deleted: {path}", {
                    "path": path,
                    "content": old_content
                })
                
                result["success"] = True
                result["message"] = f"File deleted: {path}"
            
            elif action_type == "info":
                # Informational action, no changes required
                app_logger.info(f"Informational action: {description}")
                self.logger.log_action("info", description, action)
                result["success"] = True
                result["message"] = description
            
            else:
                error_msg = f"Unknown action type: {action_type}"
                app_logger.error(error_msg)
                raise ActionError(error_msg, action)
        
        except ActionError:
            # Reraise action errors
            raise
        
        except Exception as e:
            error_msg = f"Error executing action '{action_type}': {str(e)}"
            app_logger.exception(error_msg)
            raise ActionError(error_msg, action, cause=e)
        
        return result
    
    def rollback(self, steps=1):
        """Rolls back the last executed actions.
        
        Args:
            steps (int): Number of steps to roll back.
            
        Returns:
            dict: Rollback result.
        """
        result = {
            "success": False,
            "actions_rolled_back": [],
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Get action logs in reverse order (newest first)
        log_dir = self.logger.log_dir
        if not os.path.exists(log_dir):
            result["errors"].append("Action log not found")
            return result
        
        # Only consider regular .json logs, not ones that have already been rolled back
        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.endswith(".json") and not f.endswith("_rolled_back.json")],
            key=lambda f: os.path.getmtime(os.path.join(log_dir, f)),
            reverse=True
        )
        
        # Determine number of logs to rollback
        logs_to_rollback = min(steps, len(log_files))
        if logs_to_rollback == 0:
            result["errors"].append("No actions to roll back - action log is empty")
            app_logger.warning("Rollback attempted but no actions found in the log")
            return result
        
        rolled_back = 0
        for i in range(logs_to_rollback):
            if i >= len(log_files):
                break
                
            log_path = os.path.join(log_dir, log_files[i])
            
            try:
                # Load log
                with open(log_path, 'r') as f:
                    log = json.load(f)
                
                # Rollback action depending on its type
                action_type = log.get("action")
                details = log.get("details", {})
                
                if action_type == "create":
                    # For created file - delete it if exists, or restore if deleted
                    path = details.get("path")
                    content = details.get("content")
                    
                    if path:
                        if os.path.exists(path):
                            # File exists - delete it (normal rollback of creation)
                            os.remove(path)
                            result["actions_rolled_back"].append({
                                "type": "delete",
                                "path": path,
                                "description": f"File deleted, created by action: {log.get('description')}"
                            })
                            rolled_back += 1
                        elif content is not None:
                            # File doesn't exist but we have content - restore it
                            write_file(path, content)
                            result["actions_rolled_back"].append({
                                "type": "restore",
                                "path": path,
                                "description": f"Deleted file restored: {path}"
                            })
                            rolled_back += 1
                        else:
                            result["errors"].append(f"File not found and no content to restore: {path}")
                    else:
                        result["errors"].append(f"No path specified in create action")
                
                elif action_type == "modify":
                    # For modified file - restore previous content
                    path = details.get("path")
                    old_content = details.get("old_content")
                    
                    if path and old_content is not None:
                        write_file(path, old_content)
                        result["actions_rolled_back"].append({
                            "type": "restore",
                            "path": path,
                            "description": f"Previous state restored for file: {path}"
                        })
                        rolled_back += 1
                    else:
                        result["errors"].append(f"Not enough data to rollback file modification: {path}")
                
                elif action_type == "delete":
                    # For deleted file - restore it
                    path = details.get("path")
                    content = details.get("content")
                    
                    if path and content is not None:
                        write_file(path, content)
                        result["actions_rolled_back"].append({
                            "type": "restore",
                            "path": path,
                            "description": f"Deleted file restored: {path}"
                        })
                        rolled_back += 1
                    else:
                        result["errors"].append(f"Not enough data to restore deleted file: {path}")
                        
                # Log the rollback action itself
                self.logger.log_action("rollback", f"Rolled back action: {action_type} - {log.get('description')}", {
                    "original_action_id": log.get("id"),
                    "original_action_type": action_type,
                    "path": details.get("path")
                })
                
                # Mark this log as "rolled_back" by renaming it 
                # This allows us to keep track of what's been rolled back
                rolled_back_path = log_path.replace(".json", "_rolled_back.json")
                os.rename(log_path, rolled_back_path)
                
            except Exception as e:
                error_msg = f"Error rolling back action: {str(e)}"
                result["errors"].append(error_msg)
                app_logger.error(error_msg)
        
        # Update result
        result["success"] = rolled_back > 0
        
        # Log any errors that occurred
        if result["errors"]:
            app_logger.error(f"Rollback completed with {len(result['errors'])} errors: {result['errors']}")
        
        return result
