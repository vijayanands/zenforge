import streamlit as st

from first_line_manager.mgr_productivity_dashboard import \
    productivity_dashboard
from first_line_manager.mgr_performance_metrics_dashboard import \
    manager_performance_dashboard


def show_first_line_manager_dashboard(nav_option):
    if nav_option == "Productivity":
        productivity_dashboard()
    elif nav_option == "Performance & Career":
        manager_performance_dashboard()
    else:
        st.write(f"Dashboard for {nav_option} is not implemented yet.")
