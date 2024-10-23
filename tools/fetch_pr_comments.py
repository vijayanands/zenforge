import requests
import sys
from datetime import datetime

def fetch_pr_comments(owner, repo, start_date, end_date=None, token=None):
    """
    Fetch pull request comments from a GitHub repository starting from a specific date.

    :param owner: Repository owner's username.
    :param repo: Repository name.
    :param start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SSZ).
    :param end_date: (Optional) End date in ISO format (YYYY-MM-DDTHH:MM:SSZ).
    :param token: (Optional) GitHub personal access token for authentication.
    :return: List of PR comment data.
    """
    base_url = f'https://api.github.com/repos/{owner}/{repo}/pulls/comments'
    headers = {'Accept': 'application/vnd.github.v3+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    params = {
        'since': start_date,
        'per_page': 100
    }

    all_comments = []
    page = 1

    while True:
        params['page'] = page
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            print(f'Error fetching data: {response.status_code}')
            print(response.json().get('message', 'No error message provided'))
            break

        data = response.json()
        if not data:
            break

        # If end_date is provided, filter comments within the end_date
        if end_date:
            for comment in data:
                comment_date = comment['created_at']
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

def main():
    if len(sys.argv) < 4:
        print("Usage: python fetch_pr_comments.py <owner> <repo> <start_date> [end_date] [token]")
        print("Example: python fetch_pr_comments.py octocat Spoon-Knife 2021-01-01T00:00:00Z")
        sys.exit(1)

    owner = sys.argv[1]
    repo = sys.argv[2]
    start_date = sys.argv[3]
    end_date = sys.argv[4] if len(sys.argv) > 4 and 'T' in sys.argv[4] else None
    token = sys.argv[5] if len(sys.argv) > 5 else None

    # Validate date format
    try:
        datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
        if end_date:
            datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')
    except ValueError:
        print("Date format should be YYYY-MM-DDTHH:MM:SSZ")
        sys.exit(1)

    comments = fetch_pr_comments(owner, repo, start_date, end_date, token)
    print(f"Found {len(comments)} pull request comment(s) starting from {start_date}:\n")
    for comment in comments:
        pr_number = comment['pull_request_url'].split('/')[-1]
        commenter = comment['user']['login']
        created_at = comment['created_at']
        url = comment['html_url']
        body = comment['body'].split('\n')[0]
        print(f"PR #{pr_number} Comment by {commenter} on {created_at}")
        print(f"  {body}")
        print(f"  URL: {url}\n")

if __name__ == "__main__":
    main()
