import random
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ui.style import (apply_styled_dropdown_css, create_pie_chart,
                      create_styled_bar_chart, create_styled_bullet_list,
                      create_styled_line_chart, create_styled_metric,
                      create_styled_radio_buttons, create_styled_tabs,
                      display_pie_chart)


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

    # Generate time series data for productivity and performance trends
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

    # Training impact data
    training_impact = pd.DataFrame(
        [
            {
                "department": dept,
                "avgPerformance": random.uniform(3.0, 4.5),
                "trainingHours": random.uniform(20, 60),
                "employees": random.randint(10, 50),
            }
            for dept in departments
            for _ in range(10)  # 10 data points per department
        ]
    )

    return (
        productivity_data,
        projects_data,
        performance_ratings,
        trends,
        training_impact,
    )


def org_productivity_dashboard():
    st.title("Comprehensive Productivity & Performance Dashboard")
    apply_styled_dropdown_css()

    # Generate dummy data
    productivity_data, projects_data, performance_ratings, trends, training_impact = (
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
        training_impact = training_impact[
            training_impact["department"] == selected_department
        ]

    # Use styled tabs
    tabs = create_styled_tabs(
        [
            "Overview",
            "Project Status",
            "Performance Ratings",
            "Productivity Trends",
            "Training Impact",
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
        productivity_trends_tab(trends, selected_department)

    with tabs[4]:
        training_impact_tab(training_impact)

    with tabs[5]:
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


def productivity_trends_tab(trends, selected_department):
    st.header("Productivity and Performance Trends")

    # Date range selection
    date_range = st.date_input(
        "Select Date Range",
        value=(trends.index.min(), trends.index.max()),
        min_value=trends.index.min(),
        max_value=trends.index.max(),
    )

    # Filter data based on selection
    start_date, end_date = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
    filtered_trends = trends.loc[start_date:end_date]

    if selected_department == "All":
        # Show average trends across all departments
        productivity_avg = filtered_trends[
            [col for col in filtered_trends.columns if "productivity" in col]
        ].mean(axis=1)
        performance_avg = filtered_trends[
            [col for col in filtered_trends.columns if "performance" in col]
        ].mean(axis=1)

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=filtered_trends.index,
                y=productivity_avg,
                name="Avg Productivity",
                line=dict(color="blue"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=filtered_trends.index,
                y=performance_avg,
                name="Avg Performance",
                line=dict(color="green"),
            )
        )
    else:
        # Show trends for selected department
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=filtered_trends.index,
                y=filtered_trends[f"{selected_department}_productivity"],
                name="Productivity",
                line=dict(color="blue"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=filtered_trends.index,
                y=filtered_trends[f"{selected_department}_performance"],
                name="Performance",
                line=dict(color="green"),
            )
        )

    fig.update_layout(
        title="Productivity and Performance Trends",
        xaxis_title="Date",
        yaxis_title="Score",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Calculate and display metrics
    if selected_department == "All":
        avg_productivity = productivity_avg.mean()
        max_productivity = productivity_avg.max()
        min_productivity = productivity_avg.min()
    else:
        dept_productivity = filtered_trends[f"{selected_department}_productivity"]
        avg_productivity = dept_productivity.mean()
        max_productivity = dept_productivity.max()
        min_productivity = dept_productivity.min()

    col1, col2, col3 = st.columns(3)
    with col1:
        create_styled_metric("Average Productivity", f"{avg_productivity:.2f}", "📊")
    with col2:
        create_styled_metric("Max Productivity", f"{max_productivity:.2f}", "🔼")
    with col3:
        create_styled_metric("Min Productivity", f"{min_productivity:.2f}", "🔽")


def training_impact_tab(training_impact):
    st.header("Training Impact Analysis")

    # Scatter plot of training hours vs performance
    fig = px.scatter(
        training_impact,
        x="trainingHours",
        y="avgPerformance",
        size="employees",
        color="department",
        hover_name="department",
        title="Training Hours vs Average Performance",
        labels={
            "trainingHours": "Training Hours",
            "avgPerformance": "Average Performance",
            "employees": "Number of Employees",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    # Correlation analysis
    correlation = training_impact["trainingHours"].corr(
        training_impact["avgPerformance"]
    )
    create_styled_metric("Training-Performance Correlation", f"{correlation:.2f}", "📊")

    # Training efficiency by department
    st.subheader("Training Efficiency by Department")
    dept_efficiency = (
        training_impact.groupby("department")
        .apply(lambda x: x["avgPerformance"].mean() / x["trainingHours"].mean())
        .sort_values(ascending=False)
    )
    create_styled_bar_chart(
        dept_efficiency.index,
        dept_efficiency.values,
        "Department",
        "Training Efficiency (Perf/Hour)",
    )

    # Insights
    st.subheader("Key Insights")

    # Calculate additional metrics for insights
    avg_performance = training_impact["avgPerformance"].mean()
    high_performers = training_impact[
        training_impact["avgPerformance"] > avg_performance
    ]
    low_performers = training_impact[
        training_impact["avgPerformance"] <= avg_performance
    ]

    high_perf_avg_hours = high_performers["trainingHours"].mean()
    low_perf_avg_hours = low_performers["trainingHours"].mean()

    most_efficient_dept = dept_efficiency.index[0]
    least_efficient_dept = dept_efficiency.index[-1]

    insights = [
        f"The correlation between training hours and performance is {correlation:.2f}, indicating a {'weak' if abs(correlation) < 0.3 else 'moderate' if abs(correlation) < 0.5 else 'strong'} {'positive' if correlation > 0 else 'negative'} relationship.",
        f"{most_efficient_dept} shows the highest training efficiency at {dept_efficiency.iloc[0]:.2f} performance points per training hour.",
        f"High-performing employees (above average) receive an average of {high_perf_avg_hours:.1f} training hours, compared to {low_perf_avg_hours:.1f} hours for lower-performing employees.",
        f"Consider reviewing and potentially increasing training hours for {least_efficient_dept}, which shows the lowest training efficiency.",
        f"Evaluate the training programs of {most_efficient_dept} for potential best practices that could be applied to other departments.",
    ]
    for insight in insights:
        st.write(f"• {insight}")


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

    # Risk vs Completion scatter plot
    st.subheader("Risk vs Project Completion")
    risk_numeric = {"low": 1, "medium": 2, "high": 3}
    projects_data["risk_numeric"] = projects_data["risk"].map(risk_numeric)

    fig = px.scatter(
        projects_data,
        x="completion",
        y="risk_numeric",
        color="department",
        size="risk_numeric",
        hover_name="name",
        labels={"completion": "Project Completion (%)", "risk_numeric": "Risk Level"},
        title="Project Risk vs Completion",
    )
    fig.update_yaxes(tickvals=[1, 2, 3], ticktext=["Low", "Medium", "High"])
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    org_productivity_dashboard()
