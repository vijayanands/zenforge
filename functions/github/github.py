import json
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, DefaultDict, Dict, List, Optional
import random
from dotenv import load_dotenv

from utils import unique_user_emails, user_to_external_users, map_user, get_last_calendar_year_dates, get_log_level
from model.sdlc_events import UserMapping, User, DatabaseManager, connection_string, Base
from functions.github.github_client import GitHubAPIClient
load_dotenv()

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

def _is_date_range_subset(new_start: str, new_end: str, cached_start: Optional[str], cached_end: Optional[str]) -> bool:
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
    merged_at = pr["merged_at"]
    return {
        "html_url": pr["html_url"],
        "id": pr["id"],
        "number": pr["number"],
        "state": pr["state"],
        "title": pr["title"],
        "body": pr["body"],
        "author": pr["user"]["login"],
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


def get_all_pull_requests_by_user(since: Optional[datetime] = None) -> Any:
    raw_prs: Any = client.get_all_pull_requests(start_date=since.strftime("%Y-%m-%d") if since else None)
    extracted_pr_info = [_extract_pr_info(pr) for pr in raw_prs]
    prs_by_author = defaultdict(dict)
    for pr_info in extracted_pr_info:
        author = pr_info["author"]
        prs_by_author[author]["author"] = author
        prs_by_author[author].setdefault("pull_requests", []).append(pr_info)
    return prs_by_author


def get_pull_requests_by_author(author: str, since: Optional[datetime] = None) -> Any:
    return get_all_pull_requests_by_user(since=since)[author].get("pull_requests", [])

def get_github_contributions_by_author_for_the_last_year(author: str) -> Any:
    """
    Get Jira contributions by the specified author for the last calendar year

    Args:
        author (str): The author's username

    Returns:
        Dict : A summary of the author's contributions
    """
    start_date, end_date = get_last_calendar_year_dates()
    return get_github_contributions_by_author(author, start_date=start_date, end_date=end_date)

def get_github_contributions_by_author(author: str, start_date: str, end_date: str) -> Any:
    """
    Get Jira contributions by the specified author for the specified date range. If no date range is provided, defaults to the last year.

    Args:
        author (str): The author's username
        start_date (datetime): The start date for the search
        end_date (datetime, optional): The end date for the search. If not provided, defaults to current date.

    Returns:
        Dict : A summary of the author's contributions
    """
    commit_info_list, total_commits = get_commits_by_author(author=author, start_date=start_date, end_date=end_date)
    pr_list = get_pull_requests_by_author(author=author)

    return {
        "author": author,
        "total_commits": total_commits,
        "total_pull_requests": len(pr_list),
        "commits": commit_info_list,
        "pull_requests": pr_list,
    }

def get_github_contributions_by_author_in_the_last_week(author: str) -> Any:
    """
    Get Jira contributions by the specified author in the last week.

    Args:
        author (str): The author's username

    Returns:
        Dict : A summary of the author's contributions in the last week
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M")
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M")
    return get_github_contributions_by_author(author, start_date=start_date_str, end_date=end_date_str)

def get_user_mapping(github_username: str, session) -> Optional[str]:
    """Get mapped user email from the mapping table"""
    try:
        session.rollback()  # Reset any failed transaction
        mapping = session.query(UserMapping).filter_by(github_username=github_username).first()
        return mapping.email if mapping else None
    except Exception as e:
        print(f"Error accessing user mappings: {e}")
        session.rollback()  # Reset the failed transaction
        try:
            # Create the table if it doesn't exist
            Base.metadata.create_all(session.bind)
            session.commit()
        except Exception as create_error:
            print(f"Error creating table: {create_error}")
            session.rollback()
        return None

def create_user_mapping(github_username: str, session) -> str:
    """Create a new user mapping by randomly assigning to an existing user"""
    try:
        session.rollback()  # Reset any failed transaction
        # Query all users from the timeseries db
        users = session.query(User).all()
        if not users:
            raise ValueError("No users found in the system to map GitHub users")
        
        try:
            # Try to get existing mappings
            existing_mappings = session.query(UserMapping).all()
        except Exception:
            # If table doesn't exist, create it and start with empty mappings
            Base.metadata.create_all(session.bind)
            session.commit()
            existing_mappings = []
        
        user_mapping_counts = defaultdict(int)
        
        # Count how many GitHub users are mapped to each system user
        for mapping in existing_mappings:
            user_mapping_counts[mapping.email] += 1
        
        # Find users with the least number of mappings
        min_mappings = float('inf')
        candidates = []
        
        for user in users:
            mappings_count = user_mapping_counts[user.email]
            if mappings_count < min_mappings:
                min_mappings = mappings_count
                candidates = [user]
            elif mappings_count == min_mappings:
                candidates.append(user)
        
        # Randomly select from the candidates with the least mappings
        selected_user = random.choice(candidates)
        
        # Create and save the mapping
        mapping = UserMapping(github_username=github_username, email=selected_user.email)
        session.add(mapping)
        session.commit()
        
        print(f"Mapped GitHub user '{github_username}' to system user '{selected_user.email}'")
        return selected_user.email
        
    except Exception as e:
        print(f"Error creating user mapping: {e}")
        session.rollback()  # Reset the failed transaction
        # If anything fails, return a default user
        default_user = session.query(User).first()
        if not default_user:
            raise ValueError("No users available in the system")
        return default_user.email

def get_or_create_user_mapping(github_username: str, session) -> str:
    """Get existing mapping or create new one"""
    try:
        session.rollback()  # Reset any failed transaction
        mapped_email = get_user_mapping(github_username, session)
        if not mapped_email:
            mapped_email = create_user_mapping(github_username, session)
        return mapped_email
    except Exception as e:
        print(f"Error in user mapping: {e}")
        session.rollback()  # Reset the failed transaction
        # Fallback to getting any user from the system
        default_user = session.query(User).first()
        if not default_user:
            raise ValueError("No users available in the system")
        return default_user.email

def aggregate_github_data(
    prs: List[Dict[str, Any]],
    pr_comments: List[Dict[str, Any]],
    commits: List[Dict[str, Any]],
    commit_comments: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    github_data: DefaultDict[str, Dict[str, Any]] = defaultdict(lambda: defaultdict(list))
    
    with DatabaseManager(connection_string).get_session() as session:
        # Process PRs
        for pr in prs:
            github_username = pr["user"]["login"]
            mapped_email = get_or_create_user_mapping(github_username, session)
            
            if mapped_email not in user_info:
                user = session.query(User).filter_by(email=mapped_email).first()
                user_info[mapped_email] = {"name": user.name if user else None}
            
            pr_info = _extract_pr_info(pr)
            github_data[mapped_email].setdefault("total_pull_requests", 0)
            github_data[mapped_email]["total_pull_requests"] += 1
            github_data[mapped_email]["pull_requests"].append(pr_info)

        # Process PR comments
        for pr_comment in pr_comments:
            github_username = pr_comment["user"]["login"]
            mapped_email = get_or_create_user_mapping(github_username, session)
            
            if mapped_email not in user_info:
                user = session.query(User).filter_by(email=mapped_email).first()
                user_info[mapped_email] = {"name": user.name if user else None}
            
            pr_comment_info = _extract_pr_comment_info(pr_comment)
            github_data[mapped_email].setdefault("total_pull_request_comments", 0)
            github_data[mapped_email]["total_pull_request_comments"] += 1
            github_data[mapped_email]["pull_request_comments"].append(pr_comment_info)

        # Process commits
        for commit in commits:
            github_username = commit["commit"]["author"]["email"]
            mapped_email = get_or_create_user_mapping(github_username, session)
            
            if mapped_email not in user_info:
                user = session.query(User).filter_by(email=mapped_email).first()
                user_info[mapped_email] = {"name": user.name if user else None}
            
            commit_info = _extract_commit_info(commit)
            github_data[mapped_email].setdefault("total_commits", 0)
            github_data[mapped_email]["total_commits"] += 1
            github_data[mapped_email]["commits"].append(commit_info)

        # Process commit comments
        for commit_comment in commit_comments:
            github_username = commit_comment["user"]["login"]
            mapped_email = get_or_create_user_mapping(github_username, session)
            
            if mapped_email not in user_info:
                user = session.query(User).filter_by(email=mapped_email).first()
                user_info[mapped_email] = {"name": user.name if user else None}
            
            commit_comment_info = _extract_commit_comment_info(commit_comment)
            github_data[mapped_email].setdefault("total_commit_comments", 0)
            github_data[mapped_email]["total_commit_comments"] += 1
            github_data[mapped_email]["commit_comments"].append(commit_comment_info)

    return dict(github_data)


def get_commits(start_date: str, end_date: Optional[str] = None):
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    branch = client.get_default_branch()
    commits = client.get_commits(branch, start_date, end_date)
    return commits


def get_pull_request_comments(prs: List, start_date: str, end_date: str):
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    comments = []
    for pr in prs:
        comments.extend(client.get_pull_request_comments(pr["number"], start, end))
    return comments


def print_pull_request_comments(comments, start_date):
    logging.debug(
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

    comments = client.get_all_commit_comments(datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d") if end_date else None)
    return comments


def get_PRs(start_date: str, end_date: Optional[str] = None):
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        logging.error("Date format should be YYYY-MM-DD")
        sys.exit(1)

    prs = client.get_all_pull_requests(start_date=datetime.strptime(start_date, "%Y-%m-%d"), end_date=datetime.strptime(end_date, "%Y-%m-%d") if end_date else None)
    return prs


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


def set_user_name_to_email(user_info: Dict[str, Dict[str, str]]) -> None:
    for email, info in user_info.items():
        if info["name"] is None:
            info["name"] = email

def pull_github_data(
    start_date: str, end_date: str
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, str]]]:
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
    pr_comments = get_pull_request_comments(prs=prs, start_date=start_date, end_date=end_date)
    commits = get_commits(start_date=start_date, end_date=end_date)
    commit_comments = get_commit_comments(start_date=start_date, end_date=end_date)

    data = aggregate_github_data(prs, pr_comments, commits, commit_comments)
    set_user_name_to_email(user_info)
    
    # Cache the new data
    _cached_github_data = data
    _cached_user_info = user_info
    _cached_start_date = start_date
    _cached_end_date = end_date
    
    # print_github_data(data)
    return data, user_info


def _analyze_commits_per_user(start_date: str, end_date: str):
    logging.info(f"Analyzing repository: {owner}/{repo}")
    branch = client.get_default_branch()
    logging.debug(f"Analyzing commits on the default branch: {branch}")

    commits = client.get_commits(branch, start_date, end_date)
    logging.debug(f"Found {len(commits)} commits on the {branch} branch")

    commits_per_user = defaultdict(dict)

    for commit in commits:
        author = commit["commit"]["author"]["email"]
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


def _get_commits_per_user_in_repo(start_date: str, end_date: str):
    try:
        commits_per_user = _analyze_commits_per_user(start_date, end_date)

        # Print the results to the console as well
        if get_log_level() == logging.DEBUG:
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

def initialize_github_hack():
    contributors = list_repo_contributors(owner="octocat", repo="Hello-World")
    print(contributors)
    for username in contributors:
        map_user(username)


def list_repo_contributors(owner: str, repo: str) -> Any:
    all_contributors = client.list_contributors()
    logging.debug(f"Found {len(all_contributors)} contributors in {owner}/{repo}")
    return all_contributors


def get_all_pull_requests_data(owner: str, repo: str) -> Any:
    client = GitHubAPIClient()
    raw_prs: Any = client.get_all_pull_requests()
    prs = [_extract_pr_info(pr) for pr in raw_prs]

    logging.debug(f"Found {len(prs)} pull requests in {owner}/{repo}")
    return prs


def get_pull_requests_per_user() -> Any:
    raw_prs: Any = client.get_all_pull_requests()
    extracted_pr_info = [_extract_pr_info(pr) for pr in raw_prs]
    prs_by_author = defaultdict(dict)
    for pr_info in extracted_pr_info:
        author = pr_info["author"]
        prs_by_author[author]["author"] = author
        prs_by_author[author].setdefault("pull_requests", []).append(pr_info)
    return prs_by_author


def get_commits_by_author(author: str, start_date: str, end_date: str) -> Any:
    # Get a list of external user ids mapped to the author
    external_usernames = user_to_external_users[author]

    logging.info(f"Get commits by author: {author} start_date: {start_date}, end_date: {end_date}")
    if not external_usernames:
        logging.warning(f"No external usernames found for author: {author}")
        return None

    # Get commits per user in the repository
    _github_data = _get_commits_per_user_in_repo(start_date, end_date)

    if not _github_data:
        logging.warning("No GitHub data retrieved")
        return None

    # Sum up the total commits for all external usernames
    commit_info_list = []
    total_commits = 0
    for username in external_usernames:
        commit_info = _github_data.get(username)
        if not commit_info:
            logging.debug(f"No commit info found for external username: {username}")
            continue
        total_commits += commit_info.get("total_commits")
        commit_info_list.append(commit_info)
    return commit_info_list, total_commits


def get_github_contributions_by_repo(start_date: str, end_date: str):
    commits_per_user = _get_commits_per_user_in_repo(start_date, end_date)
    pull_requests_per_user = get_pull_requests_per_user()

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
