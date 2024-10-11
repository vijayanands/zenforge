import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from ui.style import (apply_styled_dropdown_css, create_pie_chart,
                      create_progress_bar, create_styled_bar_chart,
                      create_styled_bullet_list, create_styled_line_chart,
                      create_styled_metric, create_styled_tabs,
                      display_pie_chart)


# Helper functions to generate dummy data for employee-level dashboard
def generate_employee_list():
    return ["John Doe", "Jane Smith", "Bob Johnson", "Alice Brown", "Charlie Davis"]


def generate_employee_position(employee):
    positions = {
        "John Doe": "Senior Developer",
        "Jane Smith": "Project Manager",
        "Bob Johnson": "UX Designer",
        "Alice Brown": "Data Analyst",
        "Charlie Davis": "Quality Assurance Specialist",
    }
    return positions.get(employee, "Employee")


def generate_productivity_score():
    return round(random.uniform(1, 10), 1)


def generate_task_data():
    total_tasks = random.randint(50, 100)
    completed = random.randint(20, total_tasks - 10)
    in_progress = total_tasks - completed
    on_track = random.randint(0, in_progress)
    overdue = in_progress - on_track
    return total_tasks, completed, in_progress, on_track, overdue


def generate_weekly_task_completion():
    return [random.randint(5, 20) for _ in range(12)]


def generate_communication_data():
    return {
        "avg_email_response_time": round(random.uniform(0.5, 4), 1),
        "meetings_attended": random.randint(10, 30),
        "feedback_implemented": random.randint(5, 15),
        "time_in_meetings": random.randint(10, 40),
    }


def generate_email_response_trend():
    return [round(random.uniform(0.5, 4), 1) for _ in range(12)]


def generate_knowledge_data():
    return {
        "articles_written": random.randint(1, 10),
        "articles_contributed": random.randint(5, 20),
        "training_sessions": random.randint(1, 5),
        "mentoring_hours": random.randint(5, 30),
        "documentation_contributions": random.randint(10, 50),
    }


def generate_recent_contributions():
    contributions = [
        "Updated user manual",
        "Created new onboarding guide",
        "Commented on API documentation",
        "Edited team best practices",
        "Contributed to project wiki",
    ]
    dates = [datetime.now() - timedelta(days=random.randint(1, 30)) for _ in range(5)]
    return list(zip(contributions, dates))


def generate_meeting_data():
    return {
        "organized": random.randint(5, 15),
        "attended": random.randint(20, 40),
        "avg_duration": round(random.uniform(0.5, 2), 1),
        "effectiveness": random.randint(1, 10),
        "weekly_time_percentage": random.randint(10, 40),
    }


def generate_raci_data():
    roles = ["Responsible", "Accountable", "Consulted", "Informed", "None"]
    return {role: random.randint(5, 25) for role in roles}


def generate_learning_data():
    courses = [
        "Python Advanced",
        "Machine Learning Basics",
        "Agile Methodologies",
        "Cloud Computing",
        "Data Visualization",
    ]
    certifications = [
        "AWS Certified Developer",
        "Scrum Master",
        "Google Analytics",
        "Cybersecurity Fundamentals",
    ]
    return {
        "courses_completed": random.sample(courses, random.randint(1, len(courses))),
        "certifications": random.sample(
            certifications, random.randint(1, len(certifications))
        ),
        "learning_hours": random.randint(20, 100),
        "conferences_attended": random.randint(1, 3),
        "skill_improvement": random.randint(1, 10),
    }


def generate_code_data():
    return {
        "quality_score": round(random.uniform(1, 10), 1),
        "peer_reviews": random.randint(5, 20),
        "refactoring_tasks": random.randint(2, 10),
        "features_developed": random.randint(1, 5),
        "bugs_fixed": {
            "low": random.randint(5, 15),
            "medium": random.randint(3, 10),
            "high": random.randint(1, 5),
            "critical": random.randint(0, 3),
        },
        "git_commits": random.randint(20, 100),
        "bug_fix_rate": round(random.uniform(0.5, 5), 1),
    }


