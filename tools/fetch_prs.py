import requests
import sys
from datetime import datetime

def fetch_pull_requests(owner, repo, start_date, end_date=None, token=None):
    """
    Fetch pull requests from a GitHub repository starting from a specific date.

    :param owner: Repository owner's username.
    :param repo: Repository name.
    :param start_date: Start date in ISO format (YYYY-MM-DD).
    :param end_date: (Optional) End date in ISO format (YYYY-MM-DD).
    :param token: (Optional) GitHub personal access token for authentication.
    :return: List of pull request data.
    """
    base_url = 'https://api.github.com/search/issues'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    date_range = f'created:>={start_date}'
    if end_date:
        date_range = f'created:{start_date}..{end_date}'

    query = f'repo:{owner}/{repo} is:pr {date_range}'
    params = {'q': query, 'per_page': 100}
    all_pull_requests = []
    page = 1

    while True:
        params['page'] = page
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f'Error fetching data: {response.status_code}')
            print(response.json().get('message', 'No error message provided'))
            break

        data = response.json()
        items = data.get('items', [])
        all_pull_requests.extend(items)

        if 'next' not in response.links:
            break
        page += 1

    return all_pull_requests

def main():
    if len(sys.argv) < 4:
        print("Usage: python fetch_prs.py <owner> <repo> <start_date> [end_date] [token]")
        print("Example: python fetch_prs.py octocat Spoon-Knife 2021-01-01")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    start_date = sys.argv[3]
    end_date = sys.argv[4] if len(sys.argv) > 4 and '-' in sys.argv[4] else None
    token = sys.argv[5] if len(sys.argv) > 5 else None

    # Validate date format
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        print("Date format should be YYYY-MM-DD")
        sys.exit(1)

    prs = fetch_pull_requests(owner, repo, start_date, end_date, token)
    print(f"Found {len(prs)} pull request(s) starting from {start_date}:\n")
    for pr in prs:
        print(f"PR #{pr['number']} - {pr['title']}")
        print(f"  Created by: {pr['user']['login']} on {pr['created_at']}")
        print(f"  URL: {pr['html_url']}\n")

if __name__ == "__main__":
    main()
