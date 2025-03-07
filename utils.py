import base64
import hashlib
import json
import os
import re
import sys
import logging
from collections import defaultdict
from datetime import datetime
from html import escape
from typing import Dict, List
from dotenv import load_dotenv
from llama_index.llms.openai import OpenAI
from pdfkit import pdfkit

unique_user_emails = [
    "vijayanands@gmail.com",
    "vijayanands@yahoo.com",
    "vjy1970@gmail.com",
    "email2vijay@gmail.com",
]
user_to_external_users: Dict[str, List[str]] = defaultdict(list)
external_user_to_user: Dict[str, str] = defaultdict()

def get_log_level():
    load_dotenv()
    # Get the logging level from environment variable, default to INFO if not set
    log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Map string log levels to logging constants
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }

    # Get the appropriate logging level, default to INFO if invalid
    log_level = log_level_map.get(log_level_str, logging.INFO)

    return log_level


def map_user(external_username: str):
    hash_value = int(hashlib.md5(external_username.encode()).hexdigest(), 16)
    mapped_user_email = unique_user_emails[hash_value % len(unique_user_emails)]
    external_user_to_user[external_username] = mapped_user_email
    user_to_external_users[mapped_user_email].append(external_username)


def get_llm(**kwargs):
    """
    Factory function to create an LLM instance based on the vendor.
    """
    load_dotenv()
    return OpenAI(
        temperature=kwargs.get("temperature", 0.7),
        model=kwargs.get("model", "gpt-3.5-turbo"),
        api_key=os.getenv("OPENAI_API_KEY"),  # Assumes environment variable OPENAI_API_KEY is set with your OpenAI API key.
    )


def base64_encode_string(input_string: str) -> str:
    """
    Encode a string to base64.

    :param input_string: The string to encode
    :return: The base64 encoded string
    """
    # Convert the string to bytes
    input_bytes = input_string.encode("utf-8")

    # Perform base64 encoding
    encoded_bytes = base64.b64encode(input_bytes)

    # Convert the result back to a string
    encoded_string = encoded_bytes.decode("utf-8")

    return encoded_string


def get_basic_auth_header(username: str, password: str) -> str:
    auth_string = f"{username}:{password}"
    return f"Basic {base64_encode_string(auth_string)}"


def get_headers(username: str, api_token: str) -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Authorization": get_basic_auth_header(username, api_token),
    }
    return headers


def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


def get_base64_of_bytes(bytes_data):
    return base64.b64encode(bytes_data).decode()

def parse_markdown_links(text):
    def replace_link(match):
        text = match.group(1)
        url = match.group(2)
        return f'<a href="{url}" target="_blank">{text}</a>'

    pattern = r"\[(.*?)\]\((.*?)\)"
    return re.sub(pattern, replace_link, text)


def json_to_html(data, level=1):
    if isinstance(data, dict):
        html = "<dl>\n"
        for key, value in data.items():
            html += f"<dt><h{level}>{escape(str(key))}</h{level}></dt>\n"
            html += f"<dd>{json_to_html(value, level + 1)}</dd>\n"
        html += "</dl>\n"
    elif isinstance(data, list):
        html = "<ul>\n"
        for item in data:
            html += f"<li>{json_to_html(item, level + 1)}</li>\n"
        html += "</ul>\n"
    else:
        if isinstance(data, str):
            if data.startswith("http"):
                html = f'<a href="{escape(data)}" target="_blank">{escape(data)}</a>'
            else:
                html = f"<p>{parse_markdown_links(escape(data))}</p>"
        else:
            html = f"<p>{escape(str(data))}</p>"
    return html


def generate_html(input_file, output_file, title="JSON to HTML"):
    # Read JSON data from file
    with open(input_file, "r") as file:
        json_data = json.load(file)

    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(title)}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
        }}
        dl {{
            margin-left: 20px;
        }}
        dt {{
            font-weight: bold;
        }}
        dd {{
            margin-bottom: 10px;
        }}
        ul {{
            padding-left: 20px;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <h1>{escape(title)}</h1>
    {json_to_html(json_data)}
</body>
</html>
    """

    # Write HTML content to file
    with open(output_file, "w") as file:
        file.write(html_content)

    return html_content


def create_pdf(html_content, output_file):
    """
    Create a PDF file from HTML content.

    :param html_content: String containing HTML content
    :param output_file: String, path to the output PDF file
    :return: Boolean indicating success or failure
    """
    try:
        pdfkit.from_string(html_content, output_file)
        if os.path.exists(output_file):
            print(f"PDF file generated successfully: {output_file}")
            return True
        else:
            print(f"PDF file was not created at the specified location: {output_file}")
            return False
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        print("Make sure wkhtmltopdf is installed on your system.")
        return False


def process_json_to_html_and_pdf(json_file, html_file, pdf_file, author):
    # Generate HTML
    html_output = generate_html(json_file, html_file, f"Self Appraisal for {author}")

    # Create PDF
    pdf_created = create_pdf(html_output, pdf_file)

    if pdf_created:
        print("Both HTML and PDF files have been generated.")
    else:
        print("HTML file was generated, but there was an issue with PDF creation.")


def generate_weekly_report_docs(input_json_file: str, author):
    _generate_docs(input_json_file, author, "weekly_report")


def generate_appraisal_docs(input_json_file: str, author):
    _generate_docs(input_json_file, author, "appraisal")


def _generate_docs(input_json_file: str, author, doc_type):
    # Use the current working directory
    current_dir = os.getcwd()

    # Define input and output file paths
    html_file = os.path.join(current_dir, f"{doc_type}.html")
    pdf_file = os.path.join(current_dir, f"{doc_type}.pdf")

    process_json_to_html_and_pdf(input_json_file, html_file, pdf_file, author)

    print(f"Current working directory: {current_dir}")
    print(f"JSON file path: {input_json_file}")
    print(f"HTML file path: {html_file}")
    print(f"PDF file path: {pdf_file}")


def get_last_calendar_year_dates():
    # Get current year
    current_year = datetime.now().year

    # Set last year
    last_year = current_year - 1

    # Create start date: January 1st of last year at 00:00
    start_date = datetime(last_year, 1, 1, 0, 0)

    # Create end date: December 31st of last year at 23:59
    end_date = datetime(last_year, 12, 31, 23, 59)

    # Format dates as strings
    start_date_str = start_date.strftime("%Y-%m-%d %H:%M")
    end_date_str = end_date.strftime("%Y-%m-%d %H:%M")

    return start_date_str, end_date_str