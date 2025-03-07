import json
import os
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List
from dotenv import load_dotenv
import requests
from utils import unique_user_emails, get_headers, get_last_calendar_year_dates

load_dotenv()

atlassian_base_url = "https://vijayanands.atlassian.net"
atlassian_username = "vijayanands@gmail.com"
atlassian_api_token = os.getenv("ATLASSIAN_API_TOKEN")
confluence_space_key = "SD"


def _extract_description_content(description):
    extracted_content = []
    indent_level = 0
    in_bullet_list = False

    def _process_content(content):
        nonlocal indent_level, in_bullet_list
        for item in content:
            if item["type"] == "text":
                text = item["text"]
                marks = item.get("marks", [])
                is_bold = any(mark["type"] == "strong" for mark in marks)
                is_italic = any(mark["type"] == "em" for mark in marks)

                if is_bold and is_italic:
                    text = text.upper()
                elif is_bold:
                    text = text.upper()
                elif is_italic:
                    text = text.capitalize()

                if in_bullet_list:
                    extracted_content[-1] += text
                else:
                    extracted_content.append("    " * indent_level + text)

            elif item["type"] == "paragraph":
                if extracted_content and not in_bullet_list:
                    extracted_content.append("")
                _process_content(item["content"])
                if not in_bullet_list:
                    extracted_content.append("")

            elif item["type"] == "bulletList":
                in_bullet_list = True
                indent_level += 1
                for list_item in item["content"]:
                    extracted_content.append("    " * (indent_level - 1) + "- ")
                    _process_content(list_item["content"])
                indent_level -= 1
                in_bullet_list = False
                extracted_content.append("")

            elif item["type"] == "listItem":
                _process_content(item["content"])

            elif item["type"] == "inlineCard":
                url = item["attrs"]["url"]
                extracted_content.append(f"    " * indent_level + f"Link: {url}")

    for item in description:
        _process_content([item])

    return "\n".join(extracted_content).strip()


def _extract_jira_response(base_url, response):
    # Parse the JSON response
    data = response.json()
    jira_list = []
    for issue in data["issues"]:
        jira_data = defaultdict()
        jira_data["summary"] = issue["fields"]["summary"]
        jira_data["reporter"] = issue["fields"]["reporter"]["emailAddress"]
        jira_data["assignee"] = (
            issue["fields"]["assignee"]["emailAddress"]
            if issue["fields"]["assignee"]
            else "Unassigned"
        )
        jira_data["link"] = f"{base_url}/browse/{issue['key']}"
        content = (
            issue["fields"]["description"]["content"]
            if issue["fields"]["description"]
            else None
        )
        jira_data["description"] = (
            _extract_description_content(content) if content else None
        )
        jira_data["timespent"] = issue["fields"]["timespent"]
        jira_data["resolutiondate"] = issue["fields"]["resolutiondate"]
        jira_data["priority"] = issue["fields"]["priority"]["name"]
        jira_data["resolved_by"] = (
            jira_data["assignee"] if jira_data["assignee"] != "Unassigned" else None
        )
        print(json.dumps(jira_data, indent=5))
        jira_list.append(jira_data)
    # Get the total number of issues
    jira_response = defaultdict()
    jira_response["total_resolved_issues"] = len(jira_list)
    jira_response["jiras_resolved"] = jira_list
    return jira_response


