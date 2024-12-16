import os
from llama_index.llms.openai import OpenAI
from helpers import import_env

def get_llm(**kwargs):
    """
    Factory function to create an LLM instance based on the vendor.
    """
    return OpenAI(
        temperature=kwargs.get("temperature", 0.7),
        model=kwargs.get("model", "gpt-3.5-turbo"),
        api_key=os.getenv("OPENAI_API_KEY"),  # Assumes environment variable OPENAI_API_KEY is set with your OpenAI API key.
    )
