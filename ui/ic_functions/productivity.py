import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def get_employee_jira_data():
    # Generate dummy Jira data
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "issues_created": [random.randint(0, 5) for _ in range(30)],
        "issues_resolved": [random.randint(0, 4) for _ in range(30)],
    }
    return pd.DataFrame(data)


def get_employee_confluence_data():
    # Generate dummy Confluence data
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "pages_created": [random.randint(0, 2) for _ in range(30)],
        "pages_edited": [random.randint(0, 3) for _ in range(30)],
    }
    return pd.DataFrame(data)


def get_employee_github_data():
    # Generate dummy GitHub data
    date_range = pd.date_range(end=datetime.now(), periods=30)
    data = {
        "date": date_range,
        "commits": [random.randint(0, 10) for _ in range(30)],
        "pull_requests": [random.randint(0, 2) for _ in range(30)],
    }
    return pd.DataFrame(data)


def predict_productivity(jira_data, confluence_data, github_data):
    # This is a very simplistic prediction model
    total_jira_issues = jira_data["issues_resolved"].sum()
    total_confluence_edits = confluence_data["pages_edited"].sum()
    total_github_commits = github_data["commits"].sum()

    productivity_score = (
        total_jira_issues * 0.4
        + total_confluence_edits * 0.3
        + total_github_commits * 0.3
    )

    return min(productivity_score / 100, 1.0)  # Normalize to 0-1 range


def display_productivity_stats():
    st.subheader("Your Productivity Statistics")

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

    # Jira Chart
    fig_jira = px.line(
        jira_data,
        x="date",
        y=["issues_created", "issues_resolved"],
        title="Your Jira Activity",
    )
    st.plotly_chart(fig_jira)

    # Confluence Chart
    fig_confluence = px.line(
        confluence_data,
        x="date",
        y=["pages_created", "pages_edited"],
        title="Your Confluence Activity",
    )
    st.plotly_chart(fig_confluence)

    # GitHub Chart
    fig_github = px.line(
        github_data,
        x="date",
        y=["commits", "pull_requests"],
        title="Your GitHub Activity",
    )
    st.plotly_chart(fig_github)

    # Productivity Prediction
    productivity = predict_productivity(jira_data, confluence_data, github_data)
    fig_productivity = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=productivity,
            title={"text": "Your Predicted Productivity"},
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


def productivity_tab():
    st.header("Your Productivity Dashboard")
    display_productivity_stats()
