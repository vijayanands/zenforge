import streamlit as st
import uuid

from functions.ingestion import ingest_data, answer_question
from ui.ic_functions.individual_contributor import individual_contributor_dashboard_conversational


def dashboard():
    st.title(
        f"Good morning vijayanands@gmail.com"
    )

    # Get the current selection
    current_action = individual_contributor_dashboard_conversational()

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