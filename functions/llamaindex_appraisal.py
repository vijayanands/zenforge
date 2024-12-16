import json
import logging
import re
from typing import List
from llama_index.core.agent import ReActAgent
from llama_index.core.tools import BaseTool, FunctionTool

from functions.prompts import APPRAISAL_PROMPT
from helpers.confluence import get_confluence_contributions_by_author
from helpers.get_llm import get_llm
from helpers.github import get_github_contributions_by_author
from helpers.jira import get_jira_contributions_by_author
from tools.generate_appraisal_docs import generate_appraisal_docs

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Create FunctionTool instances
tools: List[BaseTool] = [
    FunctionTool.from_defaults(fn=get_jira_contributions_by_author),
    FunctionTool.from_defaults(fn=get_github_contributions_by_author),
    FunctionTool.from_defaults(fn=get_confluence_contributions_by_author),
]


def generate_self_appraisal(author: str) -> str:
    # Create the LLM instance
    llm = get_llm(model="gpt-4o-mini")

    # Create the ReAct agent
    agent = ReActAgent.from_tools(tools, llm=llm, verbose=True)

    # Use the ReAct agent to gather information
    jira_query = f"Get Jira contributions for {author}"
    github_query = f"Get GitHub contributions for {author}"
    confluence_query = f"Get Confluence contributions for {author}"

    jira_response = agent.chat(jira_query)
    github_response = agent.chat(github_query)
    confluence_response = agent.chat(confluence_query)

    # Combine the gathered information
    context = f"""
    Jira Contributions:
    {jira_response.response}

    GitHub Contributions:
    {github_response.response}

    Confluence Contributions:
    {confluence_response.response}
    """

    # Generate the self-appraisal using the LLM

    appraisal_response = llm.complete(APPRAISAL_PROMPT.format(context=context))

    # Parse the JSON response
    try:
        # Try to parse the response as JSON
        appraisal_json = json.loads(appraisal_response.text)
    except json.JSONDecodeError:
        print("Error: LLM output is not valid JSON. Attempting to clean the output.")

        # Remove any potential Markdown formatting and find JSON-like content
        cleaned_text = appraisal_response.text.strip("`").strip()
        json_match = re.search(r"\{.*\}", cleaned_text, re.DOTALL)

        if json_match:
            try:
                appraisal_json = json.loads(json_match.group())
            except json.JSONDecodeError:
                print(
                    "Error: Cleaned output is still not valid JSON. Falling back to raw text."
                )
                appraisal_json = {"Raw Appraisal": appraisal_response.text}
        else:
            print("Error: No JSON-like content found. Falling back to raw text.")
            appraisal_json = {"Raw Appraisal": appraisal_response.text}

    return json.dumps(appraisal_json, indent=2)


def save_appraisal_to_json(appraisal: str, filename: str) -> None:
    with open(filename, "w") as f:
        f.write(appraisal)
    print(f"Appraisal saved to {filename}")
    logging.info(f"Appraisal saved to {filename}")


def self_appraisal_tool(author: str):
    # Generate appraisal based on the chosen vendor
    appraisal = generate_self_appraisal(author)
    # Save appraisal to JSON
    print(appraisal)
    json_file_name = f"/tmp/self_appraisal_{author}.json"
    save_appraisal_to_json(appraisal, json_file_name)
    print(f"Appraisal saved as JSON: {json_file_name}")

    # Generate HTML and PDF documents
    generate_appraisal_docs(json_file_name, author)
    return appraisal
