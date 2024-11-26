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
            "Goal Achievement",
            "Employee Performance",
        ]
    )

    with tabs[0]:
        goal_achievement_tab(filtered_goals)

    with tabs[1]:
        employee_performance_tab(filtered_performers)


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


if __name__ == "__main__":
    director_performance_dashboard()