# New function to generate team-level dummy data
def generate_team_dummy_data(num_teams, duration):
    teams = [f"Team {i}" for i in range(1, num_teams + 1)]
    dates = pd.date_range(end=datetime.now(), periods=duration, freq="D")

    data = []
    for team in teams:
        for date in dates:
            data.append(
                {
                    "Team": team,
                    "Date": date,
                    "Task Completion Rate": np.random.uniform(0.6, 1),
                    "Communication Efficiency Rate": np.random.uniform(0.7, 1),
                    "Knowledge Contributions": np.random.randint(0, 10),
                    "Meeting Effectiveness": np.random.uniform(0.5, 1),
                    "Average Meeting Duration": np.random.uniform(30, 120),
                    "Percentage Time in Meetings": np.random.uniform(0.1, 0.4),
                    "Action Items per Meeting": np.random.uniform(1, 5),
                    "Resolutions per Meeting": np.random.uniform(0.5, 3),
                }
            )

    return pd.DataFrame(data)


def aggregate_employee_data(num_employees):
    total_productivity_score = sum(
        generate_productivity_score() for _ in range(num_employees)
    )
    total_tasks, total_completed, total_in_progress, total_on_track, total_overdue = [
        sum(x) for x in zip(*[generate_task_data() for _ in range(num_employees)])
    ]

    aggregated_comm_data = {
        key: sum(generate_communication_data()[key] for _ in range(num_employees))
        for key in generate_communication_data().keys()
    }
    aggregated_comm_data["avg_email_response_time"] /= num_employees

    aggregated_knowledge_data = {
        key: sum(generate_knowledge_data()[key] for _ in range(num_employees))
        for key in generate_knowledge_data().keys()
    }

    aggregated_meeting_data = {
        key: sum(generate_meeting_data()[key] for _ in range(num_employees))
        for key in generate_meeting_data().keys()
    }
    aggregated_meeting_data["avg_duration"] /= num_employees
    aggregated_meeting_data["effectiveness"] = round(
        aggregated_meeting_data["effectiveness"] / num_employees
    )
    aggregated_meeting_data["weekly_time_percentage"] = round(
        aggregated_meeting_data["weekly_time_percentage"] / num_employees
    )

    aggregated_learning_data = {
        "courses_completed": list(
            set(
                [
                    course
                    for _ in range(num_employees)
                    for course in generate_learning_data()["courses_completed"]
                ]
            )
        ),
        "certifications": list(
            set(
                [
                    cert
                    for _ in range(num_employees)
                    for cert in generate_learning_data()["certifications"]
                ]
            )
        ),
        "learning_hours": sum(
            generate_learning_data()["learning_hours"] for _ in range(num_employees)
        ),
        "conferences_attended": sum(
            generate_learning_data()["conferences_attended"]
            for _ in range(num_employees)
        ),
        "skill_improvement": round(
            sum(
                generate_learning_data()["skill_improvement"]
                for _ in range(num_employees)
            )
            / num_employees,
            1,
        ),
    }

    aggregated_code_data = {
        key: (
            sum(generate_code_data()[key] for _ in range(num_employees))
            if key != "bugs_fixed"
            else {
                severity: sum(
                    generate_code_data()["bugs_fixed"][severity]
                    for _ in range(num_employees)
                )
                for severity in generate_code_data()["bugs_fixed"].keys()
            }
        )
        for key in generate_code_data().keys()
    }
    aggregated_code_data["quality_score"] = round(
        aggregated_code_data["quality_score"] / num_employees, 1
    )
    aggregated_code_data["bug_fix_rate"] = round(
        aggregated_code_data["bug_fix_rate"] / num_employees, 1
    )

    return {
        "productivity_score": round(total_productivity_score / num_employees, 1),
        "total_tasks": total_tasks,
        "completed_tasks": total_completed,
        "in_progress": total_in_progress,
        "on_track": total_on_track,
        "overdue": total_overdue,
        "weekly_completion": [
            sum(x)
            for x in zip(
                *[generate_weekly_task_completion() for _ in range(num_employees)]
            )
        ],
        "communication_data": aggregated_comm_data,
        "email_trend": [
            round(
                sum(generate_email_response_trend()[i] for _ in range(num_employees))
                / num_employees,
                1,
            )
            for i in range(12)
        ],
        "knowledge_data": aggregated_knowledge_data,
        "meeting_data": aggregated_meeting_data,
        "learning_data": aggregated_learning_data,
        "code_data": aggregated_code_data,
    }


