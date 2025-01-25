import json
import os
import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from demo.metrics.development_cycle_metrics import display_development_cycle_metrics
from demo.metrics.productivity_dashboard import display_productivity_dashboard
from functions.self_appraisal import create_self_appraisal
from functions.weekly_report import create_weekly_report
from functions.ingestion import answer_question, ingest_data

def ask(llm, query, index):
    enhanced_query = f"Based on the jira, github and the confluence data in the embedded json data, please answer my {query}"
    query_engine = index.as_query_engine(llm=llm)
    response = query_engine.query(enhanced_query)
    return response, response.response  # Return both full response and text


def reset_performance_management():
    if "appraisal" in st.session_state:
        del st.session_state.appraisal
    st.session_state.reset_appraisal = True


def pretty_print_appraisal(appraisal_data):
    # Convert string to dictionary if needed
    if isinstance(appraisal_data, str):
        try:
            appraisal_data = json.loads(appraisal_data)
        except json.JSONDecodeError:
            st.error("Invalid JSON string provided. Please check the input.")
            return

    if not isinstance(appraisal_data, dict):
        st.error("Input must be a dictionary or a valid JSON string.")
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Self-Appraisal")

    with col2:
        st.button(
            "Reset",
            on_click=reset_performance_management,
            key="reset_performance_header",
        )

    # Summary
    if "Summary" in appraisal_data:
        st.subheader("Summary")
        st.write(appraisal_data["Summary"])

    # Key Achievements
    if "Key Achievements" in appraisal_data:
        st.subheader("Key Achievements")
        for achievement in appraisal_data["Key Achievements"]:
            st.markdown(f"• {achievement}")

    # Contributions
    if "Contributions" in appraisal_data:
        st.subheader("Contributions")
        for platform, contribution in appraisal_data["Contributions"].items():
            st.markdown(f"**{platform}**")
            st.write(contribution)
            st.markdown("---")

    # Learning Opportunities
    if "Learning Opportunities" in appraisal_data:
        st.subheader("Learning Opportunities")
        for opportunity in appraisal_data["Learning Opportunities"]:
            st.markdown(f"• {opportunity}")


def perform_self_appraisal():
    if "reset_appraisal" in st.session_state and st.session_state.reset_appraisal:
        if "appraisal" in st.session_state:
            del st.session_state.appraisal
        del st.session_state.reset_appraisal

    if st.button("Generate Self-Appraisal", key="generate_button"):
        user_email = "vijayanands@gmail.com"
        with st.spinner(f"Generating self-appraisal for {user_email} ..."):
            st.session_state.appraisal = create_self_appraisal(user_email)

    if "appraisal" in st.session_state:
        pretty_print_appraisal(st.session_state.appraisal)
        st.button(
            "Reset",
            on_click=reset_performance_management,
            key="reset_performance_bottom",
        )


def load_qa_data():
    with st.spinner("Ingesting data... This may take a moment."):
        index = ingest_data()
        if index is None:
            st.error(
                "Failed to initialize the index. Please check the logs and try again."
            )
            return None
        return index


def q_and_a_tab():
    if "qa_index" not in st.session_state:
        st.session_state.qa_index = load_qa_data()

    if st.session_state.qa_index is None:
        return

    # Initialize session state for storing the last question and answer
    if "last_question" not in st.session_state:
        st.session_state.last_question = ""
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = ""

    # Get the logged-in user's email
    user_email = "vijayanands@gmail.com"

    query = st.text_input("Enter your question:", key="query_input")
    show_full_response = os.getenv("SHOW_CHATBOT_DEBUG_LOG", "false").lower() == "true"

    if st.button("Ask", key="ask_button"):
        if not query.strip():
            st.error("Please enter a question before clicking 'Ask'.")
        else:
            with st.spinner("Generating Answer..."):
                try:
                    response = answer_question(
                        st.session_state.qa_index, user_email, query
                    )

                    # Store the question and answer in session state
                    st.session_state.last_question = query
                    st.session_state.last_answer = response

                except Exception as e:
                    st.error(
                        f"An error occurred while processing your question: {str(e)}"
                    )

    # Display the last question and answer if they exist
    if st.session_state.last_question:
        st.subheader("Question:")
        st.write(st.session_state.last_question)
        st.subheader("Answer:")
        st.write(st.session_state.last_answer)

        if show_full_response:
            st.write("Full Response (Debug):")
            st.write(response)  # This will show the full response object if available

    # Add a note about the context of the answers
    st.info(f"Answers are based on the data available for {user_email}.")

# New functions for manager dashboard functionality
def get_dummy_employees():
    return [
        {"id": 1, "name": "Alice Johnson", "email": "alice@example.com"},
        {"id": 2, "name": "Bob Smith", "email": "bob@example.com"},
        {"id": 3, "name": "Charlie Brown", "email": "charlie@example.com"},
        {"id": 4, "name": "Diana Ross", "email": "diana@example.com"},
    ]


def get_employee_jira_data():
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "issues_created": [random.randint(0, 5) for _ in range(30)],
        "issues_resolved": [random.randint(0, 4) for _ in range(30)],
    }
    return pd.DataFrame(data)


def get_employee_confluence_data():
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "pages_created": [random.randint(0, 2) for _ in range(30)],
        "pages_edited": [random.randint(0, 3) for _ in range(30)],
    }
    return pd.DataFrame(data)


def get_employee_github_data():
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "commits": [random.randint(0, 10) for _ in range(30)],
        "pull_requests": [random.randint(0, 2) for _ in range(30)],
    }
    return pd.DataFrame(data)


