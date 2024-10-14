import pandas as pd
import plotly.express as px
import streamlit as st

from demo_code.ui.style import (apply_styled_dropdown_css,
                                create_multi_bar_chart, create_progress_bar,
                                create_styled_metric, create_styled_tabs)


def director_project_portfolio_dashboard():
    st.title("Project and Portfolio Management Dashboard")

    # Apply styled dropdown CSS
    apply_styled_dropdown_css()

    # Dummy data (unchanged)
    portfolio_data = {
        "Digital Transformation": [
            {
                "name": "Cloud Migration",
                "status": "On Track",
                "completion": 80,
                "risk": "Low",
                "budget": 1000000,
                "spent": 750000,
                "wins": "Reduced infrastructure costs by 30%",
            },
            {
                "name": "AI Integration",
                "status": "At Risk",
                "completion": 60,
                "risk": "High",
                "budget": 1500000,
                "spent": 1200000,
                "wins": "Prototype showing 25% efficiency increase",
            },
        ],
        "Customer Experience": [
            {
                "name": "Mobile App Redesign",
                "status": "On Track",
                "completion": 90,
                "risk": "Low",
                "budget": 800000,
                "spent": 700000,
                "wins": "User engagement up by 40%",
            },
            {
                "name": "Chatbot Implementation",
                "status": "Delayed",
                "completion": 40,
                "risk": "Medium",
                "budget": 2000000,
                "spent": 1000000,
                "wins": "Successfully handling 30% of queries",
            },
        ],
    }

    team_performance = pd.DataFrame(
        {
            "name": ["Cloud Team", "AI Team", "Mobile Dev", "UX/UI Team"],
            "productivity": [85, 78, 92, 80],
            "qualityScore": [90, 85, 88, 92],
        }
    )

    resource_allocation = pd.DataFrame(
        {
            "name": [
                "Cloud Migration",
                "AI Integration",
                "Mobile App Redesign",
                "Chatbot Implementation",
            ],
            "allocated": [25, 20, 30, 15],
            "required": [30, 25, 30, 20],
        }
    )

    development_trends = pd.DataFrame(
        {
            "month": ["Jan", "Feb", "Mar", "Apr"],
            "trainingHours": [120, 150, 180, 200],
            "projectDeliverables": [15, 18, 22, 25],
        }
    )

    # Tabs using styled tabs
    tabs = create_styled_tabs(
        [
            "Portfolio & Projects",
            "Project Overview",
            "Team Performance",
            "Resource Management",
            "Project Development",
        ]
    )

    with tabs[0]:
        for portfolio, projects in portfolio_data.items():
            st.subheader(portfolio)
            for project in projects:
                with st.expander(project["name"]):
                    col1, col2 = st.columns(2)
                    with col1:
                        create_styled_metric(project["status"], "Status", "🚦")
                        create_styled_metric(project["risk"], "Risk", "⚠️")
                    with col2:
                        create_styled_metric(
                            f"{project['completion']}%", "Completion", "🏁"
                        )
                        create_styled_metric(
                            f"${project['spent']:,}/{project['budget']:,}",
                            "Budget Spent",
                            "💰",
                        )
                    st.write(f"**Key Win:** {project['wins']}")

    with tabs[1]:
        df = pd.DataFrame([proj for projs in portfolio_data.values() for proj in projs])

        st.subheader("Project Performance Overview")
        fig = create_multi_bar_chart(
            df,
            "name",
            ["spent", "budget", "completion"],
            {
                "spent": "Budget Spent ($)",
                "budget": "Total Budget ($)",
                "completion": "Completion (%)",
            },
            "Project Performance Comparison",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Project Status Overview")
        for _, row in df.iterrows():
            create_progress_bar(row["name"], row["completion"], row["status"])

    with tabs[2]:
        st.subheader("Team Performance Metrics")
        fig = create_multi_bar_chart(
            team_performance,
            "name",
            ["productivity", "qualityScore"],
            {"productivity": "Productivity", "qualityScore": "Quality Score"},
            "Team Performance Comparison",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.write(
            "This chart compares the productivity and quality scores across teams. Productivity is measured by task completion rate, while quality score is based on code reviews and client feedback."
        )

    with tabs[3]:
        st.subheader("Resource Allocation vs. Requirements")
        fig = create_multi_bar_chart(
            resource_allocation,
            "name",
            ["allocated", "required"],
            {"allocated": "Allocated", "required": "Required"},
            "Resource Allocation Comparison",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.write("Resources are measured in full-time equivalents (FTEs).")

    with tabs[4]:
        st.subheader("Project Development Trends")
        fig = px.line(
            development_trends, x="month", y=["trainingHours", "projectDeliverables"]
        )
        st.plotly_chart(fig, use_container_width=True)
        st.write(
            "This chart shows the relationship between investment in training and project output over time."
        )


# This function can be called from another Python script
if __name__ == "__main__":
    director_project_portfolio_dashboard()
