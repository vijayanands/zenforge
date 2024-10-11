from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

from ui.style import (create_pie_chart, create_progress_bar,
                      create_styled_bullet_list, create_styled_metric,
                      create_styled_tabs, display_pie_chart)


def get_overall_performance():
    return np.random.randint(1, 11)


def generate_goals():
    goals = [
        "Improve coding skills",
        "Enhance communication",
        "Complete project X",
        "Learn new technology Y",
        "Mentor junior team members",
    ]
    return pd.DataFrame(
        {"Goal": goals, "Progress": np.random.randint(0, 101, len(goals))}
    )


def generate_feedback():
    feedback = [
        "Great job on the recent project!",
        "Consider improving time management",
        "Excellent teamwork skills displayed",
        "Work on technical documentation",
    ]
    return pd.DataFrame(
        {
            "Feedback": feedback,
            "Date": [
                datetime.now() - timedelta(days=i * 7) for i in range(len(feedback))
            ],
        }
    )


def generate_performance_trend():
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    return pd.DataFrame(
        {"Quarter": quarters, "Performance": np.random.randint(1, 11, len(quarters))}
    )


def ic_perf_and_career_dashboard():
    st.title("Employee Performance and Career Dashboard")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.subheader("John Doe - Software Engineer")

    with col2:
        overall_performance = get_overall_performance()
        create_styled_metric("Overall Performance", f"{overall_performance}/10", "🌟")

    tab_labels = ["Goals", "Feedback", "Performance", "Career"]
    tabs = create_styled_tabs(tab_labels)

    with tabs[0]:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_styled_metric("Annual Goals Set", "5", "🎯")
        with col2:
            create_styled_metric("Goals Achieved", "2", "✅")
        with col3:
            create_styled_metric("Goals in Progress", "3", "🚀")
        with col4:
            create_styled_metric("Completion Rate", "40%", "📊")

        goals_df = generate_goals()
        st.subheader("Goal Progress")
        for _, row in goals_df.iterrows():
            create_progress_bar(
                row["Goal"],
                row["Progress"],
                "In Progress" if row["Progress"] < 100 else "Completed",
            )

    with tabs[1]:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            create_styled_metric("Feedback Sessions Attended", "4", "👥")
        with col2:
            create_styled_metric("Feedback Action Items", "10", "📝")
        with col3:
            create_styled_metric("Action Items Completed", "7", "✅")
        with col4:
            create_styled_metric("Pending Feedback Items", "3", "⏳")

        st.subheader("Feedback Inbox")
        feedback_df = generate_feedback()
        st.dataframe(feedback_df, use_container_width=True)

    with tabs[2]:
        st.subheader("Performance Overview")

        # Create two columns for the charts
        col1, col2 = st.columns(2)

        with col1:
            performance_df = generate_performance_trend()
            fig_performance = create_pie_chart(
                performance_df,
                names="Quarter",
                values="Performance",
                title="Performance Trend",
                hole=0.3,
                height=300,
                width=300,
            )
            display_pie_chart(fig_performance, use_container_width=False)

        with col2:
            skills = ["Technical Skills", "Communication", "Leadership", "Teamwork"]
            ratings = np.random.randint(1, 11, len(skills))
            skill_df = pd.DataFrame({"Skill": skills, "Rating": ratings})
            fig_skills = create_pie_chart(
                skill_df,
                names="Skill",
                values="Rating",
                title="Skill Ratings",
                hole=0.3,
                height=300,
                width=300,
            )
            display_pie_chart(fig_skills, use_container_width=False)

        # Add some vertical space
        st.markdown("<br>", unsafe_allow_html=True)

        st.subheader("Detailed Analytics & Insights")
        col1, col2 = st.columns(2)

        with col1:
            create_styled_bullet_list(
                ["Problem-solving", "Team collaboration", "Adaptability"], "Strengths"
            )
            create_styled_bullet_list(
                ["Time management", "Public speaking", "Documentation skills"],
                "Areas for Improvement",
            )

        with col2:
            create_styled_bullet_list(
                [
                    "Successfully delivered Project X",
                    "Mentored 2 junior developers",
                    "Improved team's code review process",
                ],
                "Achievements",
            )

    with tabs[3]:
        st.header("Career Trajectory and Gaps")
        col1, col2 = st.columns(2)

        with col1:
            create_styled_bullet_list(
                [
                    "Current Position: Software Engineer",
                    "Target Position: Senior Software Engineer",
                ],
                "Career Path",
            )

        with col2:
            create_styled_bullet_list(
                [
                    "Advanced system design",
                    "Project management",
                    "Machine learning fundamentals",
                ],
                "Skills to Develop",
            )

        if st.button("What are my gaps?"):
            gaps = [
                "Need more experience leading large-scale projects",
                "Improve mentoring and leadership skills",
                "Deepen knowledge in cloud architecture",
                "Enhance cross-functional collaboration skills",
            ]
            create_styled_bullet_list(gaps, "Identified Gaps")

        st.header("Self Appraisal")
        last_appraisal = datetime.now() - timedelta(days=180)
        st.write(f"Last submitted: {last_appraisal.strftime('%B %d, %Y')}")
        if st.button("Generate Self Appraisal"):
            st.success("Self Appraisal form generated and sent to your email.")


if __name__ == "__main__":
    ic_perf_and_career_dashboard()
