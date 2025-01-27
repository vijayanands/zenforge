from functions.llm.llamaindex_appraisal import self_appraisal_tool
from functions.github.github import initialize_github_hack

debug_jira = False
debug_confluence = False
debug_github = True


def create_self_appraisal(author):
    initialize_github_hack()
    return self_appraisal_tool(author)
