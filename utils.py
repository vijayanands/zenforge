import hashlib
import os
from collections import defaultdict
from typing import Dict, List

from llama_index.llms.openai import OpenAI

unique_user_emails = [
    "vijayanands@gmail.com",
    "vijayanands@yahoo.com",
    "vjy1970@gmail.com",
    "email2vijay@gmail.com",
]
user_to_external_users: Dict[str, List[str]] = defaultdict(list)
external_user_to_user: Dict[str, str] = defaultdict()


def map_user(external_username: str):
    hash_value = int(hashlib.md5(external_username.encode()).hexdigest(), 16)
    mapped_user_email = unique_user_emails[hash_value % len(unique_user_emails)]
    external_user_to_user[external_username] = mapped_user_email
    user_to_external_users[mapped_user_email].append(external_username)


def get_llm(**kwargs):
    """
    Factory function to create an LLM instance based on the vendor.
    """
    return OpenAI(
        temperature=kwargs.get("temperature", 0.7),
        model=kwargs.get("model", "gpt-3.5-turbo"),
        api_key=os.getenv("OPENAI_API_KEY"),  # Assumes environment variable OPENAI_API_KEY is set with your OpenAI API key.
    )
