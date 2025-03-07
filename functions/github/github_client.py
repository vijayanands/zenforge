import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests
from dotenv import load_dotenv

from utils import get_log_level

load_dotenv()


# Set up logging
logging.basicConfig(
    level=get_log_level(), format="%(asctime)s - %(levelname)s - %(message)s"
)


def get_github_auth_header() -> Dict[str, str]:
    headers = {
        "Authorization": f"token {os.getenv('GITHUB_TOKEN')}",
        "Accept": "application/vnd.github.v3+json",
    }

    return headers
headers = get_github_auth_header()


class GitHubAPIClient:
    def __init__(self):
        self.headers = headers
        self.github_owner = os.getenv("GITHUB_OWNER")
        self.github_repo = os.getenv("GITHUB_REPO")
        assert self.github_owner is not None, "GITHUB_OWNER must be set"
        assert self.github_repo is not None, "GITHUB_REPO must be set"
        self.base_path = f"repos/{self.github_owner}/{self.github_repo}"
        self.base_url = f"https://api.github.com/{self.base_path}"

    def get_github_owner(self) -> str:
        if self.github_owner is None:
            raise ValueError("GitHub owner is not set")
        return self.github_owner

    def get_github_repo(self) -> str:
        if self.github_repo is None:
            raise ValueError("GitHub repo is not set")
        return self.github_repo

    def call_github(self, url, params=None) -> Any:
        logging.debug(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        logging.debug(f"Response status code: {response.status_code}")
        if response.status_code != 200:
            logging.error(f"Error calling url: {url}, response code: {response.status_code}")
            logging.error(response.json().get("message", "No error message provided"))
            logging.error(f"Response content: {response.text}")
        return response

    def get_default_branch(self) -> str:
        response = self.call_github(self.base_url)
        if response.status_code != 200:
            logging.error(f"Error fetching repository info: {response.status_code}")
            logging.error(f"Response content: {response.text}")
            sys.exit(1)
        return response.json()["default_branch"]

    def get_commits(self, branch: str, start_date: str, end_date: str) -> Any:
        return self._fetch_from_github("commits", {"sha": branch}, start_date, end_date)

    def get_all_pull_requests(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("pulls", start_date=start_date, end_date=end_date)

    def get_pull_request_comments(self, pr_number: int, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github(f"pulls/{pr_number}/comments", start_date=start_date, end_date=end_date)

    def get_repo_activities(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("activity", start_date=start_date, end_date=end_date)

    def get_repo_contributors(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("contributors", start_date=start_date, end_date=end_date)

    def get_all_commit_comments(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("comments", start_date=start_date, end_date=end_date)

    def get_issues_data(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Any:
        return self._fetch_from_github("issues", start_date=start_date, end_date=end_date)

    def list_contributors(self) -> Any:
        all_contributors: Set[str] = set()

        # Fetch commit contributors
        commit_contributors = self.get_repo_contributors()
        all_contributors.update(
            contributor["login"] for contributor in commit_contributors
        )

        # Fetch comment contributors
        comment_contributors = self.get_all_commit_comments()
        all_contributors.update(
            contributor["user"]["login"] for contributor in comment_contributors
        )

        # Fetch pull request contributors
        pr_contributors = self.get_all_pull_requests()
        all_contributors.update(
            contributor["user"]["login"] for contributor in pr_contributors
        )

        logging.debug(f"Fetched {len(all_contributors)} unique contributors")
        return list(all_contributors)

    def _fetch_from_github(self, path: str, additional_params: Optional[Dict[str, Any]] = None,
                           start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{path}"
        params: Dict[str, Any] = {"per_page": 100}
        if additional_params is not None:
            params.update(additional_params)

        if start_date:
            params["since"] = start_date  # Assuming the string is already in ISO format
        if end_date:
            params["until"] = end_date  # Assuming the string is already in ISO format

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

            # Clear params for subsequent requests to avoid duplicate query parameters
            params = {}

        logging.debug(f"Fetched {len(all_items)} {path}")
        return all_items
