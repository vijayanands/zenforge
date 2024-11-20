import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any, DefaultDict, Dict, List, Optional

from tools.github.fetch_commit_comments import fetch_commit_comments
from tools.github.fetch_commits import fetch_commits
from tools.github.fetch_pr_comments import fetch_pr_comments
from tools.github.fetch_prs import fetch_pull_requests
from tools.github.github_client import GitHubAPIClient

client = GitHubAPIClient()
owner = client.get_github_owner()
repo = client.get_github_repo()
token = os.getenv("GITHUB_TOKEN")

github_data: Dict[str, Dict[str, Any]] = DefaultDict[str, Dict[str, Any]]()
user_info: Dict[str, Dict[str, str]] = {}

# Add these global variables to track data cache
_cached_github_data = None
_cached_user_info = None
_cached_start_date = None
_cached_end_date = None

def _is_date_range_subset(new_start: str, new_end: str, cached_start: str, cached_end: str) -> bool:
    """Check if new date range is a subset of cached date range"""
    if not all([new_start, new_end, cached_start, cached_end]):
        return False
        
    new_start_date = datetime.strptime(new_start, "%Y-%m-%d")
    new_end_date = datetime.strptime(new_end, "%Y-%m-%d")
    cached_start_date = datetime.strptime(cached_start, "%Y-%m-%d")
    cached_end_date = datetime.strptime(cached_end, "%Y-%m-%d")
    
    return new_start_date >= cached_start_date and new_end_date <= cached_end_date

def _extract_pr_info(pr: Dict[str, Any]) -> Dict[str, Any]:
    milestone = pr.get("milestone", {})
    merged_at = pr["pull_request"]["merged_at"]
    return {
        "html_url": pr["html_url"],
        "id": pr["id"],
        "number": pr["number"],
        "state": pr["state"],
        "title": pr["title"],
        "body": pr["body"],
        "labels": [
            {
                "id": label["id"],
                "name": label["name"],
                "description": label["description"],
            }
            for label in pr.get("labels", [])
        ],
        "milestone": (
            {
                "id": milestone.get("id"),
                "number": milestone.get("number"),
                "state": milestone.get("state"),
                "title": milestone.get("title"),
                "description": milestone.get("description"),
                "open_issues": milestone.get("open_issues"),
                "closed_issues": milestone.get("closed_issues"),
                "created_at": milestone.get("created_at"),
                "updated_at": milestone.get("updated_at"),
                "closed_at": milestone.get("closed_at"),
                "due_on": milestone.get("due_on"),
            }
            if milestone
            else None
        ),
        "created_at": pr["created_at"],
        "updated_at": pr["updated_at"],
        "closed_at": pr["closed_at"],
        "merged_at": merged_at,
    }


def _extract_pr_comment_info(pr_comment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "html_url": pr_comment["html_url"],
        "pull_request_review_id": pr_comment.get("pull_request_review_id"),
        "id": pr_comment["id"],
        "commit_id": pr_comment.get("commit_id"),
        "original_commit_id": pr_comment.get("original_commit_id"),
        "in_reply_to_id": pr_comment.get("in_reply_to_id"),
        "body": pr_comment["body"],
        "created_at": pr_comment["created_at"],
    }


def _extract_commit_comment_info(commit_comment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "html_url": commit_comment["html_url"],
        "id": commit_comment["id"],
        "body": commit_comment["body"],
        "commit_id": commit_comment["commit_id"],
        "created_at": commit_comment["created_at"],
        "updated_at": commit_comment["updated_at"],
    }


def _extract_commit_info(commit: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "sha": commit["sha"],
        "html_url": commit["html_url"],
        "message": commit["commit"]["message"],
        "date": commit["commit"]["author"]["date"],
    }


def get_all_PRs_by_user(since: Optional[datetime] = None) -> Any:
    raw_prs: Any = client.get_all_pulls(since=since)
    extracted_pr_info = [_extract_pr_info(pr) for pr in raw_prs]
    prs_by_author = defaultdict(dict)
    for pr_info in extracted_pr_info:
        author = pr_info["author"]
        prs_by_author[author]["author"] = author
        prs_by_author[author].setdefault("pull_requests", []).append(pr_info)
    return prs_by_author