# Combined styling function
def set_page_style():
    st.markdown(
        """
    <style>
    .main > div {
        padding-top: 2rem;
    }
    .plot-container {
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-radius: 5px;
        padding: 1rem;
        background-color: white;
    }
    .dataframe {
        font-size: 0.8rem;
    }
    .stAlert {
        border-radius: 5px;
    }
    h1 {
        color: #1E3A8A;
        padding-bottom: 1rem;
        border-bottom: 2px solid #E5E7EB;
    }
    h3 {
        color: #1E3A8A;
        margin-top: 2rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# Main Streamlit UI function
def productivity_dashboard():
    set_page_style()
    apply_styled_dropdown_css()
    st.title("Productivity Dashboard")

    # Main tabs
    main_tabs = create_styled_tabs(["Employee View", "Manager View"])

    with main_tabs[0]:
        employee_productivity_dashboard()

    with main_tabs[1]:
        manager_productivity_dashboard()


def employee_productivity_dashboard():
    st.header("Employee Productivity Dashboard")

    # Dropdowns for employee and duration
    col1, col2 = st.columns(2)
    with col1:
        employees = ["All Employees"] + generate_employee_list()
        selected_employee = st.selectbox(
            "Select Employee", employees, key="employee_select"
        )
    with col2:
        duration = st.selectbox(
            "Select Duration", ["Quarterly", "Yearly"], key="duration_select"
        )

    # Handle "All Employees" selection
    if selected_employee == "All Employees":
        num_employees = len(generate_employee_list())
        data = aggregate_employee_data(num_employees)
        employee_position = f"Team of {num_employees}"
        productivity_score = data["productivity_score"]
        total_tasks = data["total_tasks"]
        completed_tasks = data["completed_tasks"]
    else:
        data = {
            "productivity_score": generate_productivity_score(),
            "task_data": generate_task_data(),
            "communication_data": generate_communication_data(),
            "knowledge_data": generate_knowledge_data(),
            "meeting_data": generate_meeting_data(),
            "learning_data": generate_learning_data(),
            "code_data": generate_code_data(),
        }
        employee_position = generate_employee_position(selected_employee)
        productivity_score = data["productivity_score"]
        total_tasks, completed_tasks, _, _, _ = data["task_data"]

    # Display employee info and productivity score in a single row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        create_styled_metric("Employee", selected_employee, "👤")
    with col2:
        create_styled_metric("Position", employee_position, "💼")
    with col3:
        create_styled_metric("Productivity Score", f"{productivity_score}/10", "🌟")
    with col4:
        create_styled_metric("Total Tasks", total_tasks, "📋")
    with col5:
        create_styled_metric("Completed Tasks", completed_tasks, "✅")

    # Tabs
    tabs = create_styled_tabs(
        ["Tasks", "Communication", "Knowledge", "Meetings", "Learning", "Code"]
    )

    # Tab 1: Tasks
    with tabs[0]:
        st.header("Tasks")
        if selected_employee == "All Employees":
            total_tasks = data["total_tasks"]
            completed = data["completed_tasks"]
            in_progress = data["in_progress"]
            on_track = data["on_track"]
            overdue = data["overdue"]
            weekly_completion = data["weekly_completion"]
        else:
            total_tasks, completed, in_progress, on_track, overdue = data["task_data"]
            weekly_completion = generate_weekly_task_completion()

        # Task metrics in a single row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric("Total Tasks", total_tasks, "📋")
        with col2:
            create_styled_metric("Completed", completed, "✅")
        with col3:
            create_styled_metric("In Progress", in_progress, "🔄")
        with col4:
            create_styled_metric("On Track", on_track, "🎯")
        with col5:
            create_styled_metric("Overdue", overdue, "⏰")

        # Weekly Task Completion and Task Distribution in one row
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Weekly Task Completion Rate")
            create_styled_line_chart(weekly_completion, "Week", "Tasks Completed")

        with col2:
            st.subheader("Task Distribution")
            task_distribution = {
                "Status": ["Completed", "On Track", "Overdue"],
                "Count": [completed, on_track, overdue],
            }
            fig = create_pie_chart(
                task_distribution, "Status", "Count", title="Task Distribution"
            )
            display_pie_chart(fig)

    # Tab 2: Communication Efficiency
    with tabs[1]:
        st.header("Communication Efficiency")
        comm_data = data["communication_data"]

        # Communication metrics in a single row
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_styled_metric(
                "Avg Email Response Time",
                f"{comm_data['avg_email_response_time']} hours",
                "📧",
            )
        with col2:
            create_styled_metric(
                "Meetings Attended", comm_data["meetings_attended"], "🗓️"
            )
        with col3:
            create_styled_metric(
                "Feedback Implemented", comm_data["feedback_implemented"], "💡"
            )
        with col4:
            create_styled_metric(
                "Time in Meetings", f"{comm_data['time_in_meetings']}%", "⏱️"
            )

        st.subheader("Email Response Time Trend")
        email_trend = data.get("email_trend", generate_email_response_trend())
        create_styled_line_chart(email_trend, "Week", "Response Time (hours)")

    # Tab 3: Knowledge
    with tabs[2]:
        st.header("Knowledge")
        knowledge_data = data["knowledge_data"]

        # Knowledge metrics in a single row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric(
                "Articles Written", knowledge_data["articles_written"], "📝"
            )
        with col2:
            create_styled_metric(
                "Articles Contributed", knowledge_data["articles_contributed"], "💬"
            )
        with col3:
            create_styled_metric(
                "Training Sessions", knowledge_data["training_sessions"], "🎓"
            )
        with col4:
            create_styled_metric(
                "Mentoring Hours", knowledge_data["mentoring_hours"], "🤝"
            )
        with col5:
            create_styled_metric(
                "Doc Contributions",
                f"{knowledge_data['documentation_contributions']} pages",
                "📚",
            )

        # Recent Contributions (only for individual employees)
        if selected_employee != "All Employees":
            st.subheader("Recent Contributions")
            contributions = generate_recent_contributions()
            contrib_list = [
                f"{contrib} - {date.strftime('%Y-%m-%d')}"
                for contrib, date in contributions
            ]
            create_styled_bullet_list(contrib_list, "Recent Knowledge Contributions")

    # Tab 4: Meetings
    with tabs[3]:
        st.header("Meetings")
        meeting_data = data["meeting_data"]

        # Meeting metrics in a single row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric("Meetings Organized", meeting_data["organized"], "📅")
        with col2:
            create_styled_metric("Meetings Attended", meeting_data["attended"], "👥")
        with col3:
            create_styled_metric(
                "Avg Duration", f"{meeting_data['avg_duration']} hours", "⏳"
            )
        with col4:
            create_styled_metric(
                "Effectiveness", f"{meeting_data['effectiveness']}/10", "📊"
            )
        with col5:
            create_styled_metric(
                "Weekly Time", f"{meeting_data['weekly_time_percentage']}%", "🕰️"
            )

        st.subheader("Role in Meetings (RACI)")
        raci_data = data.get("raci_data", generate_raci_data())
        create_styled_bar_chart(
            list(raci_data.keys()), list(raci_data.values()), "Role", "Count"
        )

    # Tab 5: Learning
    with tabs[4]:
        st.header("Learning")
        learning_data = data["learning_data"]

        # Learning metrics in a single row
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric(
                "Learning Hours", learning_data["learning_hours"], "📚"
            )
        with col2:
            create_styled_metric(
                "Conferences", learning_data["conferences_attended"], "🎤"
            )
        with col3:
            create_styled_metric(
                "Skill Improvement", f"{learning_data['skill_improvement']}/10", "📈"
            )
        with col4:
            create_styled_metric(
                "Courses Completed", len(learning_data["courses_completed"]), "🎓"
            )
        with col5:
            create_styled_metric(
                "Certifications", len(learning_data["certifications"]), "🏅"
            )

        # Courses and Certifications
        col1, col2 = st.columns(2)
        with col1:
            create_styled_bullet_list(
                learning_data["courses_completed"], "Courses Completed"
            )
        with col2:
            create_styled_bullet_list(
                learning_data["certifications"], "Certifications Achieved"
            )

    # Tab 6: Code
    with tabs[5]:
        st.header("Code")
        code_data = data["code_data"]

        # All code metrics in two rows
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric(
                "Code Quality", f"{code_data['quality_score']}/10", "🏆"
            )
        with col2:
            create_styled_metric("Code Reviews", code_data["peer_reviews"], "👁️")
        with col3:
            create_styled_metric(
                "Refactoring Tasks", code_data["refactoring_tasks"], "🔧"
            )
        with col4:
            create_styled_metric(
                "Features Developed", code_data["features_developed"], "🚀"
            )
        with col5:
            create_styled_metric("Git Commits", code_data["git_commits"], "💻")

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric(
                "Bug Fix Rate", f"{code_data['bug_fix_rate']} bugs/week", "🐛"
            )
        with col2:
            create_styled_metric(
                "Critical Bugs Fixed", code_data["bugs_fixed"]["critical"], "🚨"
            )
        with col3:
            create_styled_metric(
                "High Bugs Fixed", code_data["bugs_fixed"]["high"], "🔴"
            )
        with col4:
            create_styled_metric(
                "Medium Bugs Fixed", code_data["bugs_fixed"]["medium"], "🟠"
            )
        with col5:
            create_styled_metric("Low Bugs Fixed", code_data["bugs_fixed"]["low"], "🟡")

        # Bugs Fixed by Criticality pie chart
        st.subheader("Bugs Fixed by Criticality")
        bug_data = {
            "Criticality": list(code_data["bugs_fixed"].keys()),
            "Count": list(code_data["bugs_fixed"].values()),
        }
        fig = create_pie_chart(
            bug_data, "Criticality", "Count", title="Bugs Fixed by Criticality"
        )
        display_pie_chart(fig)


def manager_productivity_dashboard():
    st.header("Team Productivity Overview")

    # Dummy data
    df = generate_team_dummy_data(num_teams=5, duration=365)

    # Filters
    col1, col2 = st.columns(2)
    with col1:
        duration = st.selectbox(
            "Select Duration",
            ["Month", "Quarter", "Half Year", "Year"],
            key="manager_duration",
        )
    with col2:
        team = st.selectbox(
            "Select Team",
            ["All Teams"] + df["Team"].unique().tolist(),
            key="manager_team",
        )

    # Filter data based on selection
    end_date = df["Date"].max()
    if duration == "Month":
        start_date = end_date - timedelta(days=30)
    elif duration == "Quarter":
        start_date = end_date - timedelta(days=90)
    elif duration == "Half Year":
        start_date = end_date - timedelta(days=180)
    else:
        start_date = end_date - timedelta(days=365)

    filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]
    if team != "All Teams":
        filtered_df = filtered_df[filtered_df["Team"] == team]

    # Aggregate data
    agg_df = (
        filtered_df.groupby("Team")
        .agg(
            {
                "Task Completion Rate": "mean",
                "Communication Efficiency Rate": "mean",
                "Knowledge Contributions": "sum",
                "Meeting Effectiveness": "mean",
                "Average Meeting Duration": "mean",
                "Percentage Time in Meetings": "mean",
                "Action Items per Meeting": "mean",
                "Resolutions per Meeting": "mean",
            }
        )
        .reset_index()
    )

    # Create visualizations
    st.subheader("Team Performance Metrics")

    create_styled_bar_chart(
        agg_df["Team"], agg_df["Task Completion Rate"], "Team", "Completion Rate"
    )

    create_styled_bar_chart(
        agg_df["Team"],
        agg_df["Communication Efficiency Rate"],
        "Team",
        "Efficiency Rate",
    )

    create_styled_bar_chart(
        agg_df["Team"],
        agg_df["Knowledge Contributions"],
        "Team",
        "Number of Contributions",
    )

    # Split tables
    st.subheader("Meeting Productivity Analysis Table")
    meeting_df = agg_df[
        [
            "Team",
            "Meeting Effectiveness",
            "Average Meeting Duration",
            "Percentage Time in Meetings",
            "Action Items per Meeting",
            "Resolutions per Meeting",
        ]
    ]
    st.dataframe(
        meeting_df.set_index("Team").style.format(
            {
                "Meeting Effectiveness": "{:.2%}",
                "Average Meeting Duration": "{:.0f} min",
                "Percentage Time in Meetings": "{:.2%}",
                "Action Items per Meeting": "{:.1f}",
                "Resolutions per Meeting": "{:.1f}",
            }
        ),
        height=220,
    )

    st.subheader("Other Productivity Metrics Table")
    other_df = agg_df[
        [
            "Team",
            "Task Completion Rate",
            "Communication Efficiency Rate",
            "Knowledge Contributions",
        ]
    ]
    st.dataframe(
        other_df.set_index("Team").style.format(
            {
                "Task Completion Rate": "{:.2%}",
                "Communication Efficiency Rate": "{:.2%}",
                "Knowledge Contributions": "{:.0f}",
            }
        ),
        height=220,
    )

    # Attention Required section
    st.subheader("Attention Required")
    attention_required = False
    for _, row in agg_df.iterrows():
        if row["Task Completion Rate"] < 0.7:
            create_styled_metric(
                f"{row['Team']} Task Completion",
                f"{row['Task Completion Rate']:.2%}",
                "⚠️",
            )
            st.warning(
                f"{row['Team']}'s task completion rate is below 70%. Consider scheduling a review to address any blockers."
            )
            attention_required = True
        if row["Communication Efficiency Rate"] < 0.75:
            create_styled_metric(
                f"{row['Team']} Communication Efficiency",
                f"{row['Communication Efficiency Rate']:.2%}",
                "⚠️",
            )
            st.warning(
                f"{row['Team']}'s communication efficiency rate is below 75% ({row['Communication Efficiency Rate']:.2%}). Consider implementing team communication improvement strategies."
            )
            attention_required = True
        if row["Knowledge Contributions"] < 10:
            create_styled_metric(
                f"{row['Team']} Knowledge Contributions",
                f"{row['Knowledge Contributions']:.0f}",
                "ℹ️",
            )
            st.info(
                f"{row['Team']} has made fewer than 10 knowledge contributions ({row['Knowledge Contributions']}). Encourage more knowledge sharing within the team."
            )
            attention_required = True

    if not attention_required:
        create_styled_metric("Team Performance", "All Good", "🎉")
        st.success("All teams are performing well. No immediate attention required.")


if __name__ == "__main__":
    productivity_dashboard()
