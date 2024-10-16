import json
import logging
from collections import defaultdict
from typing import Any

from github_client import GitHubAPIClient

from helpers.constants import (map_user, unique_user_emails,
                               user_to_external_users)

github_repo = "Hello-World"
github_owner = "octocat"

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def _analyze_commits_per_user(client, owner, repo):
    branch = client.get_default_branch(owner, repo)
    logging.info(f"Analyzing commits on the default branch: {branch}")

    commits = client.get_commits(owner, repo, branch)
    logging.info(f"Found {len(commits)} commits on the {branch} branch")

    commits_per_user = defaultdict(dict)

    for commit in commits:
        author = commit["author"]["login"]
        commits_per_user[author]["login"] = author
        commits_per_user[author].setdefault("commits", []).append(
            f"https://github.com/{author}/{repo}/commits/{commit['sha']}"
        )
        commits_per_user[author]["total_commits"] = (
            commits_per_user[author].setdefault("total_commits", 0) + 1
        )
        commits_per_user[author]["comment_count"] = commit["commit"]["comment_count"]
        commits_per_user[author]["message"] = commit["commit"]["message"]

    return commits_per_user


def _get_commits_per_user_in_repo(owner, repo):
    logging.info(f"Analyzing repository: {owner}/{repo}")
    client = GitHubAPIClient()

    try:
        commits_per_user = _analyze_commits_per_user(client, owner, repo)

        # Print the results to the console as well
        print("\nCommits per user:")
        for commit_info in commits_per_user.items():
            print(json.dumps(commit_info))

        # Return the commits_per_user dictionary
        return commits_per_user

    except Exception as e:
        logging.exception("An error occurred during analysis")
        print(f"An error occurred during analysis: {str(e)}")
        print("Please check your token, owner, and repo name, and try again.")
        return None  # Return None in case of an error


def _extract_comment_info(pr_comments):
    comments = []
    for comment in pr_comments:
        if comment["body"] is not None or comment["body"] != "":
            comments.append(
                {
                    "author": comment["user"]["login"],
                    "comment_url": comment["html_url"],
                    "comment_body": comment["body"],
                }
            )
    return comments


def _extract_pr_info(pr) -> dict:
    return {
        "number": pr["number"],
        "pr_title": pr["title"],
        "pr_url": pr["html_url"],
        "author": pr["user"]["login"],
        "body": pr["body"],
    }


def initialize_github_hack():
    contributors = list_repo_contributors(owner="octocat", repo="Hello-World")
    print(contributors)
    for username in contributors:
        map_user(username)


def list_repo_contributors(owner: str, repo: str) -> Any:
    client = GitHubAPIClient()
    all_contributors = client.list_contributors(owner, repo)
    print(f"Found {len(all_contributors)} contributors in {owner}/{repo}")
    return all_contributors


def get_all_pull_requests_data(owner: str, repo: str) -> Any:
    client = GitHubAPIClient()
    raw_prs: Any = client.fetch_PR_data(owner, repo)
    prs = [_extract_pr_info(pr) for pr in raw_prs]

    print(f"Found {len(prs)} pull requests in {owner}/{repo}")
    return prs


def get_pull_requests_per_user(owner: str, repo: str) -> Any:
    client = GitHubAPIClient()
    raw_prs: Any = client.fetch_PR_data(owner, repo)
    extracted_pr_info = [_extract_pr_info(pr) for pr in raw_prs]
    prs_by_author = defaultdict(dict)
    for pr_info in extracted_pr_info:
        author = pr_info["author"]
        prs_by_author[author]["author"] = author
        prs_by_author[author].setdefault("pull_requests", []).append(pr_info)
    return prs_by_author


def get_pull_requests_by_author(owner: str, repo: str, author: str) -> Any:
    # Get a list of external user ids mapped to the author
    external_usernames = user_to_external_users[author]

    if not external_usernames:
        logging.warning(f"No external usernames found for author: {author}")
        return None

    client = GitHubAPIClient()
    raw_prs: Any = client.fetch_PR_data(owner, repo)

    pr_list = []
    for user in external_usernames:
        raw_prs_by_author = [
            pr for pr in raw_prs if pr["user"]["login"].lower() == user.lower()
        ]
        prs_by_author = [_extract_pr_info(pr) for pr in raw_prs_by_author]
        pr_list.extend(prs_by_author)
    return pr_list


def get_commits_by_author(owner: str, repo: str, author: str) -> Any:
    # Get a list of external user ids mapped to the author
    external_usernames = user_to_external_users[author]

    if not external_usernames:
        logging.warning(f"No external usernames found for author: {author}")
        return None

    # Get commits per user in the repository
    github_data = _get_commits_per_user_in_repo(github_owner, github_repo)

    if not github_data:
        logging.warning("No GitHub data retrieved")
        return None

    # Sum up the total commits for all external usernames
    commit_info_list = []
    total_commits = 0
    for username in external_usernames:
        commit_info = github_data.get(username)
        if not commit_info:
            logging.warning(f"No commit info found for external username: {username}")
            continue
        total_commits += commit_info.get("total_commits", 0)
        commit_info_list.append(commit_info)
    return commit_info_list, total_commits


def get_github_contributions_by_author(author):
    commit_info_list, total_commits = get_commits_by_author(
        owner=github_owner, repo=github_repo, author=author
    )
    pr_list = get_pull_requests_by_author(github_owner, github_repo, author)

    return {
        "author": author,
        "total_commits": total_commits,
        "total_pull_requests": len(pr_list),
        "commits": commit_info_list,
        "pull_requests": pr_list,
    }


def get_github_contributions_by_repo(repo_owner, repo_name):
    commits_per_user = _get_commits_per_user_in_repo(repo_owner, repo_name)
    pull_requests_per_user = get_pull_requests_per_user(repo_owner, repo_name)

    if commits_per_user is None or pull_requests_per_user is None:
        logging.error("Failed to retrieve GitHub data")
        return {}

    keys = list(commits_per_user.keys()) + list(pull_requests_per_user.keys())
    for key in keys:
        map_user(key)

    github_contributions = {}
    for user in unique_user_emails:
        github_contributions[user] = {}
        # Get a list of external user ids mapped to the author
        external_usernames = user_to_external_users[user]
        commits = []
        pull_requests = []
        for external_user in external_usernames:
            if external_user in commits_per_user:
                commits.extend(commits_per_user[external_user]["commits"])
            if external_user in pull_requests_per_user:
                pull_requests.extend(
                    pull_requests_per_user[external_user]["pull_requests"]
                )
        github_contributions[user]["commits"] = commits
        github_contributions[user]["pull_requests"] = pull_requests

    return github_contributions


if __name__ == "__main__":
    author = "vijayanands@gmail.com"
    initialize_github_hack()

    # contributors = list_repo_contributors(github_owner, github_repo)
    # print(f"\nAll contributors in {github_owner}/{github_repo}:")
    # print(json.dumps(contributors, indent=2))
    #
    # prs = get_all_pull_requests_data(github_owner, github_repo)
    # print(f"\nAll pull requests in {github_owner}/{github_repo}:")
    # print(json.dumps(prs, indent=2))
    #
    # prs_by_author = get_pull_requests_by_author(github_owner, github_repo, author)
    # print(f"\nPull requests by {author}:")
    # print(json.dumps(prs_by_author, indent=2))

    contributions_by_author = get_github_contributions_by_author(author)
    print(f"\nGitHub contributions by {author}:")
    print(json.dumps(contributions_by_author, indent=2))