def get_pull_requests_by_author(author: str, since: Optional[datetime] = None) -> Any:
    return get_all_PRs_by_user(since=since)[author].get("pull_requests", [])


def _extract_commits_by_user(since: Optional[datetime] = None) -> Any:
    branch = client.get_default_branch()
    print(f"Analyzing commits on the default branch: {branch}")

    commits = client.get_commits(branch, since=since)
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
        commits_per_user[author][
            "commemake sure that the updated_at is greater than sincets_url"
        ] = commit["comments_url"]
        commits_per_user[author]["message"] = commit["commit"]["message"]

    return commits_per_user


def get_commits_by_user(since: Optional[datetime] = None) -> Any:
    try:
        commits_per_user = _extract_commits_by_user(since=since)

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


def get_commits_by_author(author: str, since: Optional[datetime] = None) -> Any:
    # Get commits per user in the repository
    commits_by_users = get_commits_by_user(since=since)
    if commits_by_users is None:
        return None, 0
    return commits_by_users.get(author, {}), commits_by_users.get(author, {}).get(
        "total_commits", 0
    )


def get_github_contributions_by_author(
    author: str, since: Optional[datetime] = None
) -> Any:
    commit_info_list, total_commits = get_commits_by_author(author=author, since=since)
    pr_list = get_pull_requests_by_author(author=author, since=since)

    return {
        "author": author,
        "total_commits": total_commits,
        "total_pull_requests": len(pr_list),
        "commits": commit_info_list,
        "pull_requests": pr_list,
    }


