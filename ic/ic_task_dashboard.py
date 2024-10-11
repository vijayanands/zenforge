from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def create_styled_task_list(tasks, title):
    styled_list_css = """
    <style>
    .styled-task-list-container {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 20px;
        height: 100%;
    }
    .styled-task-list-title {
        font-size: 18px;
        font-weight: bold;
        color: #495057;
        margin-bottom: 10px;
    }
    .styled-task-list {
        list-style-type: none;
        padding-left: 0;
        margin-bottom: 0;
    }
    .styled-task-list li {
        position: relative;
        padding-left: 25px;
        margin-bottom: 12px;
        line-height: 1.5;
        color: #495057;
    }
    .styled-task-list li:before {
        content: '•';
        position: absolute;
        left: 10px;
        color: #495057;
        font-size: 18px;
        line-height: 1.2;
    }
    .styled-task-list li:last-child {
        margin-bottom: 0;
    }
    .task-caption {
        font-size: 12px;
        color: #6c757d;
        margin-top: 2px;
    }
    </style>
    """

    task_items = "".join(
        [
            f"<li>{task['name']}<div class='task-caption'>{task['project']}</div></li>"
            for task in tasks
        ]
    )
    list_html = f"""
    <div class="styled-task-list-container">
        <div class="styled-task-list-title">{title}</div>
        <ul class="styled-task-list">
            {task_items}
        </ul>
    </div>
    """

    # Combine the CSS and the list HTML
    full_html = styled_list_css + list_html

    # Render the styled list using st.markdown
    st.markdown(full_html, unsafe_allow_html=True)


def set_page_config():
    st.markdown(
        """
    <style>
    .stApp {
        background-color: #f0f2f6;
    }
    .card {
        background-color: white;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        padding: 20px;
        margin-bottom: 20px;
    }
    .card-title {
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 15px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )


def generate_dummy_data():
    return {
        "last_report_sent": datetime.now() - timedelta(days=7),
        "next_report_scheduled": datetime.now() + timedelta(days=7),
        "active_projects": 2,
        "tasks_assigned": 10,
        "tasks_completed": 7,
        "tasks_in_progress": 3,
        "upcoming_deadline": datetime.now() + timedelta(days=2),
        "task_id": "1234",
    }


def create_bar_chart(data):
    categories = ["Assigned", "Completed", "In Progress"]
    values = [
        data["tasks_assigned"],
        data["tasks_completed"],
        data["tasks_in_progress"],
    ]

    fig = go.Figure(
        data=[go.Bar(x=categories, y=values, marker_color="rgb(102,102,255)")]
    )
    fig.update_layout(
        title_text="Task Overview",
        xaxis_title="Status",
        yaxis_title="Number of Tasks",
        plot_bgcolor="rgba(0,0,0,0)",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    return fig


def card(title, content):
    st.markdown(
        f'<div class="card"><div class="card-title">{title}</div>{content}</div>',
        unsafe_allow_html=True,
    )


def task_board():
    tasks = {
        "To Do": [
            {"name": "Design UI mockups", "project": "Project A"},
            {"name": "Deploy to staging", "project": "Project B"},
        ],
        "In Progress": [
            {"name": "Implement login functionality", "project": "Project B"},
            {"name": "Conduct user testing", "project": "Project A"},
        ],
        "Completed": [{"name": "Write unit tests", "project": "Project A"}],
    }

    cols = st.columns(3)
    for i, (status, task_list) in enumerate(tasks.items()):
        with cols[i]:
            create_styled_task_list(task_list, status)


def ic_tasks_dashboard():
    set_page_config()
    st.title("My Tasks Dashboard")

    data = generate_dummy_data()

    # Weekly Report Status
    card(
        "Weekly Report",
        """
    <table width="100%">
        <tr>
            <td>Last Report Sent:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Next Report Scheduled:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Recipients:</td>
            <td>Team Lead, Project Manager</td>
        </tr>
    </table>
    """.format(
            data["last_report_sent"].strftime("%b %d, %Y"),
            data["next_report_scheduled"].strftime("%b %d, %Y"),
        ),
    )

    # Project Status
    card(
        "Project Status",
        """
    <table width="100%">
        <tr>
            <td>Active Projects:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Tasks Assigned:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Tasks Completed:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Tasks In Progress:</td>
            <td>{}</td>
        </tr>
        <tr>
            <td>Upcoming Deadlines:</td>
            <td>Task ID {} due on {}</td>
        </tr>
    </table>
    """.format(
            data["active_projects"],
            data["tasks_assigned"],
            data["tasks_completed"],
            data["tasks_in_progress"],
            data["task_id"],
            data["upcoming_deadline"].strftime("%b %d, %Y"),
        ),
    )

    # Task Overview Chart
    card("Task Overview", "")
    st.plotly_chart(create_bar_chart(data), use_container_width=True)

    # Task Board
    card("Task Board", "")
    task_board()


if __name__ == "__main__":
    ic_tasks_dashboard()
