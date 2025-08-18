import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from agentcli.core import (
    create_llm_service,
    AzureOpenAIService,
    LLMServiceError
)


def main():
    """
    Demonstrates the usage of the Azure OpenAI LLM service.
    """
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Print configuration info
        print("Azure OpenAI Parameters:")
        print(f"- Endpoint: {os.getenv('AZURE_OPENAI_ENDPOINT')}")
        print(f"- Deployment: {os.getenv('AZURE_OPENAI_DEPLOYMENT')}")
        print(f"- API Version: {os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')}")
        print(f"- Model Name: {os.getenv('AZURE_OPENAI_MODEL_NAME', 'gpt-4')}")
        
        # Create the LLM service
        print("\nCreating Azure OpenAI LLM service...")
        llm_service = create_llm_service()
        print(f"Service type: {type(llm_service).__name__}")
        
        # Generate an action plan
        prompt = "Create a simple Python function to calculate factorial"
        print(f"\nSending prompt: {prompt}")
        
        actions = llm_service.generate_actions(prompt)
        
        print(f"\nReceived action plan ({len(actions)} actions):")
        
        if len(actions) == 0:
            print("Failed to get actions from the LLM.")
        
        for i, action in enumerate(actions, 1):
            print(f"\nAction {i}:")
            print(f"Type: {action.get('type')}")
            print(f"Path: {action.get('path')}")
            print(f"Description: {action.get('description')}")
            if 'content' in action:
                print("Content:")
                print("-" * 40)
                print(action.get('content'))
                print("-" * 40)
        
    except LLMServiceError as e:
        print(f"LLM service error: {e}")
    except Exception as e:
        print(f"Unknown error: {e}")


if __name__ == "__main__":
    main()
