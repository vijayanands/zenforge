import json
from collections import defaultdict
from typing import Any

from github_client import GitHubAPIClient

client = GitHubAPIClient()


def _extract_pr_info(pr: Any) -> Any:
    return {
        "number": pr["number"],
        "pr_title": pr["title"],
        "pr_url": pr["html_url"],
        "author": pr["user"]["login"],
        "body": pr["body"],
    }


def get_all_PRs_by_user() -> Any:
    raw_prs: Any = client.get_all_pulls()
    extracted_pr_info = [_extract_pr_info(pr) for pr in raw_prs]
    prs_by_author = defaultdict(dict)
    for pr_info in extracted_pr_info:
        author = pr_info["author"]
        prs_by_author[author]["author"] = author
        prs_by_author[author].setdefault("pull_requests", []).append(pr_info)
    return prs_by_author


def get_pull_requests_by_author(author: str) -> Any:
    return get_all_PRs_by_user()[author].get("pull_requests", [])


def _extract_commits_by_user() -> Any:
    branch = client.get_default_branch()
    print(f"Analyzing commits on the default branch: {branch}")

    commits = client.get_commits(branch)
    print(f"Found {len(commits)} commits on the {branch} branch")

    commits_per_user = defaultdict(dict)
    for commit in commits:
        author = commit["author"]["login"]
        commits_per_user[author]["login"] = author
        commits_per_user[author].setdefault("commits", []).append(
            f"https://github.com/{client.get_github_owner()}/{client.get_github_repo()}/commits/{commit['sha']}"
        )
        commits_per_user[author]["total_commits"] = (
            commits_per_user[author].setdefault("total_commits", 0) + 1
        )
        commits_per_user[author]["comment_count"] = commit["commit"]["comment_count"]
        commits_per_user[author]["message"] = commit["commit"]["message"]

    return commits_per_user


def get_commits_by_user() -> Any:
    try:
        commits_per_user = _extract_commits_by_user()

        # Print the results to the console as well
        print("\nCommits per user:")
        for commit_info in commits_per_user.items():
            print(json.dumps(commit_info))

        # Return the commits_per_user dictionary
        return commits_per_user

    except Exception as e:
        print(f"An error occurred during analysis: {str(e)}")
        print("Please check your token, owner, and repo name, and try again.")
        return None  # Return None in case of an error


def get_commits_by_author(author: str) -> Any:
    # Get commits per user in the repository
    commits_by_users = get_commits_by_user()
    if commits_by_users is None:
        return None, 0
    return commits_by_users.get(author, {}), commits_by_users.get(author, {}).get(
        "total_commits", 0
    )


def get_github_contributions_by_author(author: str) -> Any:
    commit_info_list, total_commits = get_commits_by_author(author=author)
    pr_list = get_pull_requests_by_author(author=author)

    return {
        "author": author,
        "total_commits": total_commits,
        "total_pull_requests": len(pr_list),
        "commits": commit_info_list,
        "pull_requests": pr_list,
    }


if __name__ == "__main__":
    author = "vijayanands@gmail.com"
