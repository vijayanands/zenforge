import json

import streamlit as st

from functions.weekly_report import create_weekly_report


def perform_weekly_report_generation():
    if "reset_weekly_report" in st.session_state and st.session_state.reset_weekly_report:
        if "weekly_report" in st.session_state:
            del st.session_state.weekly_report
        del st.session_state.reset_weekly_report

    if st.button("Generate Weekly Report", key="generate_weekly_report_button"):
        user_email = "vijayanands@gmail.com"
        with st.spinner(f"Generating weekly report for {user_email} ..."):
            # Parse the JSON string into a dictionary
            weekly_report_str = create_weekly_report(user_email)
            st.session_state.weekly_report = json.loads(weekly_report_str)

    if "weekly_report" in st.session_state:
        pretty_print_weekly_report(st.session_state.weekly_report)
        st.button(
            "Reset",
            on_click=reset_weekly_report,
            key="reset_weekly_report_bottom",
        )


def reset_weekly_report():
    st.session_state.reset_weekly_report = True


def pretty_print_weekly_report(report):
    st.markdown("## Weekly Report")

    # Summary section
    st.markdown("### Summary")
    st.markdown(report["Summary"])  # Changed from "summary" to "Summary" to match the prompt template

    # Key Achievements
    st.markdown("### Key Achievements")
    for achievement in report["Key Achievements"]:  # Changed from "accomplishments" to "Key Achievements"
        st.markdown(f"- {achievement}")

    # Contributions
    st.markdown("### Contributions")
    for project, details in report["Contributions"].items():
        st.markdown(f"**{project}**")
        st.markdown(details)

    # Learning Opportunities
    if "Learning Opportunities" in report:
        st.markdown("### Learning Opportunities")
        for opportunity in report["Learning Opportunities"]:
            st.markdown(f"- {opportunity}")
