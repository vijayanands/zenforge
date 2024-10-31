import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
import plotly.express as px

# Database connection
def get_database_connection():
    db_name = "zenforge_sample_data"
    user = "postgres"
    password = "postgres"
    host = "localhost"
    port = "5432"
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(connection_string)

def get_project_list():
    engine = get_database_connection()
    query = """
    SELECT id, title, start_date, status 
    FROM sdlc_timeseries.projects
    ORDER BY start_date DESC
    """
    return pd.read_sql_query(query, engine)

def get_design_phase_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        design_type,
        MIN(timestamp) as start_time,
        MAX(timestamp) as end_time,
        string_agg(DISTINCT author, ', ') as authors,
        string_agg(DISTINCT stakeholders, ', ') as stakeholders
    FROM sdlc_timeseries.design_events
    WHERE event_id = %(project_id)s
    GROUP BY design_type
    ORDER BY start_time
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})

def get_sprint_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        id,
        start_date,
        end_date,
        planned_story_points,
        completed_story_points,
        planned_stories,
        completed_stories,
        team_velocity,
        burndown_efficiency,
        status
    FROM sdlc_timeseries.sprints
    WHERE event_id = %(project_id)s
    ORDER BY start_date
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})

def get_commit_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        DATE(timestamp) as commit_date,
        COUNT(*) as commit_count,
        AVG(code_coverage) as avg_coverage,
        AVG(lint_score) as avg_lint_score,
        SUM(files_changed) as total_files_changed,
        SUM(lines_added) as total_lines_added,
        SUM(lines_removed) as total_lines_removed
    FROM sdlc_timeseries.code_commits
    WHERE event_id = %(project_id)s
    GROUP BY DATE(timestamp)
    ORDER BY commit_date
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})

def get_pr_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        DATE(created_at) as pr_date,
        status,
        COUNT(*) as pr_count,
        AVG(EXTRACT(EPOCH FROM (merged_at - created_at))/3600) as avg_time_to_merge
    FROM sdlc_timeseries.pull_requests
    WHERE project_id = %(project_id)s
    GROUP BY DATE(created_at), status
    ORDER BY pr_date
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})

def get_cicd_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        DATE(timestamp) as deployment_date,
        environment,
        event_type,
        status,
        COUNT(*) as event_count,
        AVG(duration_seconds) as avg_duration
    FROM sdlc_timeseries.cicd_events
    WHERE event_id = %(project_id)s
    GROUP BY DATE(timestamp), environment, event_type, status
    ORDER BY deployment_date
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})

