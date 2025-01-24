import os
import re
from typing import Any, Dict, List

import requests
from bs4 import BeautifulSoup, Comment

from functions.llamaindex_summarization import summarize_data

from constants import unique_user_emails
from tools.auth import get_headers


# atlassian_base_url = https://openmrs.atlassian.net/wiki/spaces/docs/overview
atlassian_base_url = "https://vijayanands.atlassian.net"
atlassian_username = "vijayanands@gmail.com"
atlassian_api_token = os.getenv("ATLASSIAN_API_TOKEN")
confluence_space_key = "SD"


def get_spaces(base_url, username, api_token) -> None or List[Dict[str, Any]]:
    url = f"{base_url}/wiki/api/v2/spaces"
    response = requests.get(url, headers=get_headers(username, api_token))
    if response.status_code == 200:
        data = response.json()
        return data["results"]
    return None


def get_page_content(base_url, page_id, username, api_token) -> str or None:
    headers = get_headers(username, api_token)
    # Use the expand parameter to include body content
    url = f"{base_url}/wiki/api/v2/pages/{page_id}?body-format=storage"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        page_data = response.json()
        page_body = page_data.get("body", {}).get("storage", {}).get("value", "")
        return page_body
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def get_space_id(base_url, space_key, username, api_token) -> int or None:
    api_endpoint = f"{base_url}/wiki/api/v2/spaces"

    headers = get_headers(username, api_token)

    params = {"key": space_key, "status": "current"}

    response = requests.get(api_endpoint, headers=headers, params=params)

    if response.status_code == 200:
        spaces = response.json()["results"]
        if spaces:
            return spaces[0]["id"]
        else:
            print(f"No space found with key '{space_key}'")
            return None
    else:
        print(f"Error fetching space ID: {response.status_code}")
        print(response.text)
        return None


def clean_confluence_content(html_content):
    # Parse the HTML content
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script and style elements
    for script in soup(["script", "style"]):
        script.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda string: isinstance(string, Comment)):
        comment.extract()

    # Extract text from remaining tags
    text = soup.get_text()

    # Break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())

    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

    # Drop blank lines
    text = "\n".join(chunk for chunk in chunks if chunk)

    # Remove excessive newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text


def get_confluence_contributions(
    base_url, username, api_token, space_key, target_username
):
    space_id = get_space_id(base_url, space_key, username, api_token)

    headers = get_headers(username, api_token)
    api_endpoint = f"{base_url}/wiki/api/v2/spaces/{space_id}/pages"
    params = {
        "limit": 100,  # Adjust as needed
        "creator": target_username,
        "status": "current",
    }

    response = requests.get(api_endpoint, headers=headers, params=params)

    pages_dict = {}

    if response.status_code == 200:
        pages = response.json()["results"]
        print(f"Pages created by {target_username} in space {space_key}:")
        for page in pages:
            page_id = page["id"]
            raw_content = get_page_content(base_url, page_id, username, api_token)
            cleaned_content = clean_confluence_content(raw_content)
            print(f"Title: {page['title']}")
            print(f"ID: {page_id}")
            print(f"Created: {page['createdAt']}")
            print(f"{atlassian_base_url}/wiki{page['_links']['webui']}")
            print("Page Content:")
            print(cleaned_content)
            pages_dict[page_id] = {
                "title": page["title"],
                "created_at": page["createdAt"],
                "space_key": space_key,
                "author": target_username,
                "content": cleaned_content,
                "page_link": f"{atlassian_base_url}/wiki{page['_links']['webui']}",
            }

        return pages_dict
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def get_confluence_contributions_by_author(author: str):
    confluence_data = get_confluence_contributions(
        atlassian_base_url,
        atlassian_username,
        atlassian_api_token,
        confluence_space_key,
        author,
    )
    for key, doc in confluence_data.items():
        if not isinstance(doc, dict):
            raise ValueError(
                f"Each value in the dictionary must be a dictionary, found {type(doc)} for key {key}"
            )
        summary = summarize_data(doc, id=key)
        doc["summary"] = summary
    return confluence_data

def get_confluence_contributions_by_author_in_the_last_week(author: str):
    pass

def get_confluence_contributions_per_user():
    confluence_contributions = {}
    for user in unique_user_emails:
        confluence_data = get_confluence_contributions_by_author(user)
        confluence_contributions[user] = confluence_data
    return confluence_contributions


def get_confluence_pages_space(base_url, username, api_token, space_id):
    api_endpoint = f"{base_url}/wiki/api/v2/spaces/{space_id}/pages"

    headers = get_headers(username, api_token)
    params = {"limit": 100, "status": "current"}  # Adjust as needed

    response = requests.get(api_endpoint, headers=headers, params=params)

    if response.status_code == 200:
        pages = response.json()["results"]
        return pages
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


# if __name__ == "__main__":
#     base_url = "https://vijayanands.atlassian.net/wiki"
#     username = "vijayanands@gmail.com"
#     api_token = os.getenv("ATLASSIAN_API_TOKEN")
#     space_key = "SD"
#     page_title = "Conversational AI For Customer Service"
#     # spaces = get_spaces(base_url, username, api_token)
#     # get_page_content_v2(base_url, page_id, username, api_token)
#
# if __name__ == "__main__":
#     confluence_data = get_confluence_contributions_by_author(author="vijayanands@gmail.com")
#     print(json.dumps(confluence_data, indent=2))
