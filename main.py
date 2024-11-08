import sys

import streamlit as st

from demo_code.first_line_manager.dashboard import show_first_line_manager_dashboard
from demo_code.ic.dashboard import show_ic_dashboard
from demo_code.second_line_manager_or_director.dashboard import show_director_dashboard
from demo_code.ui.title_bar import set_title_bar
from model.load_events_db import load_sample_data_into_timeseries_db

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
        "Performance",
        "Projects and Portfolio",
    ],
}


def zenforge_dashboard():
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

    if persona == PERSONA_OPTIONS[0]:  # Individual Contributor
        show_ic_dashboard(nav_option)
    elif persona == PERSONA_OPTIONS[1]:  # First Line Manager
        show_first_line_manager_dashboard(nav_option)
    elif persona == PERSONA_OPTIONS[2]:  # Second Line Manager
        show_director_dashboard(nav_option)
    else:
        st.write(UNIMPLEMENTED_MESSAGE.format(persona))


def create_end_to_end_timechart_for_project(project: str):
    print(f"Displaying end to end view of project {project}")
    print(
        "\n"
        "    This will be the pseudo code for this\n"
        "    \n"
        "    jira_list <= get list of jiras for project\n"
        "    Let us first find the events in the design phase\n"
        "    design_jiras <= filter for type=Design in jira_list\n"
        "    create a list of dictionaries that contain the following\n"
        "        jira_id\n"
        "        title\n"
        "        status\n"
        "        start_time\n"
        "        end_time\n"
        "        assigned_to\n"
        "        estimated_hours\n"
        "        actual_hours\n"
        "    \n"
        "    Now let us get the sprints related stats\n"
        "    sprint_list <= get the list of sprints for project\n"
        "    for each sprint in the project create a list of dictionary that contains the following\n"
        "        start_date\n"
        "        end_date\n"
        "        planned_story points\n"
        "        completed_story_points\n"
        "        burndown_efficiency\n"
        "        team_velocity\n"
        "        team satisfaction score\n"
        "        \n"
        "    \n"
        "    "
    )

if __name__ == "__main__":
    # Check if running with streamlit
    if len(sys.argv) > 1 and sys.argv[1] == "streamlit":
        zenforge_dashboard()
    else:
        # Command line interface
        function_input = input(
            "Please enter the function to run ('load_data' or 'view_project' or 'dashboard'): "
        )
        if function_input == "load_data":
            load_sample_data_into_timeseries_db()
            sys.exit(1)
        elif function_input == "view_project":
            project: str = "PRJ-001"
            create_end_to_end_timechart_for_project(project)
            sys.exit(1)
        elif function_input == "dashboard":
            zenforge_dashboard()
        else:
            print("Invalid option. Please choose 'load_data' or 'view_project' or 'dashboard'.")

