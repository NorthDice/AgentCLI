"""Planner module for creating action plans."""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional

from agentcli.core.azure_llm import get_llm_service
from agentcli.core.exceptions import PlanError, ValidationError, LLMServiceError
from agentcli.utils.logging import logger


class Planner:
    """Class for creating action plans based on user queries."""
    
    def __init__(self, llm_service=None):
        """Initialize the planner.
        
        Args:
            llm_service: Service for working with LLM. By default, Azure OpenAI service is used.
        """
        self._llm_service = llm_service
        self.plans_dir = os.path.join(os.getcwd(), "plans")
        os.makedirs(self.plans_dir, exist_ok=True)
    
    @property
    def llm_service(self):
        """Lazy initialization of LLM service."""
        if self._llm_service is None:
            self._llm_service = get_llm_service()
        return self._llm_service
    
    def create_plan(self, query: str) -> Dict[str, Any]:
        """Creates an action plan based on a query.
        
        Args:
            query (str): Natural language query.
            
        Returns:
            dict: Action plan as a dictionary.
            
        Raises:
            PlanError: If plan creation fails.
            ValidationError: If plan validation fails.
            LLMServiceError: If interaction with LLM service fails.
        """
        if not query or not query.strip():
            error_msg = "Empty query for plan creation"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        logger.info(f"Creating plan for query: '{query}'")
        
        try:
            # Get plan from LLM service
            actions = self.llm_service.generate_actions(query)
            
            if not actions:
                error_msg = "LLM service returned an empty list of actions"
                logger.warning(error_msg)
            
            # Form the plan
            plan_id = str(uuid.uuid4())
            plan = {
                "id": plan_id,
                "timestamp": datetime.now().isoformat(),
                "query": query,
                "actions": actions
            }
            
            logger.info(f"Plan '{plan_id}' created. Number of actions: {len(actions)}")
            
            return plan
        except Exception as e:
            error_msg = f"Error while creating plan: {str(e)}"
            logger.exception(error_msg)
            raise PlanError(error_msg) from e
    
    def save_plan(self, plan: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """Saves a plan to a file.
        
        Args:
            plan (dict): Action plan to save.
            output_path (str, optional): Path to save the plan.
                If not provided, the plan is saved to plans/<id>.json.
                
        Returns:
            str: Path to the saved plan file.
            
        Raises:
            PlanError: If saving the plan fails.
            ValidationError: If the plan is invalid.
        """
        if not plan:
            error_msg = "Attempt to save an empty plan"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if not isinstance(plan, dict):
            error_msg = f"Invalid plan type: {type(plan)}, expected dict"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        if "id" not in plan:
            error_msg = "Plan does not contain an identifier (id)"
            logger.error(error_msg)
            raise ValidationError(error_msg)
        
        try:
            if output_path is None:
                # Ensure the directory exists
                os.makedirs(self.plans_dir, exist_ok=True)
                output_path = os.path.join(self.plans_dir, f"{plan['id']}.json")
            
            logger.debug(f"Saving plan '{plan['id']}' to file: {output_path}")
            
            with open(output_path, 'w') as f:
                json.dump(plan, f, indent=2)
            
            logger.info(f"Plan successfully saved to file: {output_path}")
            return output_path
        except Exception as e:
            error_msg = f"Error while saving plan: {str(e)}"
            logger.exception(error_msg)
            raise PlanError(error_msg) from e
    
    def get_latest_plan_path(self) -> Optional[str]:
        """Gets the path to the latest plan file.
        
        Returns:
            str: Path to the latest plan file, or None if no plans exist.
        """
        try:
            if not os.path.exists(self.plans_dir):
                return None
            
            plan_files = [f for f in os.listdir(self.plans_dir) if f.endswith('.json')]
            if not plan_files:
                return None
            
            # Get modification times and find the latest file
            plan_paths = [os.path.join(self.plans_dir, f) for f in plan_files]
            latest_plan = max(plan_paths, key=os.path.getmtime)
            
            logger.debug(f"Latest plan found: {latest_plan}")
            return latest_plan
        except Exception as e:
            logger.error(f"Error while getting latest plan: {str(e)}")
            return None
