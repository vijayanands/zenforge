from functions.llm.llamaindex_appraisal import weekly_report_tool
from functions.github.github import initialize_github_hack


def create_weekly_report(author):
    initialize_github_hack()
    return weekly_report_tool(author)