import os
import sys
from pathlib import Path
import datetime

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add project root and subdirectories to Python path
sys.path.extend([
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "tools"),
    str(PROJECT_ROOT / "demo_code"),
    str(PROJECT_ROOT / "model")
])

import streamlit as st
from dotenv import load_dotenv

from demo_code.first_line_manager.dashboard import show_first_line_manager_dashboard
from demo_code.ic.dashboard import show_ic_dashboard
from demo_code.second_line_manager_or_director.dashboard import show_director_dashboard
from demo_code.ui.title_bar import set_title_bar
from model.load_events_db import load_sample_data_into_timeseries_db
from sdlc_timeline import main as show_sdlc_timeline
from tools.github.github import pull_github_data  # Adjust the import based on your structure

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
        "Performance & Career",
        "SDLC Timeline",
    ],
    "First Line Manager": [
        "Productivity",
        "Performance & Career",
        "SDLC Timeline",
    ],
    "Second Line Manager/Director": [
        "Productivity",
        "Performance",
        "Projects and Portfolio",
        "SDLC Timeline",
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


def zenforge_dashboard():
    # Initialize synthetic data first
    initialize_synthetic_data()

    st.set_page_config(page_title=PAGE_TITLE, layout="wide")

    # Add the title bar
    logo_path = "demo_code/ui/pathforge-logo-final.png"
    set_title_bar(logo_path)

    # Create a sidebar
    with st.sidebar:
        persona = st.selectbox(
            PERSONA_SELECTION_LABEL,
            PERSONA_OPTIONS,
            index=DEFAULT_PERSONA_INDEX,
        )

        # Add navigation options based on selected persona
        if persona in PERSONA_NAVIGATION:
            nav_option = st.radio("Navigation", PERSONA_NAVIGATION[persona])
        else:
            nav_option = None

    # Add a new tab for individual contributor visualization
    st.sidebar.title("Navigation")
    tab = st.sidebar.selectbox("Select a page", ["Home", "Contributor Data"])

    if tab == "Contributor Data":
        st.title("Individual Contributor Data")

        # Get the start and end dates from the user
        start_date = st.date_input("Start Date", value=datetime.datetime.today())
        end_date = st.date_input("End Date", value=datetime.datetime.today())

        if st.button("Fetch Data"):
            github_data, user_info = pull_github_data(start_date=start_date.strftime("%Y-%m-%d"), end_date=end_date.strftime("%Y-%m-%d"))

            # Visualize the data
            if github_data:
                for author, data in github_data.items():
                    st.subheader(f"Contributor: {user_info[author]['name']}")
                    if "total_commits" in data.keys():
                        st.write(f"Total Commits: {data.get('total_commits', 0)}")
                    if "total_pull_requests" in data.keys():
                        st.write(f"Total Pull Requests: {data.get('total_pull_requests', 0)}")
            else:
                st.write("No data found for the selected dates.")

    # Display appropriate dashboard based on persona and navigation option
    if nav_option == "SDLC Timeline":
        show_sdlc_timeline()
    elif persona == PERSONA_OPTIONS[0]:  # Individual Contributor
        show_ic_dashboard(nav_option)
    elif persona == PERSONA_OPTIONS[1]:  # First Line Manager
        show_first_line_manager_dashboard(nav_option)
    elif persona == PERSONA_OPTIONS[2]:  # Second Line Manager
        show_director_dashboard(nav_option)
    else:
        st.write(UNIMPLEMENTED_MESSAGE.format(persona))


if __name__ == "__main__":
    zenforge_dashboard()
