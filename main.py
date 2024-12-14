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
from model.load_events_db import load_sample_data_into_timeseries_db
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
                load_sample_data_into_timeseries_db()
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
            ["Productivity and Performance", "Development Cycle Metrics"]
        )

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
                st.rerun()

        if main_option == "Productivity and Performance":
            # Section for persona selection
            persona = st.selectbox(
                PERSONA_SELECTION_LABEL,
                PERSONA_OPTIONS,
                index=DEFAULT_PERSONA_INDEX,
            )

            # Section for persona-based navigation
            nav_options = PERSONA_NAVIGATION.get(persona, [])
            nav_options.append("Engineering Metrics")  # Add Engineering Metrics to navigation
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
    if main_option == "Productivity and Performance":
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
            
            # Handle action button states
            if st.session_state.get("show_self_appraisal", False):
                with st.container():
                    st.markdown('<div class="modal-overlay"></div>', unsafe_allow_html=True)
                    with st.container():
                        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
                        st.subheader("Self Appraisal")
                        
                        # Initialize session state for appraisal flow
                        if 'appraisal_step' not in st.session_state:
                            st.session_state.appraisal_step = 'select_employee'
                        if 'selected_appraisal_employee' not in st.session_state:
                            st.session_state.selected_appraisal_employee = None

                        if st.session_state.appraisal_step == 'select_employee':
                            # Employee selection step
                            employees = generate_employee_list(st.session_state.get('user_info', {}))
                            employee_names = [name for name, _ in employees] if employees else ["No data available"]
                            selected_name = st.selectbox("Select Employee", employee_names)
                            
                            if st.button("Create Appraisal"):
                                st.session_state.selected_appraisal_employee = selected_name
                                st.session_state.appraisal_step = 'show_dashboard'
                                st.rerun()

                        elif st.session_state.appraisal_step == 'show_dashboard':
                            # Dashboard view
                            st.title(f"Employee Appraisal for {st.session_state.selected_appraisal_employee}")
                            st.info("Appraisal functionality not yet completed")
                            
                            if st.button("Back to Selection"):
                                st.session_state.appraisal_step = 'select_employee'
                                st.rerun()

                        # Close button
                        if st.button("Close", key="close_appraisal"):
                            st.session_state.show_self_appraisal = False
                            st.session_state.appraisal_step = 'select_employee'
                            st.session_state.selected_appraisal_employee = None
                            st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

            if st.session_state.get("show_weekly_report", False):
                with st.container():
                    st.markdown('<div class="modal-overlay"></div>', unsafe_allow_html=True)
                    with st.container():
                        st.markdown('<div class="modal-container">', unsafe_allow_html=True)
                        st.subheader("Weekly Report")
                        
                        # Initialize session state for report flow
                        if 'report_step' not in st.session_state:
                            st.session_state.report_step = 'select_employee'
                        if 'selected_report_employee' not in st.session_state:
                            st.session_state.selected_report_employee = None

                        if st.session_state.report_step == 'select_employee':
                            # Employee selection step
                            employees = generate_employee_list(st.session_state.get('user_info', {}))
                            employee_names = [name for name, _ in employees] if employees else ["No data available"]
                            selected_name = st.selectbox("Select Employee", employee_names)
                            
                            if st.button("Create Report"):
                                st.session_state.selected_report_employee = selected_name
                                st.session_state.report_step = 'show_dashboard'
                                st.rerun()

                        elif st.session_state.report_step == 'show_dashboard':
                            # Dashboard view
                            st.title(f"Weekly Report for {st.session_state.selected_report_employee}")
                            st.info("Weekly report functionality not yet completed")
                            
                            if st.button("Back to Selection"):
                                st.session_state.report_step = 'select_employee'
                                st.rerun()

                        # Close button
                        if st.button("Close", key="close_report"):
                            st.session_state.show_weekly_report = False
                            st.session_state.report_step = 'select_employee'
                            st.session_state.selected_report_employee = None
                            st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write(UNIMPLEMENTED_MESSAGE.format(persona))
    elif main_option == "Development Cycle Metrics":
        display_development_cycle_metrics()
    else:
        st.write("Invalid Option")

if __name__ == "__main__":
    zenforge_dashboard()
