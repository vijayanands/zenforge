from typing import Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ui.style import create_styled_tabs, create_styled_line_chart, create_styled_bar_chart, apply_styled_dropdown_css


# Dummy data generation functions
def get_dummy_employees() -> List[str]:
    return ["Alice", "Bob", "Charlie", "David", "Eve"]


def get_commits_per_developer(duration: str = "Quarterly") -> Dict[str, int]:
    employees = get_dummy_employees()
    multiplier = 1 if duration == "Monthly" else (3 if duration == "Quarterly" else 12)
    return {emp: np.random.randint(10, 100) * multiplier for emp in employees}


def get_pr_code_review_issues_tickets(duration: str) -> pd.DataFrame:
    employees = get_dummy_employees()
    multiplier = 1 if duration == "Monthly" else (3 if duration == "Quarterly" else 12)
    data = {
        "Employee": employees,
        "Pull Requests Merged": np.random.randint(5, 30, len(employees)) * multiplier,
        "Code Reviews Completed": np.random.randint(10, 50, len(employees))
        * multiplier,
        "Issues Resolved": np.random.randint(15, 60, len(employees)) * multiplier,
        "Tickets Assigned": np.random.randint(20, 70, len(employees)) * multiplier,
        "Tickets Resolved": np.random.randint(15, 65, len(employees)) * multiplier,
    }
    return pd.DataFrame(data)


def get_average_resolution_time(duration: str) -> Dict[str, float]:
    employees = get_dummy_employees()
    multiplier = (
        1 if duration == "Monthly" else (0.8 if duration == "Quarterly" else 0.6)
    )
    return {emp: np.random.uniform(1, 5) * multiplier for emp in employees}


def get_sprint_velocity(duration: str) -> pd.DataFrame:
    sprints = (
        range(1, 11)
        if duration == "Monthly"
        else (range(1, 5) if duration == "Quarterly" else range(1, 13))
    )
    story_points = np.random.randint(20, 100, len(sprints))
    return pd.DataFrame({"Sprint": sprints, "Story Points": story_points})


def get_bug_fix_rate(duration: str) -> Dict[str, float]:
    employees = get_dummy_employees()
    return {
        emp: min(
            1.0, np.random.uniform(0.5, 1.0) * (1.2 if duration != "Monthly" else 1)
        )
        for emp in employees
    }


def get_page_metrics(duration: str) -> pd.DataFrame:
    employees = get_dummy_employees()
    multiplier = 1 if duration == "Monthly" else (3 if duration == "Quarterly" else 12)
    data = {
        "Employee": employees,
        "Pages Created": np.random.randint(5, 30, len(employees)) * multiplier,
        "Edits and Updates": np.random.randint(20, 100, len(employees)) * multiplier,
        "Comments": np.random.randint(10, 50, len(employees)) * multiplier,
        "Collaborations": np.random.randint(5, 25, len(employees)) * multiplier,
    }
    return pd.DataFrame(data)


# Main Streamlit UI function
def manager_performance_dashboard():
    st.title("Performance Metrics and KPIs Dashboard")

    apply_styled_dropdown_css()

    # Add dropdowns for duration and employee selection
    col1, col2 = st.columns(2)
    with col1:
        duration = (
            st.selectbox("Select Duration", ["Monthly", "Quarterly", "Yearly"], index=0)
            or "Monthly"
        )
    with col2:
        employees = get_dummy_employees()
        selected_employee = st.selectbox("Select Employee", ["All"] + employees)

    # Create tabs for different metric categories
    tabs = create_styled_tabs(["Code Metrics", "Sprint & Issues", "Page Metrics"])

    with tabs[0]:
        st.header("Code Metrics")
        col1, col2 = st.columns(2)

        with col1:
            # Commits per Developer
            commits_data = get_commits_per_developer(duration)
            if selected_employee != "All" and selected_employee is not None:
                commits_data = {selected_employee: commits_data[selected_employee]}
            create_styled_bar_chart(
                list(commits_data.keys()),
                list(commits_data.values()),
                "Developer",
                f"Number of Commits ({duration})",
                # f"Commits per Developer ({duration})"
            )

        with col2:
            # Bug Fix Rate
            bug_fix_data = get_bug_fix_rate(duration)
            if selected_employee != "All" and selected_employee is not None:
                bug_fix_data = {selected_employee: bug_fix_data[selected_employee]}
            create_styled_bar_chart(
                list(bug_fix_data.keys()),
                list(bug_fix_data.values()),
                "Developer",
                "Bug Fix Rate",
                # f"Bug Fix Rate per Developer ({duration})"
            )

    with tabs[1]:
        st.header("Sprint & Issues Metrics")
        col1, col2 = st.columns(2)

        with col1:
            # Sprint Velocity
            sprint_data = get_sprint_velocity(duration)
            create_styled_line_chart(
                sprint_data["Story Points"],
                "Sprint",
                "Story Points",
                # f"Sprint Velocity (Story Points per Sprint) ({duration})"
            )

        with col2:
            # Average Resolution Time
            resolution_time_data = get_average_resolution_time(duration)
            if selected_employee != "All" and selected_employee is not None:
                resolution_time_data = {
                    selected_employee: resolution_time_data[selected_employee]
                }
            create_styled_bar_chart(
                list(resolution_time_data.keys()),
                list(resolution_time_data.values()),
                "Developer",
                f"Average Resolution Time (days) ({duration})",
                # f"Average Resolution Time per Developer ({duration})"
            )
        # Pull Requests, Code Reviews, Issues, and Tickets
        st.subheader("Pull Requests, Code Reviews, Issues, and Tickets")
        pr_review_data = get_pr_code_review_issues_tickets(duration)
        if selected_employee != "All":
            pr_review_data = pr_review_data[
                pr_review_data["Employee"] == selected_employee
            ]
        st.dataframe(pr_review_data, use_container_width=True)

    with tabs[2]:
        st.header("Page Metrics")
        # Page Metrics
        page_metrics_data = get_page_metrics(duration)
        if selected_employee != "All":
            page_metrics_data = page_metrics_data[
                page_metrics_data["Employee"] == selected_employee
            ]

        col1, col2 = st.columns(2)

        with col1:
            fig_pages = px.bar(
                page_metrics_data,
                x="Employee",
                y="Pages Created",
                title=f"Pages Created per Employee ({duration})",
            )
            st.plotly_chart(fig_pages, use_container_width=True)

        with col2:
            fig_edits = px.bar(
                page_metrics_data,
                x="Employee",
                y="Edits and Updates",
                title=f"Edits and Updates per Employee ({duration})",
            )
            st.plotly_chart(fig_edits, use_container_width=True)

        st.subheader("Detailed Page Metrics")
        st.dataframe(page_metrics_data, use_container_width=True)


# Example usage
if __name__ == "__main__":
    manager_performance_dashboard()
