import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
# Set page config first, before any other imports or st commands
st.set_page_config(page_title="Pathforge ZenForge", layout="wide")

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from demo.metrics.engineering_metrics_dashboard import engineering_metrics_dashboard
from demo.first_line_manager.dashboard import show_first_line_manager_dashboard
from demo.ic.dashboard import show_ic_dashboard
from demo.second_line_manager_or_director.dashboard import show_director_dashboard
from demo.ui.title_bar import set_title_bar
from model.load_events_db import load_sample_data
from demo.metrics.development_cycle_metrics import display_development_cycle_metrics
from datetime import datetime, timedelta
from tools.github.github import pull_github_data

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add project root and subdirectories to Python path
sys.path.extend([
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "tools"),
    str(PROJECT_ROOT / "demo"),
    str(PROJECT_ROOT / "model")
])

load_dotenv()

# Constants
PAGE_TITLE = "Pathforge ZenForge"
PERSONA_SELECTION_LABEL = "Select your persona"
PERSONA_OPTIONS = [
    "Individual Contributor",
    "First Line Manager",
    "Second Line Manager/Director",
]
DEFAULT_PERSONA_INDEX = 0
UNIMPLEMENTED_MESSAGE = "Dashboard for {} is not implemented yet."

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


def initialize_synthetic_data():
    """Initialize synthetic data if not already loaded"""
    if "synthetic_data_loaded" not in st.session_state:
        should_load_synthetic = os.getenv("LOAD_SYNTHETIC_DATA", "false").lower() in [
            "true",
            "1",
            "yes",
            "t",
        ]

        if should_load_synthetic:
            try:
                load_sample_data()
                st.session_state.synthetic_data_loaded = True
            except Exception as e:
                st.error(f"Failed to load synthetic data: {str(e)}")
                st.session_state.synthetic_data_loaded = False


def generate_employee_list(user_info):
    """Get list of employees from user_info with their emails"""
    employee_list = [(info["name"], email) for email, info in user_info.items() if info["name"]]
    employee_list.sort(key=lambda x: x[0])
    return employee_list


def zenforge_dashboard():
    # Initialize synthetic data first
    initialize_synthetic_data()

    # Add custom CSS to ensure consistent button styling
    st.markdown("""
        <style>
        /* Remove background color from all action buttons */
        .stButton button {
            background-color: transparent;
            border: 1px solid #ccc;
            color: inherit;
        }
        
        /* Hover effect */
        .stButton button:hover {
            border-color: #4e8cff;
            color: #4e8cff;
        }
        
        /* Active state */
        .stButton button:active {
            background-color: rgba(78, 140, 255, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    # Add the title bar
    logo_path = "demo/ui/pathforge-logo-final.png"
    set_title_bar(logo_path)

    # Create a sidebar
    with st.sidebar:
        # Main navigation options
        main_option = st.radio(
            "Select Navigation",
            ["Productivity", "Development Cycle Metrics"]
        )

        if main_option == "Productivity":
            # Time Range Selection
            st.markdown("---")  # Add separator
            st.header("Time Range")
            col1, col2 = st.columns(2)
            
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.today() - timedelta(days=30),
                    max_value=datetime.today(),
                    key="sidebar_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.today(),
                    min_value=start_date,
                    max_value=datetime.today(),
                    key="sidebar_end_date"
                )

            # Apply button for time range
            if st.button("Apply Time Range", key="apply_time_range"):
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
                
                # Add action buttons section if Productivity is selected
                if nav_option == "Productivity":
                    st.markdown("---")  # Add a separator
                    st.markdown("### Actions")
                    if st.button("Create Self Appraisal"):
                        st.session_state.show_self_appraisal = True
                    if st.button("Create Weekly Report"):
                        st.session_state.show_weekly_report = True

    # Main content area
    if main_option == "Development Cycle Metrics":
        # Show Development Cycle Metrics directly without time range requirement
        display_development_cycle_metrics()
    elif st.session_state.get('show_navigation', False):
        if main_option == "Productivity":
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

if __name__ == "__main__":
    zenforge_dashboard()