def aggregate_github_data(
    prs: List[Dict[str, Any]],
    pr_comments: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    commit_comments: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    github_data: DefaultDict[str, Dict[str, Any]] = defaultdict(
        lambda: defaultdict(list)
    )

    for pr in prs:
        author = pr["user"]["login"]
        if author not in user_info.keys():
            user_info[author] = {"name": None}
        pr_info = _extract_pr_info(pr)
        github_data[author].setdefault("total_pull_requests", 0)
        github_data[author]["total_pull_requests"] += 1
        github_data[author]["pull_requests"].append(pr_info)

    for pr_comment in pr_comments:
        author = pr_comment["user"]["login"]
        if author not in user_info.keys():
            user_info[author] = {"name": None}
        pr_comment_info = _extract_pr_comment_info(pr_comment)
        github_data[author].setdefault("total_pull_request_comments", 0)
        github_data[author]["total_pull_request_comments"] += 1
        github_data[author]["pull_request_comments"].append(pr_comment_info)

    for commit in commits:
        author = commit["commit"]["author"]["email"]
        name = commit["commit"]["author"]["name"]
        if author not in user_info.keys():
            user_info[author] = {"name": name}
        else:
            user_info[author]["name"] = name
        commit_info = _extract_commit_info(commit)
        github_data[author].setdefault("total_commits", 0)
        github_data[author]["total_commits"] += 1
        github_data[author]["commits"].append(commit_info)

    for commit_comment in commit_comments:
        author = commit_comment["user"]["login"]
        if author not in user_info.keys():
            user_info[author] = {"name": None}
        commit_comment_info = _extract_commit_comment_info(commit_comment)
        github_data[author].setdefault("total_commit_comments", 0)
        github_data[author]["total_commit_comments"] += 1
        github_data[author]["commit_comments"].append(commit_comment_info)


    return dict(github_data)


def get_commits(start_date: str, end_date: Optional[str] = None):
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    commits = fetch_commits(owner, repo, start_date, end_date, token)
    return commits


def print_commits(commits, start_date):
    print(f"Found {len(commits)} commit(s) starting from {start_date}:\n")
    for commit in commits:
        sha = commit["sha"]
        message = commit["commit"]["message"].split("\n")[0]
        author = commit["commit"]["author"]["name"]
        date = commit["commit"]["author"]["date"]
        url = commit["html_url"]
        print(f"Commit {sha[:7]} - {message}")
        print(f"  Author: {author} on {date}")
        print(f"  URL: {url}\n")


def get_PR_comments(start_date: str, end_date: Optional[str] = None):
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    comments = fetch_pr_comments(owner, repo, start_date, end_date, token)
    return comments


def print_PR_comments(comments, start_date):
    print(
        f"Found {len(comments)} pull request comment(s) starting from {start_date}:\n"
    )
    for comment in comments:
        pr_number = comment["pull_request_url"].split("/")[-1]
        commenter = comment["user"]["login"]
        created_at = comment["created_at"]
        url = comment["html_url"]
        body = comment["body"].split("\n")[0]
        print(f"PR #{pr_number} Comment by {commenter} on {created_at}")
        print(f"  {body}")
        print(f"  URL: {url}\n")


def get_commit_comments(start_date: str, end_date: Optional[str] = None):
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    comments = fetch_commit_comments(owner, repo, start_date, end_date, token)
    return comments


def print_commit_comments(comments, start_date):
    print(f"Found {len(comments)} commit comment(s) starting from {start_date}:\n")
    for comment in comments:
        commit_id = comment["commit_id"]
        commenter = comment["user"]["login"]
        created_at = comment["created_at"]
        url = comment["html_url"]
        body = comment["body"].split("\n")[0]
        print(f"Commit {commit_id[:7]} Comment by {commenter} on {created_at}")
        print(f"  {body}")
        print(f"  URL: {url}\n")


def get_PRs(start_date: str, end_date: Optional[str] = None):
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    prs = fetch_pull_requests(owner, repo, start_date, end_date, token)
    return prs


def print_PRs(prs, start_date):
    print(f"Found {len(prs)} pull request(s) starting from {start_date}:\n")
    for pr in prs:
        print(f"PR #{pr['number']} - {pr['title']}")
        print(f"  Created by: {pr['user']['login']} on {pr['created_at']}")
        print(f"  URL: {pr['html_url']}\n")


def _pretty_print_dict(dictionary, indent=0):
    """
    Pretty prints a dictionary with nested structures.

    Args:
        dictionary: The dictionary to print
        indent: Current indentation level (default: 0)
    """
    for key, value in dictionary.items():
        print("  " * indent + str(key) + ":", end=" ")
        if isinstance(value, dict):
            print()
            _pretty_print_dict(value, indent + 1)
        else:
            print(str(value))


def print_github_data(github_data):
        # Convert github_data to JSON
    json_data = json.dumps(github_data, indent=2, default=str)

    # Print the JSON data
    print(json_data)

    # Save the JSON data to a file
    output_file = "../github_data_output.json"
    with open(output_file, "w") as f:
        f.write(json_data)

    print(f"\nJSON data has been saved to {output_file}")

def set_user_name_to_email(user_info: Dict[str, Dict[str, str]]) -> None:
    for email, info in user_info.items():
        if info["name"] is None:
            info["name"] = email

def pull_github_data(
    start_date: str, end_date: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """Pull GitHub data with caching"""
    global _cached_github_data, _cached_user_info, _cached_start_date, _cached_end_date
    
    # If we have cached data and the new date range is a subset of cached range
    if (_cached_github_data is not None and _cached_user_info is not None and
        _is_date_range_subset(start_date, end_date, _cached_start_date, _cached_end_date)):
        print(f"Using cached GitHub data from {_cached_start_date} to {_cached_end_date}")
        return _cached_github_data, _cached_user_info
    
    # If we need to fetch new data
    print(f"Fetching new GitHub data from {start_date} to {end_date}")
    prs = get_PRs(start_date=start_date, end_date=end_date)
    pr_comments = get_PR_comments(start_date=start_date, end_date=end_date)
    commits = get_commits(start_date=start_date, end_date=end_date)
    commit_comments = get_commit_comments(start_date=start_date, end_date=end_date)

    github_data = aggregate_github_data(prs, pr_comments, commits, commit_comments)
    set_user_name_to_email(user_info)
    
    # Cache the new data
    _cached_github_data = github_data
    _cached_user_info = user_info
    _cached_start_date = start_date
    _cached_end_date = end_date
    
    print_github_data(github_data)
    return github_data, user_info


if __name__ == "__main__":
    start_date = "2024-10-01"
    end_date = None
    github_data, user_info = pull_github_data(start_date, end_date)