def get_bug_data(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        DATE(created_date) as bug_date,
        severity,
        status,
        COUNT(*) as bug_count,
        AVG(resolution_time_hours) as avg_resolution_time
    FROM sdlc_timeseries.bugs
    WHERE event_id = %(project_id)s AND severity = 'P0'
    GROUP BY DATE(created_date), severity, status
    ORDER BY bug_date
    """
    return pd.read_sql_query(query, engine, params={'project_id': project_id})


def create_timeline_visualization(design_data, sprint_data, commit_data, pr_data, cicd_data, bug_data):
    # Create figure with subplots
    fig = make_subplots(
        rows=6, cols=1,
        subplot_titles=("Design Phase", "Sprint Progress", "Commits", "Pull Requests", "CI/CD Events", "P0 Bugs"),
        vertical_spacing=0.05,
        row_heights=[0.2, 0.2, 0.15, 0.15, 0.15, 0.15]  # Changed from 'heights' to 'row_heights'
    )

    # Design Phase Timeline
    if not design_data.empty:
        for idx, row in design_data.iterrows():
            fig.add_trace(
                go.Bar(
                    x=[row['start_time'], row['end_time']],
                    y=[row['design_type'], row['design_type']],
                    orientation='h',
                    name=row['design_type'],
                    showlegend=False
                ),
                row=1, col=1
            )

    # Sprint Progress
    if not sprint_data.empty:
        fig.add_trace(
            go.Scatter(
                x=sprint_data['end_date'],
                y=sprint_data['completed_story_points'],
                mode='lines+markers',
                name='Completed Story Points',
                line=dict(color='green')
            ),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(
                x=sprint_data['end_date'],
                y=sprint_data['planned_story_points'],
                mode='lines+markers',
                name='Planned Story Points',
                line=dict(color='blue')
            ),
            row=2, col=1
        )

    # Commit Activity
    if not commit_data.empty:
        fig.add_trace(
            go.Bar(
                x=commit_data['commit_date'],
                y=commit_data['commit_count'],
                name='Commits',
                marker_color='purple'
            ),
            row=3, col=1
        )

    # Pull Requests
    if not pr_data.empty:
        status_colors = {
            'OPEN': 'yellow',
            'MERGED': 'green',
            'BLOCKED': 'red'
        }
        for status in pr_data['status'].unique():
            status_data = pr_data[pr_data['status'] == status]
            fig.add_trace(
                go.Scatter(
                    x=status_data['pr_date'],
                    y=status_data['pr_count'],
                    mode='lines+markers',
                    name=f'PRs - {status}',
                    line=dict(color=status_colors.get(status, 'gray'))
                ),
                row=4, col=1
            )

    # CI/CD Events
    if not cicd_data.empty:
        env_colors = {
            'dev': 'lightblue',
            'staging': 'blue',
            'qa': 'darkblue',
            'production': 'navy'
        }
        for env in cicd_data['environment'].unique():
            env_data = cicd_data[cicd_data['environment'] == env]
            fig.add_trace(
                go.Bar(
                    x=env_data['deployment_date'],
                    y=env_data['event_count'],
                    name=f'CI/CD - {env}',
                    marker_color=env_colors.get(env, 'blue')
                ),
                row=5, col=1
            )

    # Bugs
    if not bug_data.empty:
        status_colors = {
            'Open': 'red',
            'In Progress': 'orange',
            'Fixed': 'green'
        }
        for status in bug_data['status'].unique():
            status_data = bug_data[bug_data['status'] == status]
            fig.add_trace(
                go.Scatter(
                    x=status_data['bug_date'],
                    y=status_data['bug_count'],
                    mode='lines+markers',
                    name=f'P0 Bugs - {status}',
                    line=dict(color=status_colors.get(status, 'gray'))
                ),
                row=6, col=1
            )

    # Update layout
    fig.update_layout(
        height=1200,
        showlegend=True,
        title_text="Software Development Lifecycle Timeline",
        template="plotly_white"
    )

    # Update y-axes labels
    fig.update_yaxes(title_text="Design Type", row=1, col=1)
    fig.update_yaxes(title_text="Story Points", row=2, col=1)
    fig.update_yaxes(title_text="Commit Count", row=3, col=1)
    fig.update_yaxes(title_text="PR Count", row=4, col=1)
    fig.update_yaxes(title_text="Event Count", row=5, col=1)
    fig.update_yaxes(title_text="Bug Count", row=6, col=1)

    # Update x-axes labels
    fig.update_xaxes(title_text="Date", row=6, col=1)  # Only show date label on bottom plot

    # Update subplot spacing
    fig.update_layout(
        height=1200,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=100, b=100)  # Add more margin at top and bottom
    )

    return fig

def create_timeline_gantt(design_data, sprint_data, commit_data, pr_data, cicd_data, bug_data, project_info):
    """Create a Gantt chart showing the timeline of different phases"""

    def get_date_range(df, start_col, end_col):
        if df.empty:
            return None, None
        start = df[start_col].min()
        end = df[end_col].max()
        return start, end

    # Collect all timeline data
    timeline_data = []

    # Add Design Phase
    if not design_data.empty:
        for _, row in design_data.iterrows():
            timeline_data.append({
                'Task': f"Design: {row['design_type']}",
                'Start': row['start_time'],
                'Finish': row['end_time'],
                'Phase': 'Design',
                'Details': f"Authors: {row['authors']}\nStakeholders: {row['stakeholders']}"
            })

    # Add Sprints
    if not sprint_data.empty:
        for _, row in sprint_data.iterrows():
            timeline_data.append({
                'Task': f"Sprint: {row['id']}",
                'Start': row['start_date'],
                'Finish': row['end_date'],
                'Phase': 'Sprint',
                'Details': f"Completed: {row['completed_story_points']}/{row['planned_story_points']} points"
            })

    # Add Development Phases (based on commit activity)
    if not commit_data.empty:
        timeline_data.append({
            'Task': 'Development',
            'Start': commit_data['commit_date'].min(),
            'Finish': commit_data['commit_date'].max(),
            'Phase': 'Development',
            'Details': f"Total Commits: {commit_data['commit_count'].sum()}"
        })

    # Add PR Phase
    if not pr_data.empty:
        timeline_data.append({
            'Task': 'Code Reviews',
            'Start': pd.to_datetime(pr_data['pr_date'].min()),
            'Finish': pd.to_datetime(pr_data['pr_date'].max()),
            'Phase': 'Code Review',
            'Details': f"Total PRs: {pr_data['pr_count'].sum()}"
        })

    # Add CI/CD Phase
    if not cicd_data.empty:
        for env in cicd_data['environment'].unique():
            env_data = cicd_data[cicd_data['environment'] == env]
            timeline_data.append({
                'Task': f"CI/CD: {env}",
                'Start': env_data['deployment_date'].min(),
                'Finish': env_data['deployment_date'].max(),
                'Phase': 'CI/CD',
                'Details': f"Environment: {env}\nEvents: {env_data['event_count'].sum()}"
            })

    # Create DataFrame
    df = pd.DataFrame(timeline_data)

    # Create Gantt chart
    colors = {
        'Design': '#2E86C1',
        'Sprint': '#28B463',
        'Development': '#8E44AD',
        'Code Review': '#D35400',
        'CI/CD': '#1ABC9C'
    }

    fig = px.timeline(df, x_start="Start", x_end="Finish", y="Task", color="Phase",
                      color_discrete_map=colors,
                      hover_data=["Details"])

    # Update layout
    fig.update_layout(
        title="Project Timeline",
        height=400,
        xaxis=dict(
            title="Date",
            tickformat="%Y-%m-%d",
            tickangle=45,
        ),
        yaxis=dict(
            title="",
            categoryorder="total ascending"
        ),
        showlegend=True,
        legend_title="Phase",
        hovermode="x unified"
    )

    return fig


def create_metrics_dashboard(design_data, sprint_data, commit_data, pr_data, cicd_data, bug_data):
    """Create a dashboard of key metrics"""

    # Sprint Burndown
    if not sprint_data.empty:
        sprint_fig = go.Figure()
        sprint_fig.add_trace(go.Scatter(
            x=sprint_data['end_date'],
            y=sprint_data['completed_story_points'],
            name='Completed Points',
            mode='lines+markers',
            line=dict(color='green')
        ))
        sprint_fig.add_trace(go.Scatter(
            x=sprint_data['end_date'],
            y=sprint_data['planned_story_points'],
            name='Planned Points',
            mode='lines+markers',
            line=dict(color='blue', dash='dash')
        ))
        sprint_fig.update_layout(
            title="Sprint Burndown",
            xaxis_title="Sprint End Date",
            yaxis_title="Story Points",
            height=300
        )
    else:
        sprint_fig = None

    # Development Activity
    if not commit_data.empty:
        commit_fig = px.bar(commit_data,
                            x='commit_date',
                            y='commit_count',
                            title="Daily Commit Activity")
        commit_fig.update_layout(height=300)
    else:
        commit_fig = None

    return sprint_fig, commit_fig


def create_metric_card(title, value, delta=None, help_text=None):
    """Create a styled metric card"""
    st.markdown(
        f"""
        <div style="
            padding: 1rem;
            border-radius: 0.5rem;
            background: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
            margin-bottom: 1rem;
        ">
            <h3 style="margin: 0 0 0.5rem 0; color: #1f1f1f;">{title}</h3>
            <p style="font-size: 1.5rem; margin: 0; color: #2e86c1;">{value}</p>
            {f'<p style="font-size: 0.8rem; margin: 0.5rem 0 0 0; color: #666;">{help_text}</p>' if help_text else ''}
        </div>
        """,
        unsafe_allow_html=True
    )


def main():
    st.set_page_config(page_title="SDLC Timeline", layout="wide")

    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1rem;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("Software Development Lifecycle Timeline")

    try:
        projects_df = get_project_list()
        project_options = ['None'] + projects_df['id'].tolist()

        selected_project = st.selectbox(
            "Select Project",
            options=project_options,
            format_func=lambda x: x if x == 'None' else f"{x} - {projects_df[projects_df['id'] == x]['title'].iloc[0]}"
        )

        if selected_project and selected_project != 'None':
            project_info = projects_df[projects_df['id'] == selected_project].iloc[0]

            # Project Information Header
            st.markdown(f"""
                <div style="
                    padding: 1.5rem;
                    border-radius: 0.5rem;
                    background: white;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
                    margin-bottom: 2rem;
                ">
                    <h2 style="margin: 0;">{project_info['title']}</h2>
                    <p style="margin: 0.5rem 0;">Status: {project_info['status']} | Started: {project_info['start_date'].strftime('%Y-%m-%d')}</p>
                </div>
            """, unsafe_allow_html=True)

            # Fetch all data
            with st.spinner('Loading project data...'):
                design_data = get_design_phase_data(selected_project)
                sprint_data = get_sprint_data(selected_project)
                commit_data = get_commit_data(selected_project)
                pr_data = get_pr_data(selected_project)
                cicd_data = get_cicd_data(selected_project)
                bug_data = get_bug_data(selected_project)

            # Timeline View
            st.subheader("Project Timeline")
            timeline_fig = create_timeline_gantt(
                design_data, sprint_data, commit_data, pr_data, cicd_data, bug_data, project_info
            )
            st.plotly_chart(timeline_fig, use_container_width=True)

            # Create metric dashboard
            sprint_fig, commit_fig = create_metrics_dashboard(
                design_data, sprint_data, commit_data, pr_data, cicd_data, bug_data
            )

            # Detailed Metrics in Tabs with Cards
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "Design", "Sprint Progress", "Development", "CI/CD", "Quality"
            ])

            with tab1:
                if not design_data.empty:
                    st.markdown("### Design Phase Metrics")
                    for _, row in design_data.iterrows():
                        duration = (row['end_time'] - row['start_time']).days
                        create_metric_card(
                            row['design_type'],
                            f"{duration} days",
                            help_text=f"Authors: {row['authors']}\nStakeholders: {row['stakeholders']}"
                        )
                else:
                    st.info("No design phase data available")

            with tab2:
                if not sprint_data.empty:
                    st.plotly_chart(sprint_fig, use_container_width=True)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        create_metric_card(
                            "Average Velocity",
                            f"{sprint_data['team_velocity'].mean():.1f}",
                            help_text="Points completed per sprint"
                        )
                    with col2:
                        completion_rate = (
                                sprint_data['completed_stories'].sum() /
                                sprint_data['planned_stories'].sum() * 100
                        )
                        create_metric_card(
                            "Completion Rate",
                            f"{completion_rate:.1f}%",
                            help_text="Stories completed vs planned"
                        )
                    with col3:
                        create_metric_card(
                            "Total Story Points",
                            f"{sprint_data['completed_story_points'].sum()}",
                            help_text="Completed across all sprints"
                        )
                else:
                    st.info("No sprint data available")

            with tab3:
                if not commit_data.empty:
                    st.plotly_chart(commit_fig, use_container_width=True)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        create_metric_card(
                            "Total Commits",
                            commit_data['commit_count'].sum(),
                            help_text="Across all branches"
                        )
                    with col2:
                        create_metric_card(
                            "Code Coverage",
                            f"{commit_data['avg_coverage'].mean():.1f}%",
                            help_text="Average across all commits"
                        )
                    with col3:
                        create_metric_card(
                            "Code Changes",
                            f"+{commit_data['total_lines_added'].sum()}/-{commit_data['total_lines_removed'].sum()}",
                            help_text="Lines added/removed"
                        )
                else:
                    st.info("No commit data available")

            with tab4:
                if not cicd_data.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        success_rate = (
                                len(cicd_data[cicd_data['status'] == 'success']) /
                                len(cicd_data) * 100
                        )
                        create_metric_card(
                            "Build Success Rate",
                            f"{success_rate:.1f}%",
                            help_text="Successful builds percentage"
                        )
                    with col2:
                        create_metric_card(
                            "Average Build Duration",
                            f"{cicd_data['avg_duration'].mean():.0f}s",
                            help_text="Average build time in seconds"
                        )
                else:
                    st.info("No CI/CD data available")

            with tab5:
                if not bug_data.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        create_metric_card(
                            "Total P0 Bugs",
                            bug_data['bug_count'].sum(),
                            help_text="High priority bugs"
                        )
                    with col2:
                        avg_resolution = bug_data['avg_resolution_time'].mean()
                        if pd.notna(avg_resolution):
                            create_metric_card(
                                "Average Resolution Time",
                                f"{avg_resolution:.1f}h",
                                help_text="Average time to fix P0 bugs"
                            )
                else:
                    st.info("No bug data available")

        else:
            st.info("Please select a project to view its timeline and metrics.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check your database connection and try again.")


if __name__ == "__main__":
    main()