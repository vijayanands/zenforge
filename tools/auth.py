import base64
import os
from typing import Dict


def base64_encode_string(input_string: str) -> str:
    """
    Encode a string to base64.

    :param input_string: The string to encode
    :return: The base64 encoded string
    """
    # Convert the string to bytes
    input_bytes = input_string.encode("utf-8")

    # Perform base64 encoding
    encoded_bytes = base64.b64encode(input_bytes)

    # Convert the result back to a string
    encoded_string = encoded_bytes.decode("utf-8")

    return encoded_string


def get_basic_auth_header(username: str, password: str) -> str:
    auth_string = f"{username}:{password}"
    return f"Basic {base64_encode_string(auth_string)}"


def get_headers(username: str, api_token: str) -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Authorization": get_basic_auth_header(username, api_token),
    }
    return headers


def get_github_auth_header() -> Dict[str, str]:
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }

    return headers
