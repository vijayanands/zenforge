import datetime

import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts

from demo_code.ui.style import (apply_styled_dropdown_css, create_pie_chart,
                                create_progress_bar, create_styled_tabs,
                                display_pie_chart)


def ic_learning_dashboard():
    st.title("My Learning Dashboard")

    tab_labels = ["Learning Status", "Courses", "Compliance", "Learning Opportunities"]
    tabs = create_styled_tabs(tab_labels)

    with tabs[0]:
        learning_status_tab()

    with tabs[1]:
        courses_tab()

    with tabs[2]:
        compliance_tab()

    with tabs[3]:
        learning_opportunities_tab()


def learning_status_tab():
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("Overall Progress")

        # Create data for the pie chart
        data = pd.DataFrame(
            {"Status": ["Completed", "In Progress", "Not Started"], "Value": [3, 2, 2]}
        )

        # Create and display the pie chart
        fig = create_pie_chart(
            data=data,
            names="Status",
            values="Value",
            title="Course Status",
            color_sequence=["#28a745", "#ffc107", "#dc3545"],  # Green, Yellow, Red
            hole=0.4,
            height=300,
            width=300,
            show_legend=True,
            text_info="percent",
            hover_info="label+percent+value",
        )
        display_pie_chart(fig)

        st.metric("Learning Alignment", "80%", "Performance Feedback")

    with col2:
        st.header("Course Progress")
        courses = [
            {"name": "Python Basics", "progress": 100, "status": "Completed"},
            {
                "name": "Data Analysis with Pandas",
                "progress": 75,
                "status": "In Progress",
            },
            {
                "name": "Machine Learning Fundamentals",
                "progress": 50,
                "status": "In Progress",
            },
            {"name": "Advanced SQL", "progress": 100, "status": "Completed"},
            {
                "name": "Cloud Computing Essentials",
                "progress": 0,
                "status": "Not Started",
            },
        ]

        for course in courses:
            create_progress_bar(course["name"], course["progress"], course["status"])


def courses_tab():
    courses = [
        {
            "name": "Python Basics",
            "status": "Completed",
            "completion_date": "2024-03-15",
        },
        {
            "name": "Data Analysis with Pandas",
            "status": "In Progress",
            "expected_completion": "2024-10-30",
        },
        {
            "name": "Machine Learning Fundamentals",
            "status": "In Progress",
            "expected_completion": "2024-11-15",
        },
        {
            "name": "Advanced SQL",
            "status": "Completed",
            "completion_date": "2024-05-01",
        },
        {
            "name": "Cloud Computing Essentials",
            "status": "Not Started",
            "start_date": "2024-12-01",
        },
        {
            "name": "Web Development with Django",
            "status": "Not Started",
            "start_date": "2025-01-15",
        },
        {
            "name": "Data Visualization with Matplotlib",
            "status": "Not Started",
            "start_date": "2025-02-01",
        },
    ]

    for course in courses:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{course['name']}**")
        with col2:
            if course["status"] == "Completed":
                st.write(f"Completed on: {course['completion_date']}")
            elif course["status"] == "In Progress":
                st.write(f"Expected completion: {course['expected_completion']}")
            else:
                st.write(f"Starts on: {course['start_date']}")
        with col3:
            if course["status"] == "Completed":
                st.success("Completed")
            elif course["status"] == "In Progress":
                st.info("In Progress")
            else:
                st.warning("Not Started")
        st.write("---")


def compliance_tab():
    compliance_courses = [
        {
            "name": "Data Privacy and Security",
            "status": "Completed",
            "due_date": "2024-06-30",
            "completion_date": "2024-06-15",
        },
        {
            "name": "Workplace Ethics",
            "status": "In Progress",
            "due_date": "2024-11-15",
            "progress": 60,
        },
        {
            "name": "Health and Safety",
            "status": "Not Started",
            "due_date": "2024-12-31",
        },
    ]

    for course in compliance_courses:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{course['name']}**")
            if course["status"] == "In Progress":
                st.progress(course["progress"])
        with col2:
            st.write(f"Due date: {course['due_date']}")
            if course["status"] == "Completed":
                st.write(f"Completed on: {course['completion_date']}")
        with col3:
            if course["status"] == "Completed":
                st.success("Completed")
            elif course["status"] == "In Progress":
                st.info("In Progress")
            else:
                st.warning("Not Started")
        st.write("---")

    st.header("Compliance Alerts")
    st.warning("Workplace Ethics course due in 30 days (Due: Nov 15, 2024)")
    st.info("Health and Safety course not started (Due: Dec 31, 2024)")


def learning_opportunities_tab():
    st.header("Course Filters")

    # Apply the generalized styled dropdown CSS
    apply_styled_dropdown_css()

    col1, col2 = st.columns(2)
    with col1:
        category = st.selectbox(
            "Category", ["All", "Programming", "Data Science", "Cloud Computing"]
        )
    with col2:
        date_range = st.date_input(
            "Date Range", [datetime.date(2024, 1, 1), datetime.date(2024, 12, 31)]
        )

    if st.button("Apply Filters"):
        st.write(f"Filtered by: Category: {category}, Date Range: {date_range}")

    st.header("Available Courses")
    courses = [
        "Advanced Python Programming",
        "Big Data Analytics",
        "AWS Certified Solutions Architect",
        "Deep Learning Specialization",
        "Agile Project Management",
    ]

    for course in courses:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{course}**")
            st.write("Course description would go here...")
        with col2:
            if st.button("Enroll", key=course):
                st.success(f"Enrolled in {course}")
                st.write("Course details:")
                details = {
                    "Start Date": "October 1, 2024",
                    "Duration": "8 weeks",
                    "Instructor": "Dr. Jane Smith",
                }
                st.json(details)
        st.write("---")


if __name__ == "__main__":
    ic_learning_dashboard()
