"""Configuration module for managing application settings."""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from agentcli.utils.logging import logger


class Config:
    """Class for managing application settings."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize application configuration."""
        if Config._initialized:
            return
            
        # Load environment variables from .env file
        env_path = Path(os.getcwd()) / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # LLM configuration
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        
        # OpenAI configuration
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4")
        
        # Azure OpenAI configuration
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        self.azure_openai_api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.azure_openai_api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")
        self.azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
        self.azure_openai_model_name = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-4")
        
        # Validate settings
        self._validate_config()
        
        Config._initialized = True
        logger.debug("Configuration initialized")
    
    def _validate_config(self):
        """Validate configuration correctness."""
        provider = self.llm_provider
        
        if provider not in ["openai", "azure", "mock"]:
            logger.warning(f"Unsupported LLM_PROVIDER: {provider}. Falling back to 'mock'.")
            self.llm_provider = "mock"
        
        if provider == "openai" and not self.openai_api_key:
            logger.warning("OPENAI_API_KEY is not set. Using MockLLMService fallback.")
            self.llm_provider = "mock"
        
        if provider == "azure" and (not self.azure_openai_api_key or not self.azure_openai_endpoint):
            logger.warning("Missing required parameters for Azure OpenAI. Using MockLLMService fallback.")
            self.llm_provider = "mock"
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Return LLM configuration depending on provider.
        
        Returns:
            Dict[str, Any]: LLM configuration.
        """
        provider = self.llm_provider
        
        if provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model_name": self.openai_model_name,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens
            }
        elif provider == "azure":
            return {
                "provider": "azure",
                "api_key": self.azure_openai_api_key,
                "endpoint": self.azure_openai_endpoint,
                "api_version": self.azure_openai_api_version,
                "deployment": self.azure_openai_deployment,
                "model_name": self.azure_openai_model_name,
                "temperature": self.llm_temperature,
                "max_tokens": self.llm_max_tokens
            }
        else:
            return {
                "provider": "mock"
            }


# Export a Config instance for global access
config = Config()
