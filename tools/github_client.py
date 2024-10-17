import os
import sys
from typing import Any, DefaultDict, Dict, List

import requests
from dotenv import load_dotenv

from tools.auth import get_github_auth_header

load_dotenv()
headers = get_github_auth_header()


class GitHubAPIClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = headers
        self.github_owner = os.getenv("GITHUB_OWNER")
        self.github_repo = os.getenv("GITHUB_REPO")
        self.base_url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}"

    def get_github_owner(self):
        return self.github_owner

    def get_github_repo(self):
        return self.github_repo

    def call_github(self, url, params=None):
        print(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        print(f"Response status code: {response.status_code}")
        return response

    def get_default_branch(self):
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}"
        response = self.call_github(url)
        if response.status_code != 200:
            print(f"Error fetching repository info: {response.status_code}")
            print(f"Response content: {response.text}")
            sys.exit(1)
        return response.json()["default_branch"]

    def get_commits(self, branch):
        return self._fetch_from_github("commits", {"sha": branch})

    def get_all_pulls(self) -> Any:
        return self._fetch_from_github("pulls")

    def get_PR_comments(self, pr_number: int) -> Any:
        return self._fetch_from_github(f"pulls/{pr_number}/comments")

    def get_all_contributors(self) -> Any:
        return self._fetch_from_github("contributors")

    def get_all_commit_comments(self) -> Any:
        return self._fetch_from_github("comments")

    def _fetch_from_github(
        self, path: str, additional_params: Dict[str, str] = DefaultDict
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{path}"
        params: Dict[str, Any] = {"per_page": 100, "state": "all"}
        for key, value in additional_params:
            params[key] = value
        all_items = []

        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                print(f"Error fetching {path}: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            items = response.json()
            all_items.extend(items)

            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_items)} {path}")
        return all_items
