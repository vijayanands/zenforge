import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from demo_code.ui.style import (
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


# Generate more realistic performance trend data
def generate_realistic_trends(start, end, periods):
    return [
        round(x + random.uniform(-0.2, 0.2), 2)
        for x in np.linspace(start, end, periods)
    ]


performance_trends = pd.DataFrame(
    {
        "month": pd.date_range(start="2023-01-01", periods=12, freq="ME"),
        "Sales": generate_realistic_trends(3.5, 4.0, 12),
        "Marketing": generate_realistic_trends(3.6, 4.1, 12),
        "Engineering": generate_realistic_trends(3.7, 4.2, 12),
        "Customer Support": generate_realistic_trends(3.4, 3.9, 12),
        "HR": generate_realistic_trends(3.5, 4.0, 12),
    }
)

# Other dummy data
all_performance_ratings = [
    {
        "department": "Sales",
        "exceptional": 12,
        "exceedsExpectations": 23,
        "meetsExpectations": 45,
        "needsImprovement": 15,
        "unsatisfactory": 5,
    },
    {
        "department": "Marketing",
        "exceptional": 8,
        "exceedsExpectations": 17,
        "meetsExpectations": 55,
        "needsImprovement": 18,
        "unsatisfactory": 2,
    },
    {
        "department": "Engineering",
        "exceptional": 15,
        "exceedsExpectations": 25,
        "meetsExpectations": 48,
        "needsImprovement": 10,
        "unsatisfactory": 2,
    },
    {
        "department": "Customer Support",
        "exceptional": 10,
        "exceedsExpectations": 20,
        "meetsExpectations": 52,
        "needsImprovement": 13,
        "unsatisfactory": 5,
    },
    {
        "department": "HR",
        "exceptional": 7,
        "exceedsExpectations": 18,
        "meetsExpectations": 60,
        "needsImprovement": 12,
        "unsatisfactory": 3,
    },
]

departmental_goals = [
    {"department": "Sales", "achieved": 85, "total": 100},
    {"department": "Marketing", "achieved": 72, "total": 100},
    {"department": "Engineering", "achieved": 95, "total": 100},
    {"department": "Customer Support", "achieved": 88, "total": 100},
    {"department": "HR", "achieved": 92, "total": 100},
]

all_performers = [
    {"name": "John Doe", "department": "Sales", "rating": 4.9},
    {"name": "Jane Smith", "department": "Engineering", "rating": 4.8},
    {"name": "Bob Johnson", "department": "Marketing", "rating": 4.7},
    {"name": "Alice Brown", "department": "Customer Support", "rating": 4.7},
    {"name": "Charlie Davis", "department": "HR", "rating": 4.6},
    {"name": "Eve Wilson", "department": "Sales", "rating": 2.1},
    {"name": "Frank Miller", "department": "Engineering", "rating": 2.2},
    {"name": "Grace Lee", "department": "Marketing", "rating": 2.3},
    {"name": "Henry Taylor", "department": "Customer Support", "rating": 2.4},
    {"name": "Ivy Clark", "department": "HR", "rating": 2.5},
]


# Generate more realistic and varied performance vs training data
def generate_performance_vs_training_data(departments, num_entries_per_dept=10):
    data = []
    for dept in departments:
        base_performance = random.uniform(3.0, 4.5)
        base_training_hours = random.uniform(20, 60)
        for _ in range(num_entries_per_dept):
            performance = base_performance + random.uniform(-0.5, 0.5)
            training_hours = base_training_hours + random.uniform(-10, 10)
            employees = random.randint(1, 10)
            data.append(
                {
                    "department": dept,
                    "avgPerformance": round(performance, 2),
                    "trainingHours": round(training_hours, 1),
                    "employees": employees,
                }
            )
    return data


def director_performance_dashboard():
    st.title("Performance Dashboard")
    apply_styled_dropdown_css()

    # Convert data to DataFrames
    df_performance_ratings = pd.DataFrame(all_performance_ratings)
    df_goals = pd.DataFrame(departmental_goals)
    df_performers = pd.DataFrame(all_performers)
    departments = ["Sales", "Marketing", "Engineering", "Customer Support"]
    df_performance_vs_training = pd.DataFrame(
        generate_performance_vs_training_data(departments)
    )

    # Calculate total employees and average performance per department
    df_performance_ratings["total_employees"] = df_performance_ratings.iloc[:, 1:].sum(
        axis=1
    )
    df_performance_ratings["avg_performance"] = (
        df_performance_ratings["exceptional"] * 5
        + df_performance_ratings["exceedsExpectations"] * 4
        + df_performance_ratings["meetsExpectations"] * 3
        + df_performance_ratings["needsImprovement"] * 2
        + df_performance_ratings["unsatisfactory"] * 1
    ) / df_performance_ratings["total_employees"]

    # Department selection dropdown with label
    departments = ["All"] + list(df_performance_ratings["department"])
    selected_department = st.selectbox(
        "Select Department",
        departments,
        key="department_selector",
        help="Choose a department to filter the dashboard data",
    )

    # Filter data based on selected department
    if selected_department == "All":
        filtered_performance_ratings = df_performance_ratings
        filtered_goals = df_goals
        filtered_performers = df_performers
        filtered_performance_vs_training = df_performance_vs_training
    else:
        filtered_performance_ratings = df_performance_ratings[
            df_performance_ratings["department"] == selected_department
        ]
        filtered_goals = df_goals[df_goals["department"] == selected_department]
        filtered_performers = df_performers[
            df_performers["department"] == selected_department
        ]
        filtered_performance_vs_training = df_performance_vs_training[
            df_performance_vs_training["department"] == selected_department
        ]

    # Use styled tabs
    tabs = create_styled_tabs(
        [
            "Performance Overview",
            "Goal Achievement",
            "Employee Performance",
            "Training Impact",
        ]
    )

    with tabs[0]:
        performance_overview_tab(filtered_performance_ratings, performance_trends)

    with tabs[1]:
        goal_achievement_tab(filtered_goals)

    with tabs[2]:
        employee_performance_tab(filtered_performers)

    with tabs[3]:
        training_impact_tab(filtered_performance_vs_training)


def performance_overview_tab(filtered_performance_ratings, performance_trends):
    st.header("Performance Ratings Distribution")

    # Use styled metrics for alerts
    worst_dept = filtered_performance_ratings.loc[
        filtered_performance_ratings["avg_performance"].idxmin()
    ]
    create_styled_metric(
        "Lowest Performing Department",
        f"{worst_dept['department']} ({worst_dept['avg_performance']:.2f})",
        "⚠️",
    )

    # Use styled pie chart for ratings distribution
    ratings_data = filtered_performance_ratings.melt(
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

    # Map ratings to numeric values and labels
    rating_map = {
        "exceptional": (5, "Exceptional (5)"),
        "exceedsExpectations": (4, "Exceeds Expectations (4)"),
        "meetsExpectations": (3, "Meets Expectations (3)"),
        "needsImprovement": (2, "Needs Improvement (2)"),
        "unsatisfactory": (1, "Unsatisfactory (1)"),
    }
    ratings_data["rating_value"] = ratings_data["rating"].map(
        lambda x: rating_map[x][0]
    )
    ratings_data["rating_label"] = ratings_data["rating"].map(
        lambda x: rating_map[x][1]
    )

    # Use a custom color sequence instead of RdYlGn
    custom_colors = ["#d7191c", "#fdae61", "#ffffbf", "#a6d96a", "#1a9641"]

    fig_ratings = create_pie_chart(
        ratings_data,
        names="rating_label",
        values="percentage",
        title="Performance Ratings Distribution",
        color_sequence=custom_colors[::-1],  # Reverse the color sequence
        hole=0.3,
    )
    display_pie_chart(fig_ratings)

    # Use styled line chart for performance trends
    st.subheader("Performance Trends")
    for department in performance_trends.columns[1:]:
        create_styled_line_chart(
            performance_trends[department], "Month", f"{department} Performance Rating"
        )


def goal_achievement_tab(filtered_goals):
    st.header("Goal Achievement Rates")

    # Create a more intuitive list view for goal achievement
    for _, row in filtered_goals.iterrows():
        col1, col2, col3 = st.columns([2, 6, 2])
        with col1:
            st.subheader(row["department"])
        with col2:
            progress = row["achieved"] / row["total"]
            st.progress(progress)
        with col3:
            create_styled_metric(
                "Achieved",
                f"{row['achieved']}%",
                f"{row['achieved'] - row['total']}% from target",
            )

    # Add a summary chart
    create_styled_bar_chart(
        filtered_goals["department"],
        filtered_goals["achieved"],
        "Department",
        "Achievement (%)",
    )
    st.markdown("**Note:** The red dashed line indicates the 100% target.")


def employee_performance_tab(filtered_performers):
    st.header("Top and Bottom Performers")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Performers")
        top_performers = filtered_performers.nlargest(5, "rating")
        list = [
            f"{row['name']} ({row['department']}): {row['rating']}"
            for _, row in top_performers.iterrows()
        ]
        for item in list:
            st.write(f"• {item}")

    with col2:
        st.subheader("Bottom Performers")
        bottom_performers = filtered_performers.nsmallest(5, "rating")
        list = [
            f"{row['name']} ({row['department']}): {row['rating']}"
            for _, row in bottom_performers.iterrows()
        ]
        for item in list:
            st.write(f"• {item}")


def training_impact_tab(filtered_performance_vs_training):
    st.header("Training Impact")

    # Create a more intuitive visualization for training impact
    fig_training = px.scatter(
        filtered_performance_vs_training,
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
    st.plotly_chart(fig_training, use_container_width=True)

    # Add insights
    st.subheader("Insights")

    # Overall correlation
    overall_correlation = filtered_performance_vs_training["trainingHours"].corr(
        filtered_performance_vs_training["avgPerformance"]
    )

    # Create three columns for a better layout
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        create_styled_metric("Overall Correlation", f"{overall_correlation:.2f}", "📊")
        st.write(
            "A correlation close to 1 indicates a strong positive relationship between training hours and performance."
        )

    with col2:
        max_performance = filtered_performance_vs_training.loc[
            filtered_performance_vs_training["avgPerformance"].idxmax()
        ]
        create_styled_metric(
            "Highest Avg Performance",
            f"{max_performance['avgPerformance']:.2f}",
            f"{max_performance['department']}",
        )

    with col3:
        max_training = filtered_performance_vs_training.loc[
            filtered_performance_vs_training["trainingHours"].idxmax()
        ]
        create_styled_metric(
            "Most Training Hours",
            f"{max_training['trainingHours']}",
            f"{max_training['department']}",
        )

    # Interpretation of correlations
    st.subheader("Interpretation")
    list = [
        "A positive correlation indicates that as training hours increase, average performance tends to increase.",
        "A negative correlation suggests that as training hours increase, average performance tends to decrease.",
        "A correlation close to 0 indicates little to no linear relationship between training hours and performance.",
        "The strength of the relationship increases as the absolute value of the correlation approaches 1.",
    ]
    for item in list:
        st.write(f"• {item}")

    # Summary statistics
    st.subheader("Summary Statistics")
    summary_stats = (
        filtered_performance_vs_training.groupby("department")
        .agg(
            {
                "trainingHours": ["mean", "min", "max"],
                "avgPerformance": ["mean", "min", "max"],
                "employees": "sum",
            }
        )
        .reset_index()
    )
    summary_stats.columns = [
        "Department",
        "Avg Training Hours",
        "Min Training Hours",
        "Max Training Hours",
        "Avg Performance",
        "Min Performance",
        "Max Performance",
        "Total Employees",
    ]
    st.dataframe(summary_stats.round(2), use_container_width=True)


if __name__ == "__main__":
    director_performance_dashboard()
