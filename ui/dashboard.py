import streamlit as st
import uuid

from demo.development_cycle_metrics import display_development_cycle_metrics
from demo.productivity_dashboard import display_productivity_dashboard

from functions.ingestion import ingest_data, answer_question
from ui.weekly_report_ui import perform_weekly_report_generation
from ui.self_appraisal_ui import perform_self_appraisal

PROMPT_OPTIONS = [
    "Select an action",
    "Generate a self appraisal for me",
    "Generate a weekly report for me",
    "Show me statistics on SDLC timeline for my projects",
    "Show me productivity dashboard",
    "compare productivity data for employees in my team",
    "List me the top 5% performers in my organization",
    "List me the bottom 5% performers in my organization",
    "Code Quality Analysis",
]
PROMPT_MAP = {
    PROMPT_OPTIONS[1]: "self_appraisal",
    PROMPT_OPTIONS[2]: "weekly_report",
    PROMPT_OPTIONS[3]: "sdlc_timeline_view",
    PROMPT_OPTIONS[4]: "producivity_dashboard",
    PROMPT_OPTIONS[5]: "compare_productivity_data",
    PROMPT_OPTIONS[6]: "top_performers",
    PROMPT_OPTIONS[7]: "bottom_performers",
    PROMPT_OPTIONS[8]: "code_quality_analysis",
}

def dashboard():
    st.title(
        f"Good morning vijayanands@gmail.com"
    )

    # Get the current selection
    current_action = dashboard_conversational()

    # Store the previous selection
    if "previous_action" not in st.session_state:
        st.session_state.previous_action = "Select an action"

    # Check if the action has changed and update the input key and value if it has
    if current_action != st.session_state.previous_action and current_action != "Select an action":
        st.session_state.input_key = str(uuid.uuid4())
        st.session_state.input_value = ""
        st.session_state.previous_action = current_action
        st.rerun()  # Force a rerun to update the UI immediately

    # Only show the "OR" and custom question input if no action is selected
    if current_action == "Select an action":
        st.markdown("### OR")

        # Initialize the input_key and input_value in session state if they don't exist
        if "input_key" not in st.session_state:
            st.session_state.input_key = str(uuid.uuid4())
        if "input_value" not in st.session_state:
            st.session_state.input_value = ""

        # Use the dynamic key for the text input and set its value
        custom_question = st.text_input("Ask a custom question:", key=st.session_state.input_key, value=st.session_state.input_value)

        if st.button("Ask", key="custom_question_button"):
            st.session_state.processing_question = True
            st.session_state.custom_question = custom_question

        # Add example questions with light styling and smaller, bold, italicized heading
        st.markdown("""
        <div style="color: #808080;">
        <p style="font-size: 1.1em; font-weight: bold; font-style: italic; margin-bottom: 5px;">Example Questions</p>
        <div style="font-style: italic;">
        You can ask questions about your work in JIRA, Confluence, and GitHub. Here are some examples:
        <ul>
        <li>What are the Jira issues that I have resolved? Give me the links for those</li>
        <li>How many pull requests are there for this user?</li>
        <li>What is the content of the 'Getting started in Confluence' page for this user?</li>
        <li>Which users have GitHub data?</li>
        <li>List all email addresses that have Confluence data.</li>
        </ul>
        </div>
        </div>
        """, unsafe_allow_html=True)

    # Display spinner and answer at the bottom of the page
    st.markdown("---")
    if st.session_state.get("processing_question", False):
        with st.spinner("Processing your question..."):
            question = st.session_state.get("custom_question", "")
            if question:
                index = ingest_data()
                answer = answer_question(index, "vijayanands@gmail.com", question)
                st.session_state.question_answer = answer
            st.session_state.processing_question = False
            st.rerun()

    if "question_answer" in st.session_state and st.session_state.question_answer:
        st.subheader("Answer to your question:")
        st.write(st.session_state.question_answer)
        # Clear the answer after displaying
        st.session_state.question_answer = None


def dashboard_conversational():
    if "current_view" not in st.session_state:
        st.session_state.current_view = "main"

    if st.session_state.current_view != "main":
        if st.button("Back to Dashboard", key=f"back_{st.session_state.current_view}"):
            st.session_state.current_view = "main"
            st.session_state.selected_skill_for_improvement = None
            st.session_state.add_skill_mode = False
            st.session_state.skills_edit_mode = False
            st.rerun()

    if st.session_state.current_view == "main":
        selected_prompt = st.selectbox(
            "", PROMPT_OPTIONS, index=0, key="action_selector"
        )

        if selected_prompt != "Select an action":
            st.session_state.current_view = PROMPT_MAP.get(selected_prompt, selected_prompt)
            st.rerun()

        return selected_prompt  # Return the selected action

    elif st.session_state.current_view == "self_appraisal":
        perform_self_appraisal()
    elif st.session_state.current_view == "weekly_report":
        perform_weekly_report_generation()
    elif st.session_state.current_view == "producivity_dashboard":
        display_productivity_dashboard()
    elif st.session_state.current_view == "sdlc_timeline_view":
        display_development_cycle_metrics()
    elif st.session_state.current_view == "compare_productivity_data":
        st.error("Functionality not yet implemented.")
    elif st.session_state.current_view == "top_performers":
        st.error("Functionality not yet implemented.")
    elif st.session_state.current_view == "bottom_performers":
        st.error("Functionality not yet implemented.")
    elif st.session_state.current_view == "code_quality_analysis":
        st.error("Functionality not yet implemented.")
    else:
        st.error("Invalid view selected. Please go back to the main dashboard.")

    return st.session_state.current_view  # Return the current view for all cases
