import streamlit as st

from demo_code.second_line_manager_or_director.org_performance_dashboard import \
    director_performance_dashboard
from demo_code.second_line_manager_or_director.org_productivity_dashboard import \
    org_productivity_dashboard
from demo_code.second_line_manager_or_director.org_project_and_portfolio_dashboard import \
    director_project_portfolio_dashboard


def show_director_dashboard(nav_option):
    if nav_option == "Productivity":
        org_productivity_dashboard()
    elif nav_option == "Performance":
        director_performance_dashboard()
    elif nav_option == "Projects and Portfolio":
        director_project_portfolio_dashboard()
    else:
        st.write(f"Dashboard for {nav_option} is not implemented yet.")
