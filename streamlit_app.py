import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

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

from ui.dashboard import dashboard
from ui.style import set_page_style, set_page_container_style
from ui.title_bar import set_title_bar

def setup_streamlit_ui():
    """Setup and run the Streamlit UI"""
    st.set_page_config(
        page_title="PathForge",
        layout="wide",
        menu_items=None,  # This removes the hamburger menu
    )

    # Hide the "Made with Streamlit" footer and other potential UI elements
    hide_streamlit_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        header {visibility: hidden;}
        #stDecoration {display:none;}
        </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    set_page_style()
    set_page_container_style()
    set_title_bar()

    # Initialize user skills in session state
    if "user_skills" not in st.session_state:
        st.session_state.user_skills = {}

    # Show dashboard directly
    dashboard()

if __name__ == "__main__":
    setup_streamlit_ui()
