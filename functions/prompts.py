# Define a custom prompt for generating the self-appraisal
from llama_index.core import PromptTemplate

APPRAISAL_PROMPT = PromptTemplate(
    """
    You are tasked with generating a professional self-appraisal based only on the following information about an employee's contributions:

    {context}

    Please create a self-appraisal following these guidelines:
    1. Use an official and professional tone.
    2. Focus on facts and provide links to associated documents when possible.
    3. Highlight key achievements in jira, github and confluence.
    4. Highlight contributions in jira, github and confluence. Give details about the project and any relevant links or screenshots.
    4. Suggest potential learning opportunities based on the employee's work.
    6. Format the output as a valid JSON object with the following structure:
       {{
         "Summary": "Overall summary...",
         "Key Achievements": ["Achievement 1", "Achievement 2", ...],
         "Contributions": {{
           "Project A": "Details about contributions to Project A...",
           "Project B": "Details about contributions to Project B..."
         }},
         "Learning Opportunities": ["Opportunity 1", "Opportunity 2", ...],
       }}

    Ensure that the response is a valid JSON object and nothing else. Do not include any markdown formatting or code blocks.

    Self-Appraisal:
    """
)
