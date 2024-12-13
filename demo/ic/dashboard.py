import streamlit as st

from demo.ic.ic_performance_and_career_dashboard import (
    ic_perf_and_career_dashboard,
)
from demo.ic.ic_productivity_dashboard import ic_productivity_dashboard

def show_ic_dashboard(nav_option):
    if nav_option == "Productivity":
        ic_productivity_dashboard()
    elif nav_option == "Performance":
        ic_perf_and_career_dashboard()
    else:
        st.write("Please select a navigation option from the sidebar.")
