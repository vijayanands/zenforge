import random
from datetime import datetime, timedelta

import pandas as pd
import streamlit as st

from ui.style import create_styled_metric, create_styled_bullet_list, create_pie_chart, \
    display_pie_chart, create_styled_tabs, create_styled_line_chart, create_styled_bar_chart

from functions.github.github import pull_github_data
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

    # Get GitHub data from session state
    github_data = st.session_state.get('github_data')
    user_info = st.session_state.get('user_info')

    if github_data and user_info:
        # Get list of employees
        employees = generate_employee_list(user_info)
        
        # Create a list of names for the selectbox, with default option
        employee_names = ["Select an employee"] + [name for name, _ in employees] if employees else ["No data available"]
        name_to_email = dict(employees) if employees else {}
        
        # Use session state to maintain selection across reruns
        if 'selected_employee' not in st.session_state:
            st.session_state.selected_employee = "Select an employee"
        
        # Move selectbox to a container to prevent duplication of elements above it
        with st.container():
            selected_name = st.selectbox("Select Employee", employee_names, 
                                       index=employee_names.index(st.session_state.selected_employee))
            st.session_state.selected_employee = selected_name
            selected_email = name_to_email.get(selected_name)

        # Only show dashboard content if a valid employee is selected
        if selected_name != "Select an employee" and selected_name != "No data available":
            # Display employee info
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Employee:** {selected_name}")
            with col2:
                designation = get_employee_designation(selected_email, user_info) if selected_email else "Unknown"
                st.info(f"**Position:** {designation}")

            # Create tabs
            tabs = create_styled_tabs(["Code", "Knowledge", "Meetings", "Goals & Objectives"])

            # Tab 1: Code
            with tabs[0]:
                # Use the selected_email to find the employee's data
                if selected_email and selected_email in github_data:
                    employee_data = github_data[selected_email]
                    code_data = {
                        "quality_score": round(random.uniform(1, 10), 1),  # Keep random for now
                        "pr_comments": employee_data.get("total_pull_request_comments", 0),  # Changed from peer_reviews
                        "git_commits": employee_data.get("total_commits", 0),
                        "total_prs": employee_data.get("total_pull_requests", 0),
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
                        "pr_comments": random.randint(10, 50),  # Changed from peer_reviews
                        "git_commits": random.randint(20, 100),
                        "total_prs": random.randint(5, 15),
                        "bug_fix_rate": round(random.uniform(0.5, 5), 1),
                        "bugs_fixed": {
                            "low": random.randint(5, 15),
                            "medium": random.randint(3, 10),
                            "high": random.randint(1, 5),
                            "critical": random.randint(0, 3),
                        }
                    }

                # Display metrics
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    create_styled_metric("Code Commits", code_data["git_commits"], "🔢")
                with col2:
                    create_styled_metric("Total PRs", code_data["total_prs"], "🔄")
                with col3:
                    create_styled_metric("PR Comments", code_data["pr_comments"], "💬")
                with col4:
                    create_styled_metric(
                        "Code Quality", f"{code_data['quality_score']}/10", "🏆"
                    )
                with col5:
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

            # Tab 2: Knowledge
            with tabs[1]:
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

            # Tab 3: Meetings
            with tabs[2]:
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
            # Tab 4: Goals & Objectives
            with tabs[3]:
                goals = generate_goals_for_employee(selected_email)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("Technical Goals")
                    for goal in goals["technical_goals"]:
                        display_goal_with_status(goal)

                with col2:
                    st.subheader("Professional Goals")
                    for goal in goals["professional_goals"]:
                        display_goal_with_status(goal)


if __name__ == "__main__":
    ic_productivity_dashboard()


def generate_goals_for_employee(email: str) -> dict:
    """Generate or fetch goals for the specified employee with random statuses"""
    # Use email as seed for random to get consistent results for same employee
    random.seed(hash(email))

    status_options = ["Completed", "On Track", "In Progress", "At Risk", "Not Started"]

    technical_goals = [
        {
            "goal": "Complete Advanced Python Certification",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Lead 2 major feature implementations",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Improve code coverage to 85%",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Mentor 2 junior developers",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        }
    ]

    professional_goals = [
        {
            "goal": "Improve presentation skills",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Take leadership training",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Contribute to 3 cross-team projects",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        },
        {
            "goal": "Write 5 technical blog posts",
            "status": random.choice(status_options),
            "completion": random.randint(0, 100)
        }
    ]

    # Ensure completion percentage matches status
    for goal in technical_goals + professional_goals:
        if goal["status"] == "Completed":
            goal["completion"] = 100
        elif goal["status"] == "Not Started":
            goal["completion"] = 0
        elif goal["status"] == "At Risk":
            goal["completion"] = random.randint(10, 40)
        elif goal["status"] == "On Track":
            goal["completion"] = random.randint(60, 90)
        else:  # In Progress
            goal["completion"] = random.randint(20, 80)

    return {
        "technical_goals": technical_goals,
        "professional_goals": professional_goals
    }


def display_goal_with_status(goal_data):
    """Display a goal with its status and completion progress"""
    status_colors = {
        "Completed": "green",
        "On Track": "blue",
        "In Progress": "orange",
        "At Risk": "red",
        "Not Started": "grey"
    }
    color = status_colors.get(goal_data["status"], "grey")

    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="flex-grow: 1;">
                    <span>• {goal_data["goal"]}</span>
                </div>
                <div style="margin-left: 20px;">
                    <span style="color: {color}; font-weight: bold;">{goal_data["status"]}</span>
                </div>
            </div>
            <div style="background-color: #f0f2f6; height: 8px; border-radius: 4px; margin-top: 5px;">
                <div style="background-color: {color}; width: {goal_data['completion']}%; height: 100%; border-radius: 4px;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
