import numpy as np
import pandas as pd
import streamlit as st

from demo_code.ui.style import (
    create_progress_bar,
    create_styled_metric,
    create_styled_tabs,
)


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

def ic_perf_and_career_dashboard():
    st.title("Employee Performance and Career Dashboard")
    st.subheader("John Doe - Software Engineer")

    tab_labels = ["Goals"]
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

if __name__ == "__main__":
    ic_perf_and_career_dashboard()
