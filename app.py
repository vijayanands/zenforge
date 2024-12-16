import streamlit as st

from ui.dashboard import dashboard
from ui.style import set_page_style, set_page_container_style
from ui.title_bar import set_title_bar

def setup_streamlit_ui():
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

    # Set dummy user data in session state with all required attributes
    if "user" not in st.session_state:
        st.session_state.user = type('DummyUser', (), {
            'id': 1,  # Added id attribute
            'first_name': 'Demo',
            'email': 'demo@example.com',
            'is_manager': False,
            'is_enterprise_admin': False,
            'get_skills': lambda: {},  # Add empty skills method
            'profile_image': None,  # Add profile image attribute
            'position': None  # Add position attribute
        })()
    
    # Initialize user skills in session state
    if "user_skills" not in st.session_state:
        st.session_state.user_skills = {}

    # Show dashboard directly
    dashboard()

if __name__ == "__main__":
    setup_streamlit_ui()
