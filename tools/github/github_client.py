import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

import requests
from dotenv import load_dotenv

load_dotenv()


# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
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
        print(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        print(f"Response status code: {response.status_code}")
        return response

    def get_default_branch(self) -> str:
        response = self.call_github(self.base_url)
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
        since: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{path}"
        params: Dict[str, Any] = {"per_page": 100}
        params.update(additional_params)

        if since:
            params["since"] = since.isoformat()

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

        print(f"Fetched {len(all_items)} {path}")
        return all_items

    def list_repo_activity(self) -> Any:
        url = f"{self.base_url}/activity"
        params: Dict[str, Any] = {"per_page": 100}
        all_activity = []
        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching activity: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            activities = response.json()
            all_activity.extend(activities)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_activity)} repository activities")
        return all_activity

    def list_repo_contributors(self) -> Any:
        url = f"{self.base_url}/contributors"
        params: Dict[str, Any] = {"per_page": 100}
        all_contributors = []
        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching contributors: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            contributors = response.json()
            all_contributors.extend(contributors)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_contributors)} contributors")
        return all_contributors

    def fetch_issues_data(self) -> Any:
        url = f"{self.base_url}/issues"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_issues = []
        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching issues: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            issues = response.json()
            all_issues.extend(issues)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_issues)} issues")
        return all_issues


    def fetch_PR_data(self) -> Any:
        url = f"{self.base_url}/pulls"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_prs = []
        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching PRs: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            prs = response.json()
            all_prs.extend(prs)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_prs)} pull requests")
        return all_prs


    def fetch_PR_comments(self, pr_number: int) -> Any:
        url = f"{self.base_url}/pulls/{pr_number}/comments"
        params: Dict[str, Any] = {"per_page": 100}
        all_comments = []
        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching PR comments: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            comments = response.json()
            all_comments.extend(comments)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_comments)} comments for PR #{pr_number}")
        return all_comments

    def fetch_pr_comments(self, start_date, end_date=None, token=None):
        base_url = f"{self.base_url}/pulls/comments"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        params = {"since": start_date, "per_page": 100}

        all_comments = []
        page = 1

        while True:
            params["page"] = page
            response = requests.get(base_url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}")
                print(response.json().get("message", "No error message provided"))
                break

            data = response.json()
            if not data:
                break

            # If end_date is provided, filter comments within the end_date
            if end_date:
                for comment in data:
                    comment_date = comment["created_at"]
                    if comment_date <= end_date:
                        all_comments.append(comment)
                    else:
                        break
            else:
                all_comments.extend(data)

            if len(data) < 100:
                break
            page += 1

        return all_comments

    def fetch_commits(self, start_date, end_date=None, token=None):
        base_url = f"{self.base_url}/commits"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        params = {"since": start_date, "per_page": 100}
        if end_date:
            params["until"] = end_date

        all_commits = []
        page = 1

        while True:
            params["page"] = page
            response = requests.get(base_url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}")
                print(response.json().get("message", "No error message provided"))
                break

            data = response.json()
            if not data:
                break

            all_commits.extend(data)
            if len(data) < 100:
                break
            page += 1

        return all_commits

    def fetch_commit_comments(self, start_date, end_date=None, token=None):
        base_url = f"{self.base_url}/comments"
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"

        params = {"since": start_date, "per_page": 100}

        all_comments = []
        page = 1

        while True:
            params["page"] = page
            response = requests.get(base_url, headers=headers, params=params)

            if response.status_code != 200:
                print(f"Error fetching data: {response.status_code}")
                print(response.json().get("message", "No error message provided"))
                break

            data = response.json()
            if not data:
                break

            # If end_date is provided, filter comments within the end_date
            if end_date:
                for comment in data:
                    comment_date = comment["created_at"]
                    if comment_date <= end_date:
                        all_comments.append(comment)
                    else:
                        break
            else:
                all_comments.extend(data)

            if len(data) < 100:
                break
            page += 1

        return all_comments


    def list_contributors(self) -> Any:
        all_contributors: Set[str] = set()

        # Fetch commit contributors
        commit_contributors = self._fetch_contributors("contributors")
        all_contributors.update(
            contributor["login"] for contributor in commit_contributors
        )

        # Fetch comment contributors
        comment_contributors = self._fetch_contributors("comments")
        all_contributors.update(
            contributor["user"]["login"] for contributor in comment_contributors
        )

        # Fetch pull request contributors
        pr_contributors = self._fetch_contributors("pulls")
        all_contributors.update(
            contributor["user"]["login"] for contributor in pr_contributors
        )

        print(f"Fetched {len(all_contributors)} unique contributors")
        return list(all_contributors)

    def _fetch_contributors(self, contribution_type: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/{contribution_type}"
        params: Dict[str, Any] = {"per_page": 100, "state": "all"}
        all_items = []

        while url:
            response = self.call_github(url, params)
            if response.status_code != 200:
                logging.error(
                    f"Error fetching {contribution_type}: {response.status_code}"
                )
                logging.error(f"Response content: {response.text}")
                break
            items = response.json()
            all_items.extend(items)

            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_items)} {contribution_type}")
        return all_items
