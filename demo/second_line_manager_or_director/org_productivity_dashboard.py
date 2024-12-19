import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from demo.ui.style import (
    apply_styled_dropdown_css,
    create_pie_chart,
    create_styled_bar_chart,
    create_styled_bullet_list,
    create_styled_line_chart,
    create_styled_metric,
    create_styled_radio_buttons,
    create_styled_tabs,
    display_pie_chart,
)


# Generate dummy data
def generate_dummy_data():
    # Departments
    departments = ["Engineering", "Marketing", "Sales", "Customer Support"]

    # Productivity data
    productivity_data = pd.DataFrame(
        [
            {"department": dept, "productivity": random.randint(70, 95)}
            for dept in departments
        ]
    )

    # Projects data
    projects_data = pd.DataFrame(
        [
            {
                "id": 1,
                "name": "Website Redesign",
                "department": "Marketing",
                "completion": 75,
                "status": "on-track",
                "risk": "low",
            },
            {
                "id": 2,
                "name": "Mobile App Development",
                "department": "Engineering",
                "completion": 40,
                "status": "delayed",
                "risk": "medium",
            },
            {
                "id": 3,
                "name": "CRM Integration",
                "department": "Sales",
                "completion": 90,
                "status": "on-track",
                "risk": "low",
            },
            {
                "id": 4,
                "name": "Data Migration",
                "department": "Engineering",
                "completion": 60,
                "status": "on-track",
                "risk": "high",
            },
            {
                "id": 5,
                "name": "Security Audit",
                "department": "Engineering",
                "completion": 30,
                "status": "delayed",
                "risk": "medium",
            },
        ]
    )

    # Performance ratings data
    performance_ratings = pd.DataFrame(
        [
            {
                "department": dept,
                "exceptional": random.randint(5, 15),
                "exceedsExpectations": random.randint(15, 25),
                "meetsExpectations": random.randint(40, 60),
                "needsImprovement": random.randint(10, 20),
                "unsatisfactory": random.randint(1, 5),
            }
            for dept in departments
        ]
    )

    # Calculate total employees and average performance per department
    performance_ratings["total_employees"] = performance_ratings.iloc[:, 1:].sum(axis=1)
    performance_ratings["avg_performance"] = (
        performance_ratings["exceptional"] * 5
        + performance_ratings["exceedsExpectations"] * 4
        + performance_ratings["meetsExpectations"] * 3
        + performance_ratings["needsImprovement"] * 2
        + performance_ratings["unsatisfactory"] * 1
    ) / performance_ratings["total_employees"]

    # Generate time series data for productivity trends
    date_range = pd.date_range(start="2023-01-01", end="2023-12-31", freq="D")
    trends = pd.DataFrame(index=date_range)

    for dept in departments:
        base_productivity = productivity_data[productivity_data["department"] == dept][
            "productivity"
        ].values[0]
        base_performance = performance_ratings[
            performance_ratings["department"] == dept
        ]["avg_performance"].values[0]

        trends[f"{dept}_productivity"] = [
            base_productivity + random.uniform(-5, 5) for _ in range(len(date_range))
        ]
        trends[f"{dept}_performance"] = [
            base_performance + random.uniform(-0.5, 0.5) for _ in range(len(date_range))
        ]

    return (
        productivity_data,
        projects_data,
        performance_ratings,
        trends,
    )


def org_productivity_dashboard():
    st.title("Comprehensive Productivity & Performance Dashboard")
    apply_styled_dropdown_css()

    # Generate dummy data
    productivity_data, projects_data, performance_ratings, trends = (
        generate_dummy_data()
    )

    # Department selection
    departments = ["All"] + productivity_data["department"].tolist()
    selected_department = st.selectbox("Select Department", departments)

    # Filter data based on selected department
    if selected_department != "All":
        productivity_data = productivity_data[
            productivity_data["department"] == selected_department
        ]
        projects_data = projects_data[
            projects_data["department"] == selected_department
        ]
        performance_ratings = performance_ratings[
            performance_ratings["department"] == selected_department
        ]

    # Use styled tabs
    tabs = create_styled_tabs(
        [
            "Overview",
            "Project Status",
            "Performance Ratings",
            "Risk Assessment",
        ]
    )

    with tabs[0]:
        overview_tab(productivity_data, projects_data, performance_ratings)

    with tabs[1]:
        project_status_tab(projects_data)

    with tabs[2]:
        performance_ratings_tab(performance_ratings)

    with tabs[3]:
        risk_assessment_tab(projects_data)


