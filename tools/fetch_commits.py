import sys
from datetime import datetime

import requests


def fetch_commits(owner, repo, start_date, end_date=None, token=None):
    """
    Fetch commits from a GitHub repository starting from a specific date.

    :param owner: Repository owner's username.
    :param repo: Repository name.
    :param start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SSZ).
    :param end_date: (Optional) End date in ISO format (YYYY-MM-DDTHH:MM:SSZ).
    :param token: (Optional) GitHub personal access token for authentication.
    :return: List of commit data.
    """
    base_url = f"https://api.github.com/repos/{owner}/{repo}/commits"
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


def main():
    if len(sys.argv) < 4:
        print(
            "Usage: python fetch_commits.py <owner> <repo> <start_date> [end_date] [token]"
        )
        print(
            "Example: python fetch_commits.py octocat Spoon-Knife 2021-01-01T00:00:00Z"
        )
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    start_date = sys.argv[3]
    end_date = sys.argv[4] if len(sys.argv) > 4 and "T" in sys.argv[4] else None
    token = sys.argv[5] if len(sys.argv) > 5 else None

    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%dT%H:%M:%SZ")
        if end_date:
            datetime.strptime(end_date, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        print("Date format should be YYYY-MM-DDTHH:MM:SSZ")
        sys.exit(1)

    commits = fetch_commits(owner, repo, start_date, end_date, token)
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


if __name__ == "__main__":
    main()