def fetch_jira_projects(base_url: str, username: str) -> list[dict[str, Any]]:
    """
    Fetch a list of projects from Jira using basic authentication.
    :return: A list of dictionaries containing project information
    """
    api_endpoint = f"{base_url}/rest/api/3/project"

    headers = get_headers(username, atlassian_api_token)
    response = requests.get(
        api_endpoint,
        headers=headers,
    )

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def count_resolved_issues(base_url, username, author, start_date, end_date):
    projects = fetch_jira_projects(base_url, username)
    print(json.dumps(projects, indent=2))
    projects = [project["key"] for project in projects]

    # Construct the JQL query with date filtering
    jql_query = f'project in ({",".join(projects)}) AND resolution = Done AND assignee = "{author}" AND resolutiondate >= "{start_date}" AND resolutiondate <= "{end_date}"'

    # Set up the API endpoint
    api_endpoint = f"{base_url}/rest/api/3/search"

    # Set up the parameters for the request
    params = {
        "jql": jql_query,
        "fields": [
            "issuetype",
            "timespent",
            "resolution",
            "resolutiondate",
            "priority",
            "summary",
            "description",
            "comments",
            "reporter",
            "assignee",
        ],
        # "maxResults": 0,  # We only need the total, not the actual issues
        # "maxResults": 0,  # We only need the total, not the actual issues
    }

    try:
        # Make the API request
        response = requests.get(
            api_endpoint,
            headers=get_headers(username, atlassian_api_token),
            params=params,
        )
        response.raise_for_status()  # Raise an exception for bad status codes

        jira_response = _extract_jira_response(base_url, response)
        return jira_response

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None


def count_resolved_issues_by_assignee(base_url, username):
    projects = fetch_jira_projects(base_url, username)
    print(json.dumps(projects, indent=2))
    projects = [project["key"] for project in projects]

    # Initialize the count dictionary
    resolved_counts = defaultdict(int)

    # Construct the JQL query
    jql_query = f'project in ({",".join(projects)}) AND resolution = Done'

    # Set up the API endpoint
    api_endpoint = f"{base_url}/rest/api/3/search"

    # Set up the parameters for the request
    params = {
        "jql": jql_query,
        "maxResults": 100,  # Adjust this value based on your needs
        "fields": "assignee",
    }

    try:
        while True:
            # Make the API request
            response = requests.get(
                api_endpoint,
                headers=get_headers(username, atlassian_api_token),
                params=params,
            )
            response.raise_for_status()  # Raise an exception for bad status codes

            # Parse the JSON response
            data = response.json()

            # Process each issue
            for issue in data["issues"]:
                assignee = issue["fields"]["assignee"]
                if assignee:
                    resolved_counts[assignee["displayName"]] += 1
                else:
                    resolved_counts["Unassigned"] += 1

            # Check if there are more issues to fetch
            if data["startAt"] + len(data["issues"]) >= data["total"]:
                break

            # Update startAt for the next page
            params["startAt"] = data["startAt"] + len(data["issues"])

        return resolved_counts

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def get_jira_contributions_by_author_for_the_last_year(author: str):
    """
    Get Jira contributions by the specified author for the last year

    Args:
        author (str): The author's username

    Returns:
        Dict : A summary of the author's contributions for the last year
    """
    start_date , end_date = get_last_calendar_year_dates()
    return get_jira_contributions_by_author(author, start_date, end_date)

def get_jira_contributions_by_author(author: str, start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Get Jira contributions by an author within a specified date range. If no date range is provided, defaults to the last year.

    Args:
        author (str): The author's username
        start_date (str): The start date for the search
        end_date (str, optional): The end date for the search. If not provided, defaults to current date.

    Returns:
        Dict : A summary of the author's contributions
    """
    response = count_resolved_issues(atlassian_base_url, atlassian_username, author, start_date, end_date)
    jira_data = response.get("jiras_resolved", [])
    jira_url_list = [jira["link"] for jira in jira_data]
    return {
        "author": author,
        "total_resolved_issues": response.get("total_resolved_issues"),
        "jiras_data": jira_data,
        "jira_list": jira_url_list,
    }

def get_jira_contributions_by_author_in_the_last_week(author: str):
    """
    Get Jira contributions by the specified author in the last week

    Args:
        author (str): The author's username

    Returns:
        Dict : A summary of the author's contributions in the last week
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M")
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M")
    get_jira_contributions_by_author(author, start_date_str, end_date_str)


def get_jira_contributions_per_user(start_date: str, end_date: str):
    all_jira_contributions = {}
    for user in unique_user_emails:
        contributions = get_jira_contributions_by_author(user, start_date, end_date)
        all_jira_contributions[user] = contributions
    return all_jira_contributions


