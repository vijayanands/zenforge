def ic_performance_dashboard():
    st.title("Performance Dashboard")

    # Use the common time range from session state
    if 'selected_time_range' in st.session_state:
        start_date = st.session_state.selected_time_range['start_date']
        end_date = st.session_state.selected_time_range['end_date']

        # Rest of the performance dashboard code... 