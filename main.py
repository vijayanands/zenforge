import streamlit as st

from demo_code.first_line_manager.dashboard import \
    show_first_line_manager_dashboard
from demo_code.ic.dashboard import show_ic_dashboard
from demo_code.second_line_manager_or_director.dashboard import \
    show_director_dashboard
from demo_code.ui.title_bar import set_title_bar

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
        "Learning & Skills",
        "Tasks",
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


def main():
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


if __name__ == "__main__":
    main()
