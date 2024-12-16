import json
import os
import re
from html import escape

# Add error handling for pdfkit import
try:
    import pdfkit

    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False
    print("pdfkit is not installed. PDF generation will be unavailable.")


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
    if not PDFKIT_AVAILABLE:
        print("Cannot create PDF: pdfkit is not installed.")
        return False

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


def generate_appraisal_docs(input_json_file: str, author):
    # Use the current working directory
    current_dir = os.getcwd()

    # Define input and output file paths
    html_file = os.path.join(current_dir, "appraisal.html")
    pdf_file = os.path.join(current_dir, "appraisal.pdf")

    process_json_to_html_and_pdf(input_json_file, html_file, pdf_file, author)

    print(f"Current working directory: {current_dir}")
    print(f"JSON file path: {input_json_file}")
    print(f"HTML file path: {html_file}")
    print(f"PDF file path: {pdf_file}")


# Example usage
# if __name__ == "__main__":
#     generate_appraisal_docs()
