import sys
from typing import Any, Dict, List, Set

import requests
from dotenv import load_dotenv

from helpers.auth import get_github_auth_header
from helpers.constants import logging  # Add this import

load_dotenv()
headers = get_github_auth_header()


class GitHubAPIClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = headers

    def api_call(self, url, params=None):
        logging.info(f"Making API call to: {url}")
        response = requests.get(url, headers=self.headers, params=params)
        logging.info(f"Response status code: {response.status_code}")
        return response

    def get_default_branch(self, owner, repo):
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self.api_call(url)
        if response.status_code != 200:
            logging.error(f"Error fetching repository info: {response.status_code}")
            logging.error(f"Response content: {response.text}")
            sys.exit(1)
        return response.json()["default_branch"]

    def get_commits(self, owner, repo, branch):
        commits = []
        page = 1
        url = f"{self.base_url}/repos/{owner}/{repo}/commits"
        while True:
            params = {"sha": branch, "page": page, "per_page": 100}
            response = self.api_call(url, params)
            if response.status_code != 200:
                logging.error(f"Error fetching commits: {response.status_code}")
                logging.error(f"Response content: {response.text}")
                break
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
        return commits

    def list_repo_activity(self, owner: str, repo: str) -> Any:
        url = f"{self.base_url}/repos/{owner}/{repo}/activity"
        params: Dict[str, Any] = {"per_page": 100}
        all_activity = []
        while url:
            response = self.api_call(url, params)
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

    def list_repo_contributors(self, owner: str, repo: str) -> Any:
        url = f"{self.base_url}/repos/{owner}/{repo}/contributors"
        params: Dict[str, Any] = {"per_page": 100}
        all_contributors = []
        while url:
            response = self.api_call(url, params)
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

    def fetch_issues_data(self, owner: str, repo: str) -> Any:
        url = f"{self.base_url}/repos/{owner}/{repo}/issues"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_issues = []
        while url:
            response = self.api_call(url, params)
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

    def fetch_PR_data(self, owner: str, repo: str) -> Any:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        params: Dict[str, Any] = {"state": "all", "per_page": 100}
        all_prs = []
        while url:
            response = self.api_call(url, params)
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

    def fetch_PR_comments(self, owner: str, repo: str, pr_number: int) -> Any:
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        params: Dict[str, Any] = {"per_page": 100}
        all_comments = []
        while url:
            response = self.api_call(url, params)
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

    def list_contributors(self, owner: str, repo: str) -> Any:
        all_contributors: Set[str] = set()

        # Fetch commit contributors
        commit_contributors = self._fetch_contributors(owner, repo, "contributors")
        all_contributors.update(
            contributor["login"] for contributor in commit_contributors
        )

        # Fetch comment contributors
        comment_contributors = self._fetch_contributors(owner, repo, "comments")
        all_contributors.update(
            contributor["user"]["login"] for contributor in comment_contributors
        )

        # Fetch pull request contributors
        pr_contributors = self._fetch_contributors(owner, repo, "pulls")
        all_contributors.update(
            contributor["user"]["login"] for contributor in pr_contributors
        )

        print(f"Fetched {len(all_contributors)} unique contributors")
        return list(all_contributors)

    def _fetch_contributors(
        self, owner: str, repo: str, contribution_type: str
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/repos/{owner}/{repo}/{contribution_type}"
        params: Dict[str, Any] = {"per_page": 100, "state": "all"}
        all_items = []

        while url:
            response = self.api_call(url, params)
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
