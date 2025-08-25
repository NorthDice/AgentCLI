"""
Command for checking LLM service configuration
"""
import os
import click
import json
from typing import Optional

from dotenv import load_dotenv
from agentcli.core import get_llm_service, LLMServiceError


@click.command()
@click.option('--test', is_flag=True, help='Test connection to LLM service')
def llm_config(test):
    """Check LLM service configuration."""
    load_dotenv()
    
    config = {
        "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
        "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT"),
        "api_version": os.environ.get("AZURE_OPENAI_API_VERSION"),
        "deployment": os.environ.get("AZURE_OPENAI_DEPLOYMENT"),
        "model_name": os.environ.get("AZURE_OPENAI_MODEL_NAME")
    }
    
    click.echo("Current Azure OpenAI configuration:")
    if config["api_key"]:
        config["api_key"] = f"{config['api_key'][:5]}...{config['api_key'][-5:]}"
    click.echo(json.dumps(config, indent=2, ensure_ascii=False))
    
    if test:
        click.echo("\nTesting connection to Azure OpenAI...")
        try:
            service = get_llm_service()
            
            test_query = "Respond with a simple 'OK' if you are working."
            click.echo(f"Query: {test_query}")
            
            actions = service.generate_actions(test_query)
            
            click.echo(f"\nReceived {len(actions)} actions from LLM")
            for i, action in enumerate(actions, 1):
                click.echo(f"Action {i}: {action.get('type')} - {action.get('description')}")
            
            click.echo("\n✅ Connection successfully established!")
        except LLMServiceError as e:
            click.echo(f"\n❌ Error connecting to LLM service: {e}", err=True)
