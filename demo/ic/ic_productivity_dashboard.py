import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from demo.ui.style import (
    create_pie_chart,
    create_styled_bar_chart,
    create_styled_bullet_list,
    create_styled_line_chart,
    create_styled_metric,
    create_styled_radio_buttons,
    create_styled_tabs,
    display_pie_chart,
)

from tools.github.github import pull_github_data
from model.sdlc_events import User, DatabaseManager, connection_string


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
def generate_employee_list(user_info):
    """Get list of employees from user_info with their emails"""
    # Create a list of tuples (name, email) for employees with names
    employee_list = [(info["name"], email) for email, info in user_info.items() if info["name"]]
    # Sort by name for better display
    employee_list.sort(key=lambda x: x[0])
    return employee_list


def generate_employee_position(employee):
    positions = {
        "John Doe": "Senior Developer",
        "Jane Smith": "Project Manager",
        "Bob Johnson": "UX Designer",
        "Alice Brown": "Data Analyst",
        "Charlie Davis": "Quality Assurance Specialist",
    }
    return positions.get(employee, "Employee")


def generate_task_data():
    total_tasks = random.randint(50, 100)
    completed = random.randint(20, total_tasks - 10)
    in_progress = total_tasks - completed
    on_track = random.randint(0, in_progress)
    overdue = in_progress - on_track
    return total_tasks, completed, in_progress, on_track, overdue


def generate_weekly_task_completion():
    return [random.randint(5, 20) for _ in range(12)]


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


