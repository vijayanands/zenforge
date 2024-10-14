import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from ui.style import (
    create_pie_chart,
    create_styled_bar_chart,
    create_styled_bullet_list,
    create_styled_line_chart,
    create_styled_metric,
    create_styled_radio_buttons,
    create_styled_tabs,
    display_pie_chart,
)


def set_custom_css():
    st.markdown(
        """
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff;
        border-bottom: 2px solid #4e8cff;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
    }
    .small-chart {
        width: 100%;
        max-width: 300px;
        margin-bottom: 20px;  /* Add margin at the bottom */
    }
    /* Add padding to the bottom of the tab content */
    .stTabs [data-baseweb="tab-panel"] {
        padding-bottom: 30px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


# Helper functions to generate dummy data (unchanged)
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


def ic_productivity_dashboard():
    set_custom_css()

    st.title("Employee Productivity Dashboard")

    # Generate a random employee for demonstration
    employees = generate_employee_list()
    selected_employee = random.choice(employees)

    # Display employee info and productivity score
    employee_position = generate_employee_position(selected_employee)
    productivity_score = generate_productivity_score()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Employee:** {selected_employee}")
    with col2:
        st.info(f"**Position:** {employee_position}")
    with col3:
        st.info(f"**Productivity Score:** {productivity_score}/10")

    # Duration selection with styled radio buttons in a container
    duration = create_styled_radio_buttons(
        "Select Duration", ["Quarterly", "Yearly"], "duration_selection"
    )

    # Tabs
    tab_labels = ["Tasks", "Communication", "Knowledge", "Meetings", "Learning", "Code"]
    tabs = create_styled_tabs(tab_labels)

    # Tab 1: Tasks
    with tabs[0]:
        total_tasks, completed, in_progress, on_track, overdue = generate_task_data()

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

        col1, col2 = st.columns(2)
        with col1:
            st.header("Task Distribution")
            task_data = pd.DataFrame(
                {
                    "Status": ["Completed", "On Track", "Overdue"],
                    "Value": [completed, on_track, overdue],
                }
            )
            fig = create_pie_chart(
                task_data,
                names="Status",
                values="Value",
                title="Task Distribution",
                height=360,
                width=360,
            )
            display_pie_chart(fig)

        with col2:
            st.header("Weekly Task Completion Rate")
            weekly_completion = generate_weekly_task_completion()
            create_styled_line_chart(weekly_completion, "Weeks", "Tasks Completed")

    # Tab 2: Communication Efficiency
    with tabs[1]:
        comm_data = generate_communication_data()

        col1, col2, col3 = st.columns(3)
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
                "Time in Meetings", f"{comm_data['time_in_meetings']}%", "⏱️"
            )

        st.header("Email Response Time Trend")
        email_trend = generate_email_response_trend()
        create_styled_line_chart(email_trend, "Weeks", "Response Time (hours)")

    # Tab 3: Knowledge
    with tabs[2]:
        knowledge_data = generate_knowledge_data()

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
                "Training Sessions", knowledge_data["training_sessions"], "👨‍🏫"
            )
        with col4:
            create_styled_metric(
                "Mentoring Hours", knowledge_data["mentoring_hours"], "🤝"
            )
        with col5:
            create_styled_metric(
                "Documentation Edits",
                knowledge_data["documentation_contributions"],
                "📚",
            )

        create_styled_bullet_list(
            [
                f"{contrib} - {date.strftime('%Y-%m-%d')}"
                for contrib, date in generate_recent_contributions()
            ],
            title="Recent Contributions",
        )

    # Tab 4: Meetings
    with tabs[3]:
        meeting_data = generate_meeting_data()

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            create_styled_metric("Organized", meeting_data["organized"], "📅")
        with col2:
            create_styled_metric("Attended", meeting_data["attended"], "👥")
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

        st.header("Role in Meetings (RACI)")
        raci_data = generate_raci_data()
        create_styled_bar_chart(
            list(raci_data.keys()), list(raci_data.values()), "Roles", "Count"
        )

    # Tab 5: Learning
    with tabs[4]:
        learning_data = generate_learning_data()

        col1, col2, col3 = st.columns(3)
        with col1:
            create_styled_metric(
                "Learning Hours", learning_data["learning_hours"], "📚"
            )
        with col2:
            create_styled_metric(
                "Conferences Attended", learning_data["conferences_attended"], "🎤"
            )
        with col3:
            create_styled_metric(
                "Skill Improvement", f"{learning_data['skill_improvement']}/10", "📈"
            )

        create_styled_bullet_list(
            learning_data["courses_completed"], title="Courses Completed"
        )
        create_styled_bullet_list(
            learning_data["certifications"], title="Certifications Achieved"
        )

    # Tab 6: Code
    with tabs[5]:
        code_data = generate_code_data()

        col1, col2, col3, col4, col5, col6 = st.columns(6)
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
            create_styled_metric("Git Commits", code_data["git_commits"], "🔢")
        with col6:
            create_styled_metric(
                "Bug Fix Rate", f"{code_data['bug_fix_rate']}/week", "🐛"
            )

        col1, col2 = st.columns(2)
        with col1:
            st.header("Bugs Fixed by Criticality")
            bugs_data = pd.DataFrame(
                {
                    "Criticality": code_data["bugs_fixed"].keys(),
                    "Count": code_data["bugs_fixed"].values(),
                }
            )
            fig = create_pie_chart(
                bugs_data,
                names="Criticality",
                values="Count",
                title="Bugs Fixed by Criticality",
                height=360,
                width=360,
            )
            display_pie_chart(fig)

        with col2:
            st.header("Code Quality Trend")
            code_quality_trend = [
                random.uniform(
                    code_data["quality_score"] - 1, code_data["quality_score"] + 1
                )
                for _ in range(12)
            ]
            create_styled_line_chart(code_quality_trend, "Weeks", "Code Quality Score")


if __name__ == "__main__":
    ic_productivity_dashboard()
