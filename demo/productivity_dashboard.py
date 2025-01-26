import streamlit as st
from datetime import datetime, timedelta

from demo.ic_productivity_dashboard import ic_productivity_dashboard
from tools.github.github import pull_github_data

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
        # Display appropriate dashboard based on persona and navigation option
        ic_productivity_dashboard()
    else:
        st.info("Please select a time range and apply it to view the dashboard.") 