def generate_code_data(selected_employee=None):
    if not selected_employee:
        return {
            "quality_score": round(random.uniform(1, 10), 1),
            "peer_reviews": random.randint(5, 20),
            "bugs_fixed": {
                "low": random.randint(5, 15),
                "medium": random.randint(3, 10),
                "high": random.randint(1, 5),
                "critical": random.randint(0, 3),
            },
            "git_commits": random.randint(20, 100),
            "bug_fix_rate": round(random.uniform(0.5, 5), 1),
        }
    
    # Get GitHub data for the last 30 days
    end_date = datetime.today()
    start_date = end_date - timedelta(days=30)
    github_data, user_info = pull_github_data(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    # Find the employee's email/login from user_info
    employee_id = None
    for email, info in user_info.items():
        if info["name"] == selected_employee:
            employee_id = email
            break
    
    if not employee_id or employee_id not in github_data:
        return generate_code_data()  # Fallback to random data
    
    employee_data = github_data[employee_id]
    
    return {
        "quality_score": round(random.uniform(1, 10), 1),  # Keep random for now
        "peer_reviews": employee_data.get("total_pull_requests", 0),
        "bugs_fixed": {  # Keep random for now
            "low": random.randint(5, 15),
            "medium": random.randint(3, 10),
            "high": random.randint(1, 5),
            "critical": random.randint(0, 3),
        },
        "git_commits": employee_data.get("total_commits", 0),
        "bug_fix_rate": round(random.uniform(0.5, 5), 1),  # Keep random for now
    }


# Dummy functions for actions
def create_weekly_report():
    pass  # Placeholder for the actual implementation


def create_self_appraisal():
    pass  # Placeholder for the actual implementation


def get_employee_designation(email: str, user_info: dict) -> str:
    """Get employee designation from user info"""
    if not user_info or email not in user_info:
        return "Unknown"
    
    # Get user from database using email
    with DatabaseManager(connection_string).get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if user and user.designation:
            # Convert enum value to display format
            return user.designation.value.replace('_', ' ').title()
    return "Unknown"


def ic_productivity_dashboard():
    set_custom_css()

    st.title("Employee Productivity Dashboard")

    # Time Range Selection Section
    st.header("Time Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.today() - timedelta(days=30),
            max_value=datetime.today(),
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.today(),
            min_value=start_date,
            max_value=datetime.today(),
        )

    # Display Dashboard button
    if st.button("Display Dashboard"):
        # Convert dates to string format for GitHub API
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Initialize session state for GitHub data if not already done
        if 'github_data' not in st.session_state:
            st.session_state.github_data = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
        if 'github_data_start_date' not in st.session_state:
            st.session_state.github_data_start_date = None
        if 'github_data_end_date' not in st.session_state:
            st.session_state.github_data_end_date = None
        if 'selected_employee' not in st.session_state:
            st.session_state.selected_employee = None
        if 'show_dashboard' not in st.session_state:
            st.session_state.show_dashboard = False

        # Check if we need to fetch new data
        need_new_data = (
            st.session_state.github_data is None or
            st.session_state.user_info is None or
            st.session_state.github_data_start_date != start_date_str or
            st.session_state.github_data_end_date != end_date_str
        )
        
        if need_new_data:
            with st.spinner('Fetching GitHub data... This may take a few moments.'):
                github_data, user_info = pull_github_data(
                    start_date=start_date_str,
                    end_date=end_date_str
                )
                
                # Update session state
                st.session_state.github_data = github_data
                st.session_state.user_info = user_info
                st.session_state.github_data_start_date = start_date_str
                st.session_state.github_data_end_date = end_date_str
                st.session_state.selected_employee = None
                st.session_state.show_dashboard = True
                
                # Show success message and rerun
                st.success('GitHub data successfully loaded!')
                st.rerun()
        else:
            # Just show the dashboard with existing data
            st.session_state.show_dashboard = True
            st.rerun()

    # Show dashboard only if data is loaded and show_dashboard is True
    if st.session_state.get('show_dashboard', False):
        st.markdown("---")  # Add a separator
        
        # Use cached data
        github_data = st.session_state.github_data
        user_info = st.session_state.user_info

        # Get list of employees from GitHub data
        employees = generate_employee_list(user_info) if user_info else []
        
        # Create a list of names for the selectbox
        employee_names = [name for name, _ in employees] if employees else ["No data available"]
        
        # Create a dict to map names to emails
        name_to_email = dict(employees) if employees else {}
        
        # Use session state to maintain selection across reruns
        index = 0
        if st.session_state.selected_employee in employee_names:
            index = employee_names.index(st.session_state.selected_employee)
        
        selected_name = st.selectbox("Select Employee", employee_names, index=index)
        st.session_state.selected_employee = selected_name
        selected_email = name_to_email.get(selected_name)

        # Display employee info
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**Employee:** {selected_name}")
        with col2:
            designation = get_employee_designation(selected_email, user_info) if selected_email else "Unknown"
            st.info(f"**Position:** {designation}")

        # Create tabs
        tabs = create_styled_tabs(["Tasks", "Code", "Knowledge", "Meetings"])

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

        # Tab 2: Code
        with tabs[1]:
            # Use the selected_email to find the employee's data
            if selected_email and selected_email in github_data:
                employee_data = github_data[selected_email]
                code_data = {
                    "quality_score": round(random.uniform(1, 10), 1),  # Keep random for now
                    "peer_reviews": employee_data.get("total_pull_requests", 0),
                    "git_commits": employee_data.get("total_commits", 0),
                    "bug_fix_rate": round(random.uniform(0.5, 5), 1),  # Keep random for now
                    "bugs_fixed": {  # Keep random for now
                        "low": random.randint(5, 15),
                        "medium": random.randint(3, 10),
                        "high": random.randint(1, 5),
                        "critical": random.randint(0, 3),
                    }
                }
            else:
                # Fallback to random data if employee not found
                code_data = {
                    "quality_score": round(random.uniform(1, 10), 1),
                    "peer_reviews": random.randint(5, 20),
                    "git_commits": random.randint(20, 100),
                    "bug_fix_rate": round(random.uniform(0.5, 5), 1),
                    "bugs_fixed": {
                        "low": random.randint(5, 15),
                        "medium": random.randint(3, 10),
                        "high": random.randint(1, 5),
                        "critical": random.randint(0, 3),
                    }
                }

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                create_styled_metric(
                    "Code Quality", f"{code_data['quality_score']}/10", "🏆"
                )
            with col2:
                create_styled_metric("Code Reviews", code_data["peer_reviews"], "👁️")
            with col3:
                create_styled_metric("Code Commits", code_data["git_commits"], "🔢")
            with col4:
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
                    "Training Sessions", knowledge_data["training_sessions"], "🎓"
                )
            with col4:
                create_styled_metric(
                    "Mentoring Hours", knowledge_data["mentoring_hours"], "🤝"
                )
            with col5:
                create_styled_metric(
                    "Doc Contributions",
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


if __name__ == "__main__":
    ic_productivity_dashboard()
