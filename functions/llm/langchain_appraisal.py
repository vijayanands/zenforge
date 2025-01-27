import json
from typing import Dict, List
from langchain.agents import AgentType, Tool, initialize_agent
from langchain.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate

from utils import generate_appraisal_docs
from functions.github.github import get_github_contributions_by_author
from functions.jira.jira import get_jira_contributions_by_author
from functions.confluence.confluence import get_confluence_contributions_by_author

def create_langchain_tools() -> List[Tool]:
    """Create tools for the Langchain agent"""
    return [
        Tool(
            name="get_github_contributions",
            func=get_github_contributions_by_author,
            description="Get GitHub contributions for a specific author"
        ),
        Tool(
            name="get_jira_contributions",
            func=get_jira_contributions_by_author,
            description="Get Jira contributions for a specific author"
        ),
        Tool(
            name="get_confluence_contributions",
            func=get_confluence_contributions_by_author,
            description="Get Confluence contributions for a specific author"
        )
    ]

def create_appraisal_prompt() -> PromptTemplate:
    """Create the prompt template for self-appraisal"""
    return PromptTemplate(
        template="""
        Generate a professional self-appraisal based on the following information:
        
        {context}
        
        Format the response as a JSON object with the following structure:
        {
            "Summary": "Overall summary...",
            "Key Achievements": ["Achievement 1", "Achievement 2", ...],
            "Contributions": {
                "Project A": "Details about contributions to Project A...",
                "Project B": "Details about contributions to Project B..."
            },
            "Learning Opportunities": ["Opportunity 1", "Opportunity 2", ...]
        }
        """,
        input_variables=["context"]
    )

def generate_self_appraisal_langchain(author: str) -> str:
    """Generate self-appraisal using Langchain agent"""
    try:
        # Initialize ChatOpenAI
        llm = ChatOpenAI(
            temperature=0,
            model="gpt-4",
        )
        
        # Create tools
        tools = create_langchain_tools()
        
        # Initialize agent with system message
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            system_message="You are a professional performance evaluation assistant."
        )
        
        # Gather information using the agent
        try:
            github_info = agent.run(f"Get GitHub contributions for {author}")
            github_info = github_info if github_info else "No GitHub contributions found."
        except Exception as e:
            print(f"Error getting GitHub info: {str(e)}")
            github_info = "Unable to fetch GitHub contributions."

        try:
            jira_info = agent.run(f"Get Jira contributions for {author}")
            jira_info = jira_info if jira_info else "No Jira contributions found."
        except Exception as e:
            print(f"Error getting Jira info: {str(e)}")
            jira_info = "Unable to fetch Jira contributions."

        try:
            confluence_info = agent.run(f"Get Confluence contributions for {author}")
            confluence_info = confluence_info if confluence_info else "No Confluence contributions found."
        except Exception as e:
            print(f"Error getting Confluence info: {str(e)}")
            confluence_info = "Unable to fetch Confluence contributions."
        
        # Combine information
        context = f"""
        GitHub Contributions:
        {github_info}
        
        Jira Contributions:
        {jira_info}
        
        Confluence Contributions:
        {confluence_info}
        """
        
        # Create prompt
        prompt = create_appraisal_prompt()
        
        try:
            # Generate appraisal
            response = llm.predict(prompt.format(context=context))
            
            # Validate JSON response
            json.loads(response)  # This will raise an exception if response is not valid JSON
            return response
            
        except json.JSONDecodeError:
            print("Error: Invalid JSON response from LLM")
            return json.dumps({
                "Summary": "Error generating complete appraisal",
                "Key Achievements": ["Unable to process achievements"],
                "Contributions": {"Error": "Unable to process contributions"},
                "Learning Opportunities": ["Unable to process learning opportunities"]
            })
        
    except Exception as e:
        print(f"Error in appraisal generation: {str(e)}")
        return json.dumps({
            "Summary": "Error generating appraisal",
            "Key Achievements": [],
            "Contributions": {},
            "Learning Opportunities": []
        })

def self_appraisal_tool_langchain(author: str) -> Dict:
    """Main function to generate and save self-appraisal"""
    # Generate appraisal
    appraisal = generate_self_appraisal_langchain(author)
    
    # Save to file
    json_file_name = f"/tmp/self_appraisal_{author}_langchain.json"
    with open(json_file_name, "w") as f:
        f.write(appraisal)
    
    print(f"Appraisal saved as JSON: {json_file_name}")
    
    # Generate docs if needed
    generate_appraisal_docs(json_file_name, author)
    
    return json.loads(appraisal) 