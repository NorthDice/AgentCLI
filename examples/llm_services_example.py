#!/usr/bin/env python3
"""
Example of using LLM services in AgentCLI.
"""
import os
import sys
from pathlib import Path

# Add parent directory to import path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agentcli.core import (
    create_llm_service,
    load_config,
    get_llm_config,
    LLMServiceError
)

def main():
    """
    Demonstrates usage of LLM services in AgentCLI.
    """
    try:
        # Load configuration from .env file
        load_config()
        
        # Get LLM configuration
        llm_config = get_llm_config()
        
        # Print configuration info
        print(f"Using LLM service: {llm_config.get('service', 'openai')}")
        
        if llm_config.get('service') == 'azure':
            print(f"Azure Endpoint: {llm_config.get('azure_endpoint')}")
            print(f"Deployment Name: {llm_config.get('azure_deployment')}")
        else:
            print(f"OpenAI Model: {llm_config.get('model', 'gpt-4o')}")
        
        # Create LLM service
        llm_service = create_llm_service()
        
        # Generate a response for a simple prompt
        prompt = "Write a short Python function to calculate factorial."
        print("\nPrompt to LLM:", prompt)
        
        # Use generate_actions method to get a list of actions
        actions = llm_service.generate_actions(prompt)
        
        print("\nResponse from LLM (action plan):")
        for i, action in enumerate(actions, 1):
            print(f"\nAction {i}:")
            print(f"Type: {action.get('type')}")
            print(f"Path: {action.get('path')}")
            print(f"Description: {action.get('description')}")
            if 'content' in action:
                print(f"Content:\n{action.get('content')}")
        
    except LLMServiceError as e:
        print(f"LLM service error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")

if __name__ == "__main__":
    main()
