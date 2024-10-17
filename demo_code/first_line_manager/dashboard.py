import streamlit as st

from demo_code.first_line_manager.mgr_performance_metrics_dashboard import (
    manager_performance_dashboard,
)
from demo_code.first_line_manager.mgr_productivity_dashboard import (
    productivity_dashboard,
)


def show_first_line_manager_dashboard(nav_option):
    if nav_option == "Productivity":
        productivity_dashboard()
    elif nav_option == "Performance & Career":
        manager_performance_dashboard()
    else:
        st.write(f"Dashboard for {nav_option} is not implemented yet.")
