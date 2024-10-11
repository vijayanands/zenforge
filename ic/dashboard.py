import streamlit as st

from ic.ic_learning_dashboard import ic_learning_dashboard
from ic.ic_performance_and_careeer_dashboard import ic_perf_and_career_dashboard
from ic.ic_productivity_dashboard import ic_productivity_dashboard
from ic.ic_task_dashboard import ic_tasks_dashboard


def show_ic_dashboard(nav_option):
    if nav_option == "Productivity":
        ic_productivity_dashboard()
    elif nav_option == "Performance & Career":
        ic_perf_and_career_dashboard()
    elif nav_option == "Learning & Skills":
        ic_learning_dashboard()
    elif nav_option == "Tasks":
        ic_tasks_dashboard()
    else:
        st.write("Please select a navigation option from the sidebar.")