def overview_tab(productivity_data, projects_data, performance_ratings):
    st.header("Organizational Overview")

    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        create_styled_metric(
            "Avg Productivity", f"{productivity_data['productivity'].mean():.1f}%", "📊"
        )
    with col2:
        create_styled_metric(
            "Avg Performance",
            f"{performance_ratings['avg_performance'].mean():.2f}",
            "⭐",
        )
    with col3:
        create_styled_metric("Total Projects", len(projects_data), "📁")
    with col4:
        on_track_count = len(projects_data[projects_data["status"] == "on-track"])
        on_track_percentage = (on_track_count / len(projects_data)) * 100
        create_styled_metric(
            "On-Track Projects", f"{on_track_count} ({on_track_percentage:.0f}%)", "✅"
        )

    # Productivity heatmap
    st.subheader("Departmental Productivity")
    fig = px.imshow(
        [productivity_data["productivity"]],
        x=productivity_data["department"],
        y=["Productivity Score"],
        color_continuous_scale="RdYlGn",
        text_auto=True,
        aspect="auto",
        title="Team Productivity Heatmap",
    )
    fig.update_layout(height=200)
    st.plotly_chart(fig, use_container_width=True)

    # Project status summary
    st.subheader("Project Status Summary")
    status_counts = projects_data["status"].value_counts()
    fig = create_pie_chart(
        status_counts,
        names=status_counts.index,
        values=status_counts.values,
        title="Project Status Distribution",
        color_sequence=["green", "orange", "red"],
    )
    display_pie_chart(fig)

    # Department productivity bar chart
    create_styled_bar_chart(
        productivity_data["department"],
        productivity_data["productivity"],
        "Department",
        "Productivity Score",
    )


def project_status_tab(projects_data):
    st.header("Project Status")

    # Project selection
    selected_project = st.selectbox("Select a project", projects_data["name"])
    project = projects_data[projects_data["name"] == selected_project].iloc[0]

    # Project details
    col1, col2 = st.columns(2)
    with col1:
        status_color = "green" if project["status"] == "on-track" else "orange"
        st.markdown(
            f"**Status:** <span style='color:{status_color};'>●</span> {project['status'].capitalize()}",
            unsafe_allow_html=True,
        )

        risk_color = {"low": "green", "medium": "orange", "high": "red"}[
            project["risk"]
        ]
        st.markdown(
            f"**Risk:** <span style='color:{risk_color};'>●</span> {project['risk'].capitalize()}",
            unsafe_allow_html=True,
        )

    with col2:
        st.metric("Completion", f"{project['completion']}%")
        st.progress(project["completion"] / 100)

    # All projects overview
    st.subheader("All Projects Overview")
    fig = go.Figure()
    for _, proj in projects_data.iterrows():
        fig.add_trace(
            go.Bar(
                x=[proj["name"]],
                y=[proj["completion"]],
                name=proj["name"],
                marker_color="green" if proj["status"] == "on-track" else "orange",
            )
        )
    fig.update_layout(
        title="Project Completion Status",
        xaxis_title="Project",
        yaxis_title="Completion (%)",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)


def performance_ratings_tab(performance_ratings):
    st.header("Performance Ratings Distribution")

    # Use styled pie chart for ratings distribution
    ratings_data = performance_ratings.melt(
        id_vars=["department", "total_employees"],
        value_vars=[
            "exceptional",
            "exceedsExpectations",
            "meetsExpectations",
            "needsImprovement",
            "unsatisfactory",
        ],
        var_name="rating",
        value_name="count",
    )
    ratings_data["percentage"] = (
        ratings_data["count"] / ratings_data["total_employees"] * 100
    )

    # Map ratings to labels
    rating_map = {
        "exceptional": "Exceptional (5)",
        "exceedsExpectations": "Exceeds Expectations (4)",
        "meetsExpectations": "Meets Expectations (3)",
        "needsImprovement": "Needs Improvement (2)",
        "unsatisfactory": "Unsatisfactory (1)",
    }
    ratings_data["rating_label"] = ratings_data["rating"].map(rating_map)

    # Create a custom color sequence
    custom_color_sequence = ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"]

    fig_ratings = create_pie_chart(
        ratings_data,
        names="rating_label",
        values="percentage",
        title="Performance Ratings Distribution",
        color_sequence=custom_color_sequence,
        hole=0.3,
    )
    display_pie_chart(fig_ratings)

    # Average performance by department
    st.subheader("Average Performance by Department")
    create_styled_bar_chart(
        performance_ratings["department"],
        performance_ratings["avg_performance"],
        "Department",
        "Average Performance",
    )


def risk_assessment_tab(projects_data):
    st.header("Risk Assessment")

    # Count projects by risk level
    risk_counts = projects_data["risk"].value_counts()

    # Create pie chart
    fig = create_pie_chart(
        risk_counts,
        names=risk_counts.index,
        values=risk_counts.values,
        title="Project Risk Distribution",
        color_sequence=["green", "orange", "red"],
    )
    display_pie_chart(fig)

    # List high-risk projects
    high_risk_projects = projects_data[projects_data["risk"] == "high"]
    if not high_risk_projects.empty:
        st.subheader("High Risk Projects")
        for project in high_risk_projects["name"].tolist():
            st.write(f"• {project}")
    else:
        st.info("No high-risk projects at the moment.")

    # Risk mitigation strategies
    st.subheader("Risk Mitigation Strategies")
    strategies = [
        "Conduct regular risk assessment meetings",
        "Implement robust testing procedures",
        "Maintain open communication channels with stakeholders",
        "Develop contingency plans for high-risk areas",
        "Provide additional resources to high-risk projects",
    ]
    for strategy in strategies:
        st.write(f"• {strategy}")


if __name__ == "__main__":
    org_productivity_dashboard()
