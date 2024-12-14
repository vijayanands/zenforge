import streamlit as st
from datetime import datetime, timedelta
from demo.ui.style import create_styled_tabs
from tools.github.github import pull_github_data
from model.sdlc_events import User, DatabaseManager, connection_string

def generate_employee_list(user_info):
    """Get list of employees from user_info with their emails"""
    # Create a list of tuples (name, email) for employees with names
    employee_list = [(info["name"], email) for email, info in user_info.items() if info["name"]]
    # Sort by name for better display
    employee_list.sort(key=lambda x: x[0])
    return employee_list

def get_employee_designation(email: str, user_info: dict) -> str:
    """Get employee designation from user info"""
    if not user_info or email not in user_info:
        return "Unknown"
    
    # Get user from database using email
    with DatabaseManager(connection_string).get_session() as session:
        user = session.query(User).filter_by(email=email).first()
        if user and user.designation:
            return user.designation.value.replace('_', ' ').title()
    return "Unknown"

def generate_goals_for_employee(email: str) -> dict:
    """Generate or fetch goals for the specified employee"""
    # This is a placeholder - you would typically fetch this from a database
    return {
        "technical_goals": [
            {"goal": "Complete Advanced Python Certification", "status": "In Progress", "completion": 60},
            {"goal": "Lead 2 major feature implementations", "status": "On Track", "completion": 50},
            {"goal": "Improve code coverage to 85%", "status": "At Risk", "completion": 30},
            {"goal": "Mentor 2 junior developers", "status": "Completed", "completion": 100}
        ],
        "professional_goals": [
            {"goal": "Improve presentation skills", "status": "On Track", "completion": 70},
            {"goal": "Take leadership training", "status": "Not Started", "completion": 0},
            {"goal": "Contribute to 3 cross-team projects", "status": "In Progress", "completion": 40},
            {"goal": "Write 5 technical blog posts", "status": "On Track", "completion": 60}
        ]
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

def ic_perf_and_career_dashboard():
    st.title("Performance Dashboard")

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
        if 'perf_selected_employee' not in st.session_state:
            st.session_state.perf_selected_employee = "Select an employee"
            
        # Find the index of the selected employee
        try:
            selected_index = employee_names.index(st.session_state.perf_selected_employee)
        except ValueError:
            selected_index = 0  # Default to first option if not found
        
        selected_name = st.selectbox("Select Employee", employee_names, index=selected_index)
        st.session_state.perf_selected_employee = selected_name
        selected_email = name_to_email.get(selected_name)

        # Display employee info
        if selected_email and selected_name != "Select an employee":
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Employee:** {selected_name}")
            with col2:
                designation = get_employee_designation(selected_email, user_info)
                st.info(f"**Position:** {designation}")

            # Create tabs for different categories
            tabs = create_styled_tabs(["Goals & Objectives", "Performance History"])

            # Goals & Objectives tab
            with tabs[0]:
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

            # Performance History tab
            with tabs[1]:
                st.write("Performance history will be displayed here")
                # Add performance history visualization here
    else:
        st.info("Please select a time range and apply it using the sidebar to view the performance dashboard.")

if __name__ == "__main__":
    ic_perf_and_career_dashboard() 