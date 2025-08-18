#!/usr/bin/env python3
"""
Example of direct usage of the Azure OpenAI API.
"""
import os
import sys
import dotenv
from openai import AzureOpenAI

def main():
    """
    Demonstrates direct usage of the Azure OpenAI API.
    """
    try:
        # Load environment variables from .env file
        dotenv.load_dotenv()
        
        # Get parameters from environment variables
        api_key = os.getenv('AZURE_OPENAI_API_KEY')
        endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        deployment_name = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME')
        api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2023-05-15')
        
        if not all([api_key, endpoint, deployment_name]):
            print("Error: Not all parameters are available in the .env file.")
            print("Make sure AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and AZURE_OPENAI_DEPLOYMENT_NAME are set.")
            return
        
        print("Azure OpenAI Parameters:")
        print(f"- Endpoint: {endpoint}")
        print(f"- Deployment: {deployment_name}")
        print(f"- API Version: {api_version}")
        
        # Create the Azure OpenAI client
        client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=api_key,
        )
        
        # Send a request to the API
        prompt = "Write a short Python function to calculate factorial."
        
        print("\nSending prompt:", prompt)
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful programmer assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        # Print the response
        if response.choices and len(response.choices) > 0:
            answer = response.choices[0].message.content
            print("\nResponse from Azure OpenAI:")
            print(answer)
        else:
            print("Error: Empty response from the API")
        
    except Exception as e:
        print(f"Error using Azure OpenAI API: {e}")

if __name__ == "__main__":
    main()
