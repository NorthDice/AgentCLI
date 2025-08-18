"""Module for validating plans before execution."""

import os
import stat
from typing import Dict, List, Any, Tuple

from agentcli.core.exceptions import ValidationError
from agentcli.utils.logging import logger


class PlanValidator:
    """Class for validating a plan before execution."""

    def __init__(self):
        """Initialize the plan validator."""
        pass

    def validate_plan(self, plan: Dict[str, Any]) -> Tuple[bool, List[Dict[str, Any]]]:
        """Validates a plan before execution.
        
        Args:
            plan (dict): The plan to validate.
            
        Returns:
            tuple: (success, issues) - validation success and list of issues.
            
        Raises:
            ValidationError: If validation cannot be performed.
        """
        if not plan or not isinstance(plan, dict):
            logger.error("Invalid plan format")
            raise ValidationError("Invalid plan format")
        
        if not plan.get("actions"):
            logger.warning("The plan contains no actions")
            return True, []
        
        issues = []
        
        # Validate each action
        for i, action in enumerate(plan.get("actions", [])):
            action_issues = self._validate_action(action, i + 1)
            issues.extend(action_issues)
        
        # Check dependencies between actions
        dependency_issues = self._validate_dependencies(plan.get("actions", []))
        issues.extend(dependency_issues)
        
        # Plan is valid if there are no critical issues
        success = not any(issue.get("critical", False) for issue in issues)
        
        if issues:
            logger.warning(f"Found {len(issues)} issues during plan validation")
        else:
            logger.info("Plan successfully passed validation")
        
        return success, issues

    def _validate_action(self, action: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
        """Validates an individual action.
        
        Args:
            action (dict): Action to validate.
            index (int): Index of the action in the plan.
            
        Returns:
            list: List of issues with the action.
        """
        issues = []
        
        # Check required fields
        required_fields = ["type"]
        for field in required_fields:
            if field not in action:
                issues.append({
                    "action_index": index,
                    "type": "missing_field",
                    "message": f"Missing required field '{field}'",
                    "critical": True
                })
        
        # Check path for file-related actions
        file_actions = ["create_file", "update_file", "delete_file", "read_file"]
        if action.get("type") in file_actions and not action.get("path"):
            issues.append({
                "action_index": index,
                "type": "missing_path",
                "message": f"Action of type '{action.get('type')}' requires a path",
                "critical": True
            })
        
        # If action works with a file, validate permissions and conflicts
        if action.get("path") and action.get("type") in file_actions:
            path_issues = self._validate_path(action, index)
            issues.extend(path_issues)
        
        return issues

    def _validate_path(self, action: Dict[str, Any], index: int) -> List[Dict[str, Any]]:
        """Validates a file path.
        
        Args:
            action (dict): Action to validate.
            index (int): Index of the action in the plan.
            
        Returns:
            list: List of issues with the path.
        """
        issues = []
        path = action.get("path")
        action_type = action.get("type")
        
        # Check for absolute path
        if not os.path.isabs(path):
            issues.append({
                "action_index": index,
                "type": "relative_path",
                "message": f"Path '{path}' should be absolute",
                "critical": False  # Not critical, can be fixed
            })
        
        # Check permissions
        if action_type in ["create_file", "update_file"] and os.path.dirname(path):
            parent_dir = os.path.dirname(path)
            if os.path.exists(parent_dir) and not os.access(parent_dir, os.W_OK):
                issues.append({
                    "action_index": index,
                    "type": "permission_denied",
                    "message": f"No write permission for directory '{parent_dir}'",
                    "critical": True
                })
        elif action_type == "read_file" and os.path.exists(path):
            if not os.access(path, os.R_OK):
                issues.append({
                    "action_index": index,
                    "type": "permission_denied",
                    "message": f"No read permission for file '{path}'",
                    "critical": True
                })
        
        # Check for conflicts
        if action_type == "create_file" and os.path.exists(path):
            issues.append({
                "action_index": index,
                "type": "file_exists",
                "message": f"File '{path}' already exists and will be overwritten",
                "critical": False  # Not critical, but attention needed
            })
        elif action_type == "delete_file" and not os.path.exists(path):
            issues.append({
                "action_index": index,
                "type": "file_not_exists",
                "message": f"File '{path}' does not exist and cannot be deleted",
                "critical": True
            })
        
        return issues

    def _validate_dependencies(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Checks dependencies between actions.
        
        Args:
            actions (list): List of actions to check.
            
        Returns:
            list: List of dependency issues.
        """
        issues = []
        file_states = {}  # Track file states
        
        for i, action in enumerate(actions):
            action_type = action.get("type")
            path = action.get("path")
            
            if not path or action_type not in ["create_file", "update_file", "delete_file", "read_file"]:
                continue
            
            # Check logical dependencies
            if action_type == "read_file" and path not in file_states:
                # Reading a file not yet created in the plan
                if not os.path.exists(path):
                    issues.append({
                        "action_index": i + 1,
                        "type": "dependency_error",
                        "message": f"Reading file '{path}' which does not exist and is not created in the plan",
                        "critical": True
                    })
            elif action_type == "delete_file" and path in file_states and file_states[path] == "deleted":
                # Deleting a file already deleted
                issues.append({
                    "action_index": i + 1,
                    "type": "dependency_error",
                    "message": f"Repeated deletion of file '{path}'",
                    "critical": True
                })
            
            # Update file state
            if action_type in ["create_file", "update_file"]:
                file_states[path] = "exists"
            elif action_type == "delete_file":
                file_states[path] = "deleted"
        
        return issues