def predict_productivity(jira_data, confluence_data, github_data):
    total_jira_issues = jira_data["issues_resolved"].sum()
    total_confluence_edits = confluence_data["pages_edited"].sum()
    total_github_commits = github_data["commits"].sum()

    productivity_score = (
        total_jira_issues * 0.4
        + total_confluence_edits * 0.3
        + total_github_commits * 0.3
    )

    return min(productivity_score / 100, 1.0)


def display_employee_stats(employee):
    st.subheader(f"Statistics for {employee['name']}")

    jira_data = get_employee_jira_data()
    confluence_data = get_employee_confluence_data()
    github_data = get_employee_github_data()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Jira Issues Resolved", jira_data["issues_resolved"].sum())
    with col2:
        st.metric(
            "Total Confluence Pages Edited", confluence_data["pages_edited"].sum()
        )
    with col3:
        st.metric("Total GitHub Commits", github_data["commits"].sum())

    fig_jira = px.line(
        jira_data,
        x="date",
        y=["issues_created", "issues_resolved"],
        title="Jira Activity",
    )
    st.plotly_chart(fig_jira)

    fig_confluence = px.line(
        confluence_data,
        x="date",
        y=["pages_created", "pages_edited"],
        title="Confluence Activity",
    )
    st.plotly_chart(fig_confluence)

    fig_github = px.line(
        github_data, x="date", y=["commits", "pull_requests"], title="GitHub Activity"
    )
    st.plotly_chart(fig_github)

    productivity = predict_productivity(jira_data, confluence_data, github_data)
    fig_productivity = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=productivity,
            title={"text": "Predicted Productivity"},
            domain={"x": [0, 1], "y": [0, 1]},
            gauge={
                "axis": {"range": [0, 1]},
                "steps": [
                    {"range": [0, 0.3], "color": "lightgray"},
                    {"range": [0.3, 0.7], "color": "gray"},
                    {"range": [0.7, 1], "color": "darkgray"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 0.8,
                },
            },
        )
    )
    st.plotly_chart(fig_productivity)


# Define prompt options as constants
PROMPT_OPTIONS = [
    "Select an action",
    "Generate a self appraisal for me",
    "Generate a weekly report for me",
    "Show me productivity dashboard",
    "Show me statistics on SDLC timeline for my projects",
    "compare productivity data for employees in my team",
    "List me the top 5% performers in my organization",
    "List me the bottom 5% performers in my organization",
]

PROMPT_MAP = {
    PROMPT_OPTIONS[1]: "self_appraisal",
    PROMPT_OPTIONS[2]: "weekly_report",
    PROMPT_OPTIONS[3]: "producitity_dashboard",
    PROMPT_OPTIONS[4]: "sdlc_timeline_view",
    PROMPT_OPTIONS[5]: "compare_productivity_data",
    PROMPT_OPTIONS[6]: "top_performers",
    PROMPT_OPTIONS[7]: "bottom_performers",
}

def individual_contributor_dashboard_conversational():
    if "current_view" not in st.session_state:
        st.session_state.current_view = "main"

    if st.session_state.current_view != "main":
        if st.button("Back to Dashboard", key=f"back_{st.session_state.current_view}"):
            st.session_state.current_view = "main"
            st.session_state.selected_skill_for_improvement = None
            st.session_state.add_skill_mode = False
            st.session_state.skills_edit_mode = False
            st.rerun()

    if st.session_state.current_view == "main":
        selected_prompt = st.selectbox(
            "", PROMPT_OPTIONS, index=0, key="action_selector"
        )

        if selected_prompt != "Select an action":
            st.session_state.current_view = PROMPT_MAP.get(selected_prompt, selected_prompt)
            st.rerun()

        return selected_prompt  # Return the selected action

    elif st.session_state.current_view == "self_appraisal":
        perform_self_appraisal()
    elif st.session_state.current_view == "weekly_report":
        perform_weekly_report_generation()
    elif st.session_state.current_view == "producitity_dashboard":
        display_productivity_dashboard()
    elif st.session_state.current_view == "sdlc_timeline_view":
        display_development_cycle_metrics()
    else:
        st.error("Invalid view selected. Please go back to the main dashboard.")

    return st.session_state.current_view  # Return the current view for all cases

def perform_weekly_report_generation():
    if "reset_weekly_report" in st.session_state and st.session_state.reset_weekly_report:
        if "weekly_report" in st.session_state:
            del st.session_state.weekly_report
        del st.session_state.reset_weekly_report

    if st.button("Generate Weekly Report", key="generate_weekly_report_button"):
        user_email = "vijayanands@gmail.com"
        with st.spinner(f"Generating weekly report for {user_email} ..."):
            # Parse the JSON string into a dictionary
            weekly_report_str = create_weekly_report(user_email)
            st.session_state.weekly_report = json.loads(weekly_report_str)

    if "weekly_report" in st.session_state:
        pretty_print_weekly_report(st.session_state.weekly_report)
        st.button(
            "Reset",
            on_click=reset_weekly_report,
            key="reset_weekly_report_bottom",
        )

def reset_weekly_report():
    st.session_state.reset_weekly_report = True

def pretty_print_weekly_report(report):
    st.markdown("## Weekly Report")
    
    # Summary section
    st.markdown("### Summary")
    st.markdown(report["Summary"])  # Changed from "summary" to "Summary" to match the prompt template
    
    # Key Achievements
    st.markdown("### Key Achievements")
    for achievement in report["Key Achievements"]:  # Changed from "accomplishments" to "Key Achievements"
        st.markdown(f"- {achievement}")
    
    # Contributions
    st.markdown("### Contributions")
    for project, details in report["Contributions"].items():
        st.markdown(f"**{project}**")
        st.markdown(details)
    
    # Learning Opportunities
    if "Learning Opportunities" in report:
        st.markdown("### Learning Opportunities")
        for opportunity in report["Learning Opportunities"]:
            st.markdown(f"- {opportunity}")