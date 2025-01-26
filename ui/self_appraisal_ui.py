import json

import streamlit as st

from functions.self_appraisal import create_self_appraisal


def reset_self_appraisal_ui():
    if "appraisal" in st.session_state:
        del st.session_state.appraisal
    st.session_state.reset_appraisal = True


def pretty_print_appraisal(appraisal_data):
    # Convert string to dictionary if needed
    if isinstance(appraisal_data, str):
        try:
            appraisal_data = json.loads(appraisal_data)
        except json.JSONDecodeError:
            st.error("Invalid JSON string provided. Please check the input.")
            return

    if not isinstance(appraisal_data, dict):
        st.error("Input must be a dictionary or a valid JSON string.")
        return

    col1, col2 = st.columns([3, 1])

    with col1:
        st.header("Self-Appraisal")

    with col2:
        st.button(
            "Reset",
            on_click=reset_self_appraisal_ui,
            key="reset_performance_header",
        )

    # Summary
    if "Summary" in appraisal_data:
        st.subheader("Summary")
        st.write(appraisal_data["Summary"])

    # Key Achievements
    if "Key Achievements" in appraisal_data:
        st.subheader("Key Achievements")
        for achievement in appraisal_data["Key Achievements"]:
            st.markdown(f"• {achievement}")

    # Contributions
    if "Contributions" in appraisal_data:
        st.subheader("Contributions")
        for platform, contribution in appraisal_data["Contributions"].items():
            st.markdown(f"**{platform}**")
            st.write(contribution)
            st.markdown("---")

    # Learning Opportunities
    if "Learning Opportunities" in appraisal_data:
        st.subheader("Learning Opportunities")
        for opportunity in appraisal_data["Learning Opportunities"]:
            st.markdown(f"• {opportunity}")


def perform_self_appraisal():
    if "reset_appraisal" in st.session_state and st.session_state.reset_appraisal:
        if "appraisal" in st.session_state:
            del st.session_state.appraisal
        del st.session_state.reset_appraisal

    if st.button("Generate Self-Appraisal", key="generate_button"):
        user_email = "vijayanands@gmail.com"
        with st.spinner(f"Generating self-appraisal for {user_email} ..."):
            st.session_state.appraisal = create_self_appraisal(user_email)

    if "appraisal" in st.session_state:
        pretty_print_appraisal(st.session_state.appraisal)
        st.button(
            "Reset",
            on_click=reset_self_appraisal_ui,
            key="reset_performance_bottom",
        )
