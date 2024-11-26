import streamlit as st

from demo_code.ic.ic_performance_and_careeer_dashboard import (
    ic_perf_and_career_dashboard,
)
from demo_code.ic.ic_productivity_dashboard import ic_productivity_dashboard
from demo_code.metrics.engineering_metrics_dashboard import engineering_metrics_dashboard


def show_ic_dashboard(nav_option):
    if nav_option == "Productivity":
        ic_productivity_dashboard()
    elif nav_option == "Performance & Career":
        ic_perf_and_career_dashboard()
    else:
        st.write("Please select a navigation option from the sidebar.")
