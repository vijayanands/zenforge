from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class JiraIssue(BaseModel):
    summary: str
    reporter: str
    assignee: str
    link: str
    description: Optional[str]
    timespent: Optional[str]
    resolutiondate: datetime
    priority: str
    resolved_by: str


class JiraData(BaseModel):
    author: str
    total_resolved_issues: int
    jiras_data: List[JiraIssue]
    jira_list: List[str]


class GitHubCommit(BaseModel):
    url: str


class GitHubPullRequest(BaseModel):
    number: int
    pr_title: str
    pr_url: str
    author: str
    body: Optional[str]


class GitHubData(BaseModel):
    commits: List[str]
    pull_requests: List[GitHubPullRequest]


class ConfluencePage(BaseModel):
    title: str
    created_at: datetime
    space_key: str
    author: str
    content: str
    page_link: str
    summary: str


class ConfluenceData(BaseModel):
    pages: Dict[str, ConfluencePage]


class UserData(BaseModel):
    jira: JiraData
    github: GitHubData
    confluence: ConfluenceData


class AllUserData(BaseModel):
    users: Dict[str, UserData]
