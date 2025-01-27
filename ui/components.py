from datetime import datetime, timedelta
import streamlit as st
from functions.github.github import pull_github_data

def time_range_selector(key_prefix=""):
    """Shared time range selector component with GitHub data fetching"""
    st.header("Time Range")
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime.today() - timedelta(days=30),
            max_value=datetime.today(),
            key=f"{key_prefix}_start_date"
        )
    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.today(),
            min_value=start_date,
            max_value=datetime.today(),
            key=f"{key_prefix}_end_date"
        )

    if st.button("Display Dashboard", key=f"{key_prefix}_display_btn"):
        with st.spinner('Loading data... Please wait.'):
            github_data, user_info = pull_github_data(
                start_date=start_date.strftime("%Y-%m-%d"),
                end_date=end_date.strftime("%Y-%m-%d")
            )
            
            # Update session state
            st.session_state[f"{key_prefix}_github_data"] = github_data
            st.session_state[f"{key_prefix}_user_info"] = user_info
            st.session_state[f"{key_prefix}_show_dashboard"] = True
            
            st.success('Data successfully loaded!')
            st.rerun()

    return (
        st.session_state.get(f"{key_prefix}_github_data"),
        st.session_state.get(f"{key_prefix}_user_info"),
        st.session_state.get(f"{key_prefix}_show_dashboard", False)
    ) 