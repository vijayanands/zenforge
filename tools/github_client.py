import os
import sys
from typing import Any, DefaultDict, Dict, List, Optional
from datetime import datetime

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
        assert self.github_owner is not None, "GITHUB_OWNER must be set"
        assert self.github_repo is not None, "GITHUB_REPO must be set"
        self.base_url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}"

    def get_github_owner(self) -> str:
        if self.github_owner is None:
            raise ValueError("GitHub owner is not set")
        return self.github_owner

    def get_github_repo(self) -> str:
        if self.github_repo is None:
            raise ValueError("GitHub repo is not set")
        return self.github_repo

    def call_github(self, url, params=None) -> Any:
        print(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        print(f"Response status code: {response.status_code}")
        return response

    def get_default_branch(self) -> str:
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}"
        response = self.call_github(url)
        if response.status_code != 200:
            print(f"Error fetching repository info: {response.status_code}")
            print(f"Response content: {response.text}")
            sys.exit(1)
        return response.json()["default_branch"]

    def get_commits(self, branch: str, since: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("commits", {"sha": branch}, since)

    def get_all_pulls(self, since: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("pulls", since=since)

    def get_PR_comments(self, pr_number: int, since: Optional[datetime] = None) -> Any:
        return self._fetch_from_github(f"pulls/{pr_number}/comments", since=since)

    def get_all_contributors(self, since: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("contributors", since=since)

    def get_all_commit_comments(self, since: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("comments", since=since)

    def _fetch_from_github(
        self, 
        path: str, 
        additional_params: Dict[str, Any] = {},
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{path}"
        params: Dict[str, Any] = {"per_page": 100, "state": "all"}
        params.update(additional_params)

        if since:
            params['since'] = since.isoformat()

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
