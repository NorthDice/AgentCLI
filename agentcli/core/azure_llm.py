"""Module for working with Azure OpenAI API."""

import os
import json
import logging
from typing import List, Dict, Any, Optional

from openai import AzureOpenAI

from agentcli.core.llm_service import LLMService
from agentcli.core.exceptions import LLMServiceError
from agentcli.utils.logging import logger


class AzureOpenAIService(LLMService):
    """Service for working with Azure OpenAI API."""
    
    def __init__(self):
        """Initialize Azure OpenAI service."""
        super().__init__()
        
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.model_name = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4")
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "10000"))
        
        if not self.api_key or not self.endpoint or not self.deployment:
            missing = []
            if not self.api_key:
                missing.append("AZURE_OPENAI_API_KEY")
            if not self.endpoint:
                missing.append("AZURE_OPENAI_ENDPOINT")
            if not self.deployment:
                missing.append("AZURE_OPENAI_DEPLOYMENT")
                
            error_msg = f"Missing required parameters for Azure OpenAI: {', '.join(missing)}"
            logger.error(error_msg)
            raise LLMServiceError(error_msg)
        
        self.system_prompt = """
        You are an assistant for generating filesystem action plans based on natural language.
        
        Your task is to convert user requests into a sequence of actions to be executed in the file system.
        
        For each action, specify:
        1. Action type (create_file, modify, delete, info)
        2. File path (absolute or relative)
        3. File content (for create_file and modify)
        4. Action description
        
        Return the result strictly in JSON format.
        """
        
        try:
            self.client = AzureOpenAI(
                api_version=self.api_version,
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                timeout=60.0,
            )
            logger.debug("Azure OpenAI client successfully initialized")
        except Exception as e:
            logger.error(f"Error initializing Azure OpenAI client: {str(e)}")
            raise LLMServiceError(f"Failed to initialize Azure OpenAI client: {str(e)}")
    
    def _format_actions(self, actions_text: str) -> List[Dict[str, Any]]:
        """Format actions text into a data structure.
        
        Args:
            actions_text (str): Text with actions in JSON format.
            
        Returns:
            List[Dict[str, Any]]: List of actions.
            
        Raises:
            LLMServiceError: If JSON parsing fails.
        """
        try:
            try:
                result = json.loads(actions_text.strip())
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and "actions" in result:
                    return result["actions"]
            except json.JSONDecodeError:
                pass
                
            # Extract JSON from response
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
            
            # Try to find JSON object
            json_start = actions_text.find("{")
            json_end = actions_text.rfind("}")
            
            if json_start != -1 and json_end != -1:
                json_str = actions_text[json_start:json_end+1]
                try:
                    result = json.loads(json_str)
                    if isinstance(result, dict) and "actions" in result:
                        return result["actions"]
                    elif isinstance(result, dict):
                        return [result]
                except:
                    pass
            
            logger.warning(f"Failed to parse JSON from response: {actions_text}")
            return []
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Error parsing JSON response from LLM: {str(e)}")
            logger.debug(f"LLM response: {actions_text}")
            raise LLMServiceError(f"Failed to parse JSON actions: {str(e)}")
    
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate a completion for the given prompt.
        
        Args:
            prompt (str): User prompt.
            system_prompt (Optional[str]): Optional system prompt. If not provided, uses default.
            
        Returns:
            str: Generated completion.
            
        Raises:
            LLMServiceError: When there's an error communicating with Azure OpenAI API.
        """
        try:
            logger.debug(f"Sending completion request to Azure OpenAI")
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                raise LLMServiceError("Empty response from Azure OpenAI API")
            
            message_content = response.choices[0].message.content
            
            if not message_content:
                raise LLMServiceError("Empty message content from Azure OpenAI API")
            
            logger.debug(f"Received completion response")
            return message_content
            
        except Exception as e:
            logger.error(f"Error generating completion through Azure OpenAI: {str(e)}")
            raise LLMServiceError(f"Failed to get completion from Azure OpenAI API: {str(e)}")
    
    def generate_actions(self, query: str) -> List[Dict[str, Any]]:
        """Generate list of actions based on query using Azure OpenAI API.
        
        Args:
            query (str): Natural language query.
            
        Returns:
            List[Dict[str, Any]]: List of actions.
            
        Raises:
            LLMServiceError: When there's an error communicating with Azure OpenAI API.
        """
        try:
            user_prompt = f"""
            User request: {query}
            
            Please create an action plan to fulfill this request.
            
            Response format:
            [
                {{
                    "type": "create_file", // Action type (create_file, modify, delete, info)
                    "path": "path/to/file.txt", // File path
                    "content": "file content", // File content (for create_file and modify)
                    "description": "Action description" // Brief action description
                }},
                // Other actions...
            ]
            """
            
            logger.debug(f"Sending request to Azure OpenAI: {query}")
            
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            if not response or not response.choices or len(response.choices) == 0:
                raise LLMServiceError("Empty response from Azure OpenAI API")
            
            message_content = response.choices[0].message.content
            
            if not message_content:
                raise LLMServiceError("Empty message content from Azure OpenAI API")
            
            logger.debug(f"Received response: {message_content}")
            
            actions = self._format_actions(message_content)
            logger.debug(f"Generated {len(actions)} actions from Azure OpenAI")
            
            if len(actions) == 0:
                logger.warning("Failed to parse actions from LLM response")
                logger.debug(f"Full response: {message_content}")
                
                return [{
                    "type": "info",
                    "path": "response.txt",
                    "content": message_content,
                    "description": "LLM response (could not parse as an action plan)"
                }]
            
            return actions
            
        except Exception as e:
            logger.error(f"Error generating actions through Azure OpenAI: {str(e)}")
            raise LLMServiceError(f"Failed to get response from Azure OpenAI API: {str(e)}")


def create_llm_service() -> LLMService:
    """Create LLM service instance.
    
    Returns:
        LLMService: LLM service instance.
        
    Raises:
        LLMServiceError: When there's an error creating LLM service.
    """
    try:
        logger.info("Using Azure OpenAI LLM service")
        return AzureOpenAIService()
    except Exception as e:
        error_msg = f"Error creating Azure OpenAI LLM service: {str(e)}"
        logger.error(error_msg)
        raise LLMServiceError(error_msg)
