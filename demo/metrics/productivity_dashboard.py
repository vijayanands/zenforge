import streamlit as st
from datetime import datetime, timedelta
from tools.github.github import pull_github_data
from demo.ic.dashboard import show_ic_dashboard
from demo.first_line_manager.dashboard import show_first_line_manager_dashboard
from demo.second_line_manager_or_director.dashboard import show_director_dashboard
from demo.metrics.engineering_metrics_dashboard import engineering_metrics_dashboard

# Constants moved from main.py
PERSONA_SELECTION_LABEL = "Select your persona"
PERSONA_OPTIONS = [
    "Individual Contributor",
    "First Line Manager",
    "Second Line Manager/Director",
]
DEFAULT_PERSONA_INDEX = 0

# Navigation options for each persona
PERSONA_NAVIGATION = {
    "Individual Contributor": [
        "Productivity",
        "Performance",
    ],
    "First Line Manager": [
        "Productivity",
        "Performance",
    ],
    "Second Line Manager/Director": [
        "Productivity",
        "Projects and Portfolio",
    ],
}

def display_productivity_dashboard():
    # Time range selection
    st.header("Time Range Selection")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.today() - timedelta(days=30),
            max_value=datetime.today()
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.today(),
            min_value=start_date,
            max_value=datetime.today()
        )

    # Apply button for time range
    if st.button("Apply Time Range"):
        # Store time range in session state
        st.session_state.selected_time_range = {
            'start_date': start_date,
            'end_date': end_date
        }
        
        # Fetch GitHub data with selected time range
        with st.spinner('Fetching GitHub data... This may take a few moments.'):
            github_data, user_info = pull_github_data(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Store in session state
            st.session_state.github_data = github_data
            st.session_state.user_info = user_info
            st.session_state.show_navigation = True  # Flag to show navigation
            st.rerun()

    # Only show persona selection and navigation after time range is applied
    if st.session_state.get('show_navigation', False):
        st.markdown("---")  # Add separator
        
        # Section for persona selection
        persona = st.selectbox(
            PERSONA_SELECTION_LABEL,
            PERSONA_OPTIONS,
            index=DEFAULT_PERSONA_INDEX,
        )

        # Section for persona-based navigation
        nav_options = PERSONA_NAVIGATION.get(persona, [])
        nav_options.append("Engineering Metrics")
        nav_option = st.radio("Persona Navigation", nav_options)

        # Display appropriate dashboard based on persona and navigation option
        if nav_option:
            if nav_option == "Engineering Metrics":
                engineering_metrics_dashboard()
            elif persona == PERSONA_OPTIONS[0]:  # Individual Contributor
                show_ic_dashboard(nav_option)
            elif persona == PERSONA_OPTIONS[1]:  # First Line Manager
                show_first_line_manager_dashboard(nav_option)
            elif persona == PERSONA_OPTIONS[2]:  # Second Line Manager
                show_director_dashboard(nav_option)
    else:
        st.info("Please select a time range and apply it to view the dashboard.") 