from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from model.events_data_generator import get_sample_data


def load_project_data(data: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """Convert raw project data into DataFrames for analysis"""

    # Process pull requests and code reviews
    pr_data = []
    for pr in data["pull_requests"]:
        review_time = None
        if pr["merged_at"] and pr["created_at"]:
            review_time = (pr["merged_at"] - pr["created_at"]).total_seconds() / (
                24 * 3600
            )  # in days

        pr_data.append(
            {
                "project_id": pr["project_id"],
                "pr_id": pr["id"],
                "created_at": pr["created_at"],
                "merged_at": pr["merged_at"],
                "status": pr["status"],
                "review_time_days": review_time,
            }
        )

    # Process PR comments
    comment_data = []
    for comment in data["pr_comments"]:
        comment_data.append(
            {
                "pr_id": comment["pr_id"],
                "created_at": comment["created_at"],
                "author": comment["author"],
            }
        )

    # Process bugs
    bug_data = []
    for bug in data["bugs"]:
        resolution_time = None
        if bug["resolved_date"] and bug["created_date"]:
            resolution_time = (
                bug["resolved_date"] - bug["created_date"]
            ).total_seconds() / (24 * 3600)

        bug_data.append(
            {
                "project_id": bug["project_id"],
                "bug_id": bug["id"],
                "created_date": bug["created_date"],
                "resolved_date": bug["resolved_date"],
                "status": bug["status"],
                "resolution_time_days": resolution_time,
                "severity": bug["severity"],
                "impact_area": bug["impact_area"],
            }
        )

    return {
        "prs": pd.DataFrame(pr_data),
        "comments": pd.DataFrame(comment_data),
        "bugs": pd.DataFrame(bug_data),
    }


def analyze_code_review_metrics(
    prs_df: pd.DataFrame, comments_df: pd.DataFrame
) -> pd.DataFrame:
    """Calculate code review metrics per project"""
    metrics = []

    for project_id in prs_df["project_id"].unique():
        project_prs = prs_df[prs_df["project_id"] == project_id]

        # Get PR comments for this project
        project_pr_ids = project_prs["pr_id"].unique()
        project_comments = comments_df[comments_df["pr_id"].isin(project_pr_ids)]

        metrics.append(
            {
                "project_id": project_id,
                "avg_review_time": project_prs["review_time_days"].mean(),
                "pr_merge_rate": (project_prs["status"] == "MERGED").mean(),
                "avg_comments_per_pr": (
                    len(project_comments) / len(project_prs)
                    if len(project_prs) > 0
                    else 0
                ),
                "blocked_pr_rate": (project_prs["status"] == "BLOCKED").mean(),
                "total_prs": len(project_prs),
            }
        )

    return pd.DataFrame(metrics)


def analyze_bug_metrics(bugs_df: pd.DataFrame) -> pd.DataFrame:
    """Calculate bug resolution metrics per project"""
    metrics = []

    for project_id in bugs_df["project_id"].unique():
        project_bugs = bugs_df[bugs_df["project_id"] == project_id]

        metrics.append(
            {
                "project_id": project_id,
                "avg_resolution_time": project_bugs["resolution_time_days"].mean(),
                "resolution_rate": (
                    project_bugs["status"].isin(["FIXED", "CLOSED"])
                ).mean(),
                "blocked_bug_rate": (project_bugs["status"] == "BLOCKED").mean(),
                "total_bugs": len(project_bugs),
                "p0_bug_count": len(project_bugs[project_bugs["severity"] == "P0"]),
            }
        )

    return pd.DataFrame(metrics)


def create_bottleneck_visualization():
    st.title("Project Bottleneck Analysis Dashboard")

    # Load and process data
    sample_data = get_sample_data()  # Your data loading function
    dfs = load_project_data(sample_data)

    # Calculate metrics
    code_review_metrics = analyze_code_review_metrics(dfs["prs"], dfs["comments"])
    bug_metrics = analyze_bug_metrics(dfs["bugs"])

    # 1. Code Review Bottleneck Analysis
    st.header("Code Review Bottleneck Analysis")

    # Review Time Distribution
    fig_review_time = px.bar(
        code_review_metrics,
        x="project_id",
        y="avg_review_time",
        title="Average PR Review Time by Project",
        labels={"avg_review_time": "Average Review Time (days)"},
    )
    st.plotly_chart(fig_review_time, use_container_width=True)

    # PR Metrics Comparison
    cols = st.columns(2)
    with cols[0]:
        fig_pr_rates = go.Figure()
        fig_pr_rates.add_trace(
            go.Bar(
                name="Merge Rate",
                x=code_review_metrics["project_id"],
                y=code_review_metrics["pr_merge_rate"],
                marker_color="green",
            )
        )
        fig_pr_rates.add_trace(
            go.Bar(
                name="Blocked Rate",
                x=code_review_metrics["project_id"],
                y=code_review_metrics["blocked_pr_rate"],
                marker_color="red",
            )
        )
        fig_pr_rates.update_layout(title="PR Merge vs Blocked Rates", barmode="group")
        st.plotly_chart(fig_pr_rates, use_container_width=True)

    with cols[1]:
        fig_comments = px.bar(
            code_review_metrics,
            x="project_id",
            y="avg_comments_per_pr",
            title="Average Comments per PR",
            color="avg_comments_per_pr",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig_comments, use_container_width=True)

    # 2. Bug Resolution Bottleneck Analysis
    st.header("Bug Resolution Bottleneck Analysis")

    # Resolution Time Distribution
    fig_resolution_time = px.bar(
        bug_metrics,
        x="project_id",
        y="avg_resolution_time",
        title="Average Bug Resolution Time by Project",
        labels={"avg_resolution_time": "Average Resolution Time (days)"},
    )
    st.plotly_chart(fig_resolution_time, use_container_width=True)

    # Bug Metrics Comparison
    cols = st.columns(2)
    with cols[0]:
        fig_bug_rates = go.Figure()
        fig_bug_rates.add_trace(
            go.Bar(
                name="Resolution Rate",
                x=bug_metrics["project_id"],
                y=bug_metrics["resolution_rate"],
                marker_color="green",
            )
        )
        fig_bug_rates.add_trace(
            go.Bar(
                name="Blocked Rate",
                x=bug_metrics["project_id"],
                y=bug_metrics["blocked_bug_rate"],
                marker_color="red",
            )
        )
        fig_bug_rates.update_layout(
            title="Bug Resolution vs Blocked Rates", barmode="group"
        )
        st.plotly_chart(fig_bug_rates, use_container_width=True)

    with cols[1]:
        fig_bug_counts = go.Figure()
        fig_bug_counts.add_trace(
            go.Bar(
                name="Total Bugs",
                x=bug_metrics["project_id"],
                y=bug_metrics["total_bugs"],
                marker_color="blue",
            )
        )
        fig_bug_counts.add_trace(
            go.Bar(
                name="P0 Bugs",
                x=bug_metrics["project_id"],
                y=bug_metrics["p0_bug_count"],
                marker_color="red",
            )
        )
        fig_bug_counts.update_layout(title="Total vs P0 Bugs", barmode="group")
        st.plotly_chart(fig_bug_counts, use_container_width=True)

    # 3. Project Timeline View with Bottlenecks
    st.header("Project Timeline with Bottlenecks")

    # Combine PR and Bug timelines
    timeline_data = []

    # Add PR timeline data
    for _, row in dfs["prs"].iterrows():
        if row["created_at"] and row["merged_at"]:
            timeline_data.append(
                {
                    "Project": row["project_id"],
                    "Type": "Code Review",
                    "Start": row["created_at"],
                    "End": row["merged_at"],
                    "Duration": (row["merged_at"] - row["created_at"]).total_seconds()
                    / (24 * 3600),
                }
            )

    # Add Bug timeline data
    for _, row in dfs["bugs"].iterrows():
        if row["created_date"] and row["resolved_date"]:
            timeline_data.append(
                {
                    "Project": row["project_id"],
                    "Type": "Bug Resolution",
                    "Start": row["created_date"],
                    "End": row["resolved_date"],
                    "Duration": (
                        row["resolved_date"] - row["created_date"]
                    ).total_seconds()
                    / (24 * 3600),
                }
            )

    timeline_df = pd.DataFrame(timeline_data)

    fig_timeline = px.timeline(
        timeline_df,
        x_start="Start",
        x_end="End",
        y="Project",
        color="Type",
        title="Project Timeline with Code Review and Bug Resolution Phases",
    )
    fig_timeline.update_layout(height=400)
    st.plotly_chart(fig_timeline, use_container_width=True)

    # 4. Bottleneck Impact Analysis
    st.header("Bottleneck Impact Analysis")

    # Calculate bottleneck impact scores
    impact_data = []
    for project_id in code_review_metrics["project_id"]:
        cr_metrics = code_review_metrics[
            code_review_metrics["project_id"] == project_id
        ].iloc[0]
        bug_metrics_row = bug_metrics[bug_metrics["project_id"] == project_id].iloc[0]

        cr_impact = (
            cr_metrics["avg_review_time"] * 0.4
            + cr_metrics["blocked_pr_rate"] * 0.3
            + (cr_metrics["avg_comments_per_pr"] / 10) * 0.3
        )

        bug_impact = (
            bug_metrics_row["avg_resolution_time"] * 0.4
            + bug_metrics_row["blocked_bug_rate"] * 0.3
            + (bug_metrics_row["p0_bug_count"] / bug_metrics_row["total_bugs"]) * 0.3
        )

        impact_data.append(
            {
                "Project": project_id,
                "Code Review Impact": cr_impact,
                "Bug Resolution Impact": bug_impact,
                "Total Impact": (cr_impact + bug_impact) / 2,
            }
        )

    impact_df = pd.DataFrame(impact_data)

    fig_impact = px.bar(
        impact_df,
        x="Project",
        y=["Code Review Impact", "Bug Resolution Impact"],
        title="Bottleneck Impact Analysis by Project",
        barmode="group",
    )
    st.plotly_chart(fig_impact, use_container_width=True)

    # 5. Detailed Metrics Table
    st.header("Detailed Metrics")

    # Combine all metrics
    detailed_metrics = pd.merge(
        code_review_metrics, bug_metrics, on="project_id", suffixes=("_pr", "_bug")
    )

    st.dataframe(detailed_metrics)


if __name__ == "__main__":
    create_bottleneck_visualization()
