import os
import sys
from typing import Any, Dict, List, Set

# Add the parent directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

import requests
from dotenv import load_dotenv

from helpers import constants
from helpers.auth import get_github_auth_header

load_dotenv()
headers = get_github_auth_header()


class GitHubAPIClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = headers
        self.github_owner = os.getenv("GITHUB_OWNER")
        self.github_repo = os.getenv("GITHUB_REPO")

    def get_github_owner(self):
        return self.github_owner

    def get_github_repo(self):
        return self.github_repo

    def api_call(self, url, params=None):
        print(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        print(f"Response status code: {response.status_code}")
        return response

    def get_default_branch(self):
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}"
        response = self.api_call(url)
        if response.status_code != 200:
            print(f"Error fetching repository info: {response.status_code}")
            print(f"Response content: {response.text}")
            sys.exit(1)
        return response.json()["default_branch"]

    def get_commits(self, branch):
        commits = []
        page = 1
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/commits"
        while True:
            params = {"sha": branch, "page": page, "per_page": 100}
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching commits: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
        return commits

    def list_repo_activity(self) -> Any:
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/activity"
        params: Dict[str, Any] = {"per_page": 100}
        all_activity = []
        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching activity: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            activities = response.json()
            all_activity.extend(activities)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_activity)} repository activities")
        return all_activity

    def list_repo_contributors(self) -> Any:
        url = (
            f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/contributors"
        )
        params: Dict[str, Any] = {"per_page": 100}
        all_contributors = []
        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching contributors: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            contributors = response.json()
            all_contributors.extend(contributors)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_contributors)} contributors")
        return all_contributors

    def fetch_issues_data(self) -> Any:
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/issues"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_issues = []
        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching issues: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            issues = response.json()
            all_issues.extend(issues)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_issues)} issues")
        return all_issues

    def fetch_PR_data(self) -> Any:
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/pulls"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_prs = []
        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching PRs: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            prs = response.json()
            all_prs.extend(prs)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_prs)} pull requests")
        return all_prs

    def fetch_PR_comments(self, pr_number: int) -> Any:
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/pulls/{pr_number}/comments"
        params: Dict[str, Any] = {"per_page": 100}
        all_comments = []
        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching PR comments: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            comments = response.json()
            all_comments.extend(comments)
            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_comments)} comments for PR #{pr_number}")
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
        url = f"{self.base_url}/repos/{self.github_owner}/{self.github_repo}/{contribution_type}"
        params: Dict[str, Any] = {"per_page": 100, "state": "all"}
        all_items = []

        while url:
            response = self.api_call(url, params)
            if response.status_code != 200:
                print(f"Error fetching {contribution_type}: {response.status_code}")
                print(f"Response content: {response.text}")
                break
            items = response.json()

            # Extract comment text if fetching comments
            if contribution_type == "comments":
                for item in items:
                    item["comment_text"] = item.get("body", "")

            all_items.extend(items)

            # Check for pagination
            url = response.links.get("next", {}).get("url")

        print(f"Fetched {len(all_items)} {contribution_type}")
        return all_items
