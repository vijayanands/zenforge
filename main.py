import os
import sys
from pathlib import Path

from demo.metrics.engineering_metrics_dashboard import engineering_metrics_dashboard

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.absolute()

# Add project root and subdirectories to Python path
sys.path.extend([
    str(PROJECT_ROOT),
    str(PROJECT_ROOT / "tools"),
    str(PROJECT_ROOT / "demo"),
    str(PROJECT_ROOT / "model")
])

import streamlit as st
from dotenv import load_dotenv

from demo.first_line_manager.dashboard import show_first_line_manager_dashboard
from demo.ic.dashboard import show_ic_dashboard
from demo.second_line_manager_or_director.dashboard import show_director_dashboard
from demo.ui.title_bar import set_title_bar
from model.load_events_db import load_sample_data_into_timeseries_db
from demo.metrics.sdlc_timeline import main as show_sdlc_timeline

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
    ],
    "First Line Manager": [
        "Productivity",
        "Performance & Career",
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


def zenforge_dashboard():
    # Initialize synthetic data first
    initialize_synthetic_data()

    st.set_page_config(page_title=PAGE_TITLE, layout="wide")

    # Add the title bar
    logo_path = "demo/ui/pathforge-logo-final.png"
    set_title_bar(logo_path)

    # Create a sidebar
    with st.sidebar:
        # Main navigation options
        main_option = st.radio("Select Navigation", ["Productivity and Performance", "SDLC Timeline", "Engineering Metrics"])

        if main_option == "Productivity and Performance":
            # Section for persona selection
            persona = st.selectbox(
                PERSONA_SELECTION_LABEL,
                PERSONA_OPTIONS,
                index=DEFAULT_PERSONA_INDEX,
            )

            # Section for persona-based navigation
            nav_options = PERSONA_NAVIGATION.get(persona, [])
            nav_option = st.radio("Persona Navigation", nav_options)

        elif main_option == "SDLC Timeline":
            st.write("Displaying SDLC Timeline")
        elif main_option == "Engineering Metrics":
            st.write("Displaying Engineering Metrics")

    # Main content area
    if main_option == "Productivity and Performance":
        # Display appropriate dashboard based on persona and navigation option
        if nav_option:
            if persona == PERSONA_OPTIONS[0]:  # Individual Contributor
                show_ic_dashboard(nav_option)
            elif persona == PERSONA_OPTIONS[1]:  # First Line Manager
                show_first_line_manager_dashboard(nav_option)
            elif persona == PERSONA_OPTIONS[2]:  # Second Line Manager
                show_director_dashboard(nav_option)
        else:
            st.write(UNIMPLEMENTED_MESSAGE.format(persona))
    elif main_option == "SDLC Timeline":
        show_sdlc_timeline()
    elif main_option == "Engineering Metrics":
        engineering_metrics_dashboard()
    else:
        st.write("Invalid Option")

if __name__ == "__main__":
    zenforge_dashboard()
