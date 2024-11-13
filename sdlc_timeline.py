import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from model.sdlc_events import Environment, BuildStatus


def safe_dataframe_check(df):
    """Safely check if a dataframe is empty or None"""
    return df is not None and not df.empty


def get_database_connection():
    try:
        db_name = "zenforge_sample_data"
        user = "postgres"
        password = "postgres"
        host = "localhost"
        port = "5432"
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        engine = create_engine(connection_string)
        # Test the connection with text() to make it executable
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return engine
    except SQLAlchemyError as e:
        st.error(f"Database connection failed: {str(e)}")
        return None


def safe_read_sql(query, engine, params=None):
    """Safely execute SQL query and return empty DataFrame if failed"""
    try:
        if engine is None:
            return pd.DataFrame()
        return pd.read_sql_query(query, engine, params=params)
    except SQLAlchemyError as e:
        st.error(f"Query execution failed: {str(e)}")
        return pd.DataFrame()


def get_project_list():
    engine = get_database_connection()
    query = """
    SELECT id, title, start_date, status 
    FROM sdlc_timeseries.projects
    ORDER BY start_date DESC
    """
    return safe_read_sql(query, engine)


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
    return safe_read_sql(query, engine, params={"project_id": project_id})


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
    return safe_read_sql(query, engine, params={"project_id": project_id})


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
    return safe_read_sql(query, engine, params={"project_id": project_id})


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
    return safe_read_sql(query, engine, params={"project_id": project_id})


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
    WHERE project_id = %(project_id)s AND severity = 'P0'
    GROUP BY DATE(created_date), severity, status
    ORDER BY bug_date
    """
    return safe_read_sql(query, engine, params={"project_id": project_id})


def get_jira_metrics(project_id):
    engine = get_database_connection()
    query = """
    SELECT 
        j.id as issue_key,
        j.created_date,
        j.completed_date as resolved_date,
        s.id as sprint_id,
        EXTRACT(EPOCH FROM (j.completed_date - j.created_date))/3600 as resolution_time_hours,
        COALESCE(
            (SELECT SUM(duration_seconds)/3600 
             FROM sdlc_timeseries.cicd_events c 
             WHERE c.event_id = j.event_id),
            0
        ) as build_time_hours,
        j.story_points
    FROM sdlc_timeseries.jira_items j
    LEFT JOIN sdlc_timeseries.sprint_jira_association sja ON j.id = sja.jira_id
    LEFT JOIN sdlc_timeseries.sprints s ON sja.sprint_id = s.id
    WHERE j.event_id = %(project_id)s
    AND j.completed_date IS NOT NULL
    ORDER BY j.created_date
    """
    return safe_read_sql(query, engine, params={"project_id": project_id})


def get_release_bug_correlation(project_id):
    engine = get_database_connection()
    query = """
    WITH releases AS (
        SELECT 
            DATE(timestamp + (duration_seconds || ' seconds')::interval) as deployment_complete_date,
            COUNT(*) as deployment_count
        FROM sdlc_timeseries.cicd_events
        WHERE event_id = %(project_id)s
        AND environment::text = %(env)s
        AND event_type = 'deployment'
        AND status::text = %(build_status)s
        GROUP BY DATE(timestamp + (duration_seconds || ' seconds')::interval)
    )
    SELECT 
        r.deployment_complete_date,
        r.deployment_count,
        COUNT(b.id) as bugs_count,
        SUM(CASE WHEN b.severity = 'P0' THEN 1 ELSE 0 END) as p0_bugs_count
    FROM releases r
    LEFT JOIN sdlc_timeseries.bugs b ON 
        b.created_date >= r.deployment_complete_date AND 
        b.created_date < r.deployment_complete_date + interval '7 days' AND
        b.project_id = %(project_id)s
    GROUP BY r.deployment_complete_date, r.deployment_count
    ORDER BY r.deployment_complete_date
    """
    return safe_read_sql(
        query,
        engine,
        params={
            "project_id": project_id,
            "env": Environment.PRODUCTION.value,
            "build_status": BuildStatus.SUCCESS.value,
        },
    )


def create_timeline_visualization(
    design_data,
    commit_data,
    pr_data,
    cicd_data,
    jira_data,
    release_bug_data,
):
    # Create figure with subplots
    fig = make_subplots(
        rows=8,
        cols=1,
        subplot_titles=(
            "Design Phase",
            "Sprint Progress",
            "JIRA Resolution Times",
            "Build Times per JIRA",
            "Commits",
            "Pull Requests",
            "CI/CD Events",
            "Release vs Bugs",
        ),
        vertical_spacing=0.05,
        row_heights=[0.15, 0.15, 0.15, 0.15, 0.1, 0.1, 0.1, 0.1],
    )

    # Design Phase Timeline
    if not design_data.empty:
        for idx, row in design_data.iterrows():
            fig.add_trace(
                go.Bar(
                    x=[row["start_time"], row["end_time"]],
                    y=[row["design_type"], row["design_type"]],
                    orientation="h",
                    name=row["design_type"],
                    showlegend=False,
                ),
                row=1,
                col=1,
            )

    # Add JIRA Resolution Times (row 3)
    if not jira_data.empty:
        fig.add_trace(
            go.Scatter(
                x=jira_data["created_date"],
                y=jira_data["resolution_time_hours"],
                mode="markers",
                name="JIRA Resolution Time",
                marker=dict(
                    size=jira_data["story_points"] * 3,
                    color="orange",
                ),
                text=jira_data["issue_key"],
            ),
            row=3,
            col=1,
        )

    # Add Build Times per JIRA (row 4)
    if not jira_data.empty:
        fig.add_trace(
            go.Bar(
                x=jira_data["issue_key"],
                y=jira_data["build_time_hours"],
                name="Build Time",
                marker_color="teal",
            ),
            row=4,
            col=1,
        )

    # Commit Activity
    if not commit_data.empty:
        fig.add_trace(
            go.Bar(
                x=commit_data["commit_date"],
                y=commit_data["commit_count"],
                name="Commits",
                marker_color="purple",
            ),
            row=5,
            col=1,
        )

    # Pull Requests
    if not pr_data.empty:
        status_colors = {"OPEN": "yellow", "MERGED": "green", "BLOCKED": "red"}
        for status in pr_data["status"].unique():
            status_data = pr_data[pr_data["status"] == status]
            fig.add_trace(
                go.Scatter(
                    x=status_data["pr_date"],
                    y=status_data["pr_count"],
                    mode="lines+markers",
                    name=f"PRs - {status}",
                    line=dict(color=status_colors.get(status, "gray")),
                ),
                row=6,
                col=1,
            )

    # CI/CD Events
    if not cicd_data.empty:
        env_colors = {
            "dev": "lightblue",
            "staging": "blue",
            "qa": "darkblue",
            "production": "navy",
        }
        for env in cicd_data["environment"].unique():
            env_data = cicd_data[cicd_data["environment"] == env]
            fig.add_trace(
                go.Bar(
                    x=env_data["deployment_date"],
                    y=env_data["event_count"],
                    name=f"CI/CD - {env}",
                    marker_color=env_colors.get(env, "blue"),
                ),
                row=7,
                col=1,
            )

    # Add Release vs Bugs correlation (row 8)
    if not release_bug_data.empty:
        # Deployments
        fig.add_trace(
            go.Bar(
                x=release_bug_data["deployment_date"],
                y=release_bug_data["deployment_count"],
                name="Deployments",
                marker_color="green",
            ),
            row=8,
            col=1,
        )
        # Bugs
        fig.add_trace(
            go.Scatter(
                x=release_bug_data["deployment_date"],
                y=release_bug_data["bugs_count"],
                mode="lines+markers",
                name="Total Bugs",
                line=dict(color="red"),
            ),
            row=8,
            col=1,
        )
        # P0 Bugs
        fig.add_trace(
            go.Scatter(
                x=release_bug_data["deployment_date"],
                y=release_bug_data["p0_bugs_count"],
                mode="lines+markers",
                name="P0 Bugs",
                line=dict(color="darkred"),
            ),
            row=8,
            col=1,
        )

    # Update layout
    fig.update_layout(
        height=1600,
        showlegend=True,
        title_text="Software Development Lifecycle Timeline",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(t=100, b=100),
    )

    # Update y-axes labels
    fig.update_yaxes(title_text="Design Type", row=1, col=1)
    fig.update_yaxes(title_text="Story Points", row=2, col=1)
    fig.update_yaxes(title_text="Resolution Hours", row=3, col=1)
    fig.update_yaxes(title_text="Build Hours", row=4, col=1)
    fig.update_yaxes(title_text="Commit Count", row=5, col=1)
    fig.update_yaxes(title_text="PR Count", row=6, col=1)
    fig.update_yaxes(title_text="Event Count", row=7, col=1)
    fig.update_yaxes(title_text="Count", row=8, col=1)

    # Update x-axes labels
    fig.update_xaxes(title_text="Date", row=8, col=1)

    return fig


def create_timeline_gantt(design_data, commit_data, pr_data, cicd_data):
    """Create a Gantt chart showing the timeline of different phases"""
    # Collect all timeline data
    timeline_data = []

    # Add Design Phase
    if not design_data.empty:
        for _, row in design_data.iterrows():
            timeline_data.append(
                {
                    "Task": f"Design: {row['design_type']}",
                    "Start": row["start_time"],
                    "Finish": row["end_time"],
                    "Phase": "Design",
                    "Details": f"Authors: {row['authors']}\nStakeholders: {row['stakeholders']}",
                }
            )

    # Add Development Phases (based on commit activity)
    if not commit_data.empty:
        timeline_data.append(
            {
                "Task": "Development",
                "Start": commit_data["commit_date"].min(),
                "Finish": commit_data["commit_date"].max(),
                "Phase": "Development",
                "Details": f"Total Commits: {commit_data['commit_count'].sum()}",
            }
        )

    # Add PR Phase
    if not pr_data.empty:
        timeline_data.append(
            {
                "Task": "Code Reviews",
                "Start": pd.to_datetime(pr_data["pr_date"].min()),
                "Finish": pd.to_datetime(pr_data["pr_date"].max()),
                "Phase": "Code Review",
                "Details": f"Total PRs: {pr_data['pr_count'].sum()}",
            }
        )

    # Add CI/CD Phase
    if not cicd_data.empty:
        for env in cicd_data["environment"].unique():
            env_data = cicd_data[cicd_data["environment"] == env]
            timeline_data.append(
                {
                    "Task": f"CI/CD: {env}",
                    "Start": env_data["deployment_date"].min(),
                    "Finish": env_data["deployment_date"].max(),
                    "Phase": "CI/CD",
                    "Details": f"Environment: {env}\nEvents: {env_data['event_count'].sum()}",
                }
            )

    # Create DataFrame and handle empty case
    df = pd.DataFrame(timeline_data) if timeline_data else pd.DataFrame()

    if df.empty:
        return go.Figure()  # Return empty figure if no data

    # Create Gantt chart
    colors = {
        "Design": "#2E86C1",
        "Sprint": "#28B463",
        "Development": "#8E44AD",
        "Code Review": "#D35400",
        "CI/CD": "#1ABC9C",
    }

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Phase",
        color_discrete_map=colors,
        hover_data=["Details"],
    )

    # Update layout
    fig.update_layout(
        title="Project Timeline",
        height=400,
        xaxis=dict(
            title="Date",
            tickformat="%Y-%m-%d",
            tickangle=45,
        ),
        yaxis=dict(title="", categoryorder="total ascending"),
        showlegend=True,
        legend_title="Phase",
        hovermode="x unified",
    )

    return fig


def create_metrics_dashboard(commit_data):
    """Create a dashboard of key metrics"""
    # Initialize figures as None
    sprint_fig = None
    commit_fig = None

    # Handle commit data visualization
    if commit_data is not None and not commit_data.empty:
        commit_fig = px.bar(
            commit_data,
            x="commit_date",
            y="commit_count",
            title="Daily Commit Activity",
        )
        commit_fig.update_layout(height=300)

    return sprint_fig, commit_fig


def create_metric_card(title, value, help_text=None):
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
        unsafe_allow_html=True,
    )


def create_release_bug_chart(release_bug_data):
    """Create a visualization showing correlation between releases and subsequent bugs"""
    if release_bug_data.empty:
        return None

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add deployments as bars
    fig.add_trace(
        go.Bar(
            x=release_bug_data["deployment_complete_date"],
            y=release_bug_data["deployment_count"],
            name="Deployments",
            marker_color="rgba(55, 83, 109, 0.7)",
            hovertemplate="<b>%{x}</b><br>"
            + "Deployments: %{y}<br>"
            + "<extra></extra>",
        ),
        secondary_y=False,
    )

    # Add bugs as lines
    fig.add_trace(
        go.Scatter(
            x=release_bug_data["deployment_complete_date"],
            y=release_bug_data["bugs_count"],
            name="Total Bugs",
            line=dict(color="rgba(219, 64, 82, 0.7)"),
            hovertemplate="<b>%{x}</b><br>"
            + "Total Bugs: %{y}<br>"
            + "<extra></extra>",
        ),
        secondary_y=True,
    )

    # Add P0 bugs as a separate line
    fig.add_trace(
        go.Scatter(
            x=release_bug_data["deployment_complete_date"],
            y=release_bug_data["p0_bugs_count"],
            name="P0 Bugs",
            line=dict(color="rgba(255, 0, 0, 0.9)", dash="dot"),
            hovertemplate="<b>%{x}</b><br>" + "P0 Bugs: %{y}<br>" + "<extra></extra>",
        ),
        secondary_y=True,
    )

    # Update layout
    fig.update_layout(
        title="Release-Bug Correlation",
        hovermode="x unified",
        showlegend=True,
        height=400,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
        margin=dict(l=60, r=60, t=50, b=50),
    )

    # Update axes
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Number of Deployments", secondary_y=False)
    fig.update_yaxes(title_text="Number of Bugs", secondary_y=True)

    return fig


def display_design_phase_tab(design_data):
    """Display design phase timeline and metrics"""
    if design_data is None:
        design_data = pd.DataFrame()

    if not design_data.empty:
        st.markdown("### Design Phase Timeline")
        try:
            # Calculate durations for hover text
            design_data["duration_days"] = (
                design_data["end_time"] - design_data["start_time"]
            ).dt.days

            # Create timeline visualization
            design_fig = go.Figure()

            # Add bars for each design phase
            design_fig.add_trace(
                go.Bar(
                    base=design_data["start_time"],
                    x=design_data["duration_days"],
                    y=design_data["design_type"],
                    orientation="h",
                    text=design_data["duration_days"].apply(lambda x: f"{x} days"),
                    textposition="auto",
                    hovertemplate="""
                <b>%{y}</b><br>
                Duration: %{text}<br>
                Authors: %{customdata[0]}<br>
                Stakeholders: %{customdata[1]}<br>
                <extra></extra>
                """,
                    customdata=design_data[["authors", "stakeholders"]].values,
                    marker_color="rgb(55, 83, 109)",
                )
            )

            # Update layout
            design_fig.update_layout(
                title="Design Phase Duration",
                xaxis_title="Duration (Days)",
                yaxis_title="Design Phase",
                height=400,
                showlegend=False,
                barmode="relative",
                xaxis=dict(showgrid=True, gridwidth=1, gridcolor="LightGrey"),
                yaxis=dict(showgrid=True, gridwidth=1, gridcolor="LightGrey"),
                plot_bgcolor="white",
            )

            st.plotly_chart(design_fig, use_container_width=True)

            # Add summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                total_duration = design_data["duration_days"].sum()
                create_metric_card(
                    "Total Design Duration",
                    f"{total_duration} days",
                    help_text="Combined duration of all design phases",
                )
            with col2:
                total_authors = len(set(",".join(design_data["authors"]).split(", ")))
                create_metric_card(
                    "Total Contributors",
                    total_authors,
                    help_text="Unique authors across all design phases",
                )
            with col3:
                longest_phase = design_data.loc[design_data["duration_days"].idxmax()]
                create_metric_card(
                    "Longest Phase",
                    f"{longest_phase['design_type']} ({longest_phase['duration_days']} days)",
                    help_text="Design phase that took the most time",
                )
        except Exception as e:
            st.error(f"Error displaying design phase data: {str(e)}")
    else:
        st.info("No design phase data available")


def display_development_tab(commit_data):
    """Display development metrics and charts"""
    st.subheader("Development Activity")

    if commit_data is None or commit_data.empty:
        st.info("No development data available")
        return

    # Create and display commit activity chart
    _, commit_fig = create_metrics_dashboard(commit_data)
    if commit_fig:
        st.plotly_chart(commit_fig, use_container_width=True)

    try:
        col1, col2, col3 = st.columns(3)
        with col1:
            commits = (
                commit_data["commit_count"].sum()
                if "commit_count" in commit_data
                else 0
            )
            create_metric_card(
                "Total Commits",
                commits,
                help_text="Across all branches",
            )
        with col2:
            coverage = (
                commit_data["avg_coverage"].mean()
                if "avg_coverage" in commit_data
                else 0
            )
            create_metric_card(
                "Code Coverage",
                f"{coverage:.1f}%",
                help_text="Average across all commits",
            )
        with col3:
            lines_added = (
                commit_data["total_lines_added"].sum()
                if "total_lines_added" in commit_data
                else 0
            )
            lines_removed = (
                commit_data["total_lines_removed"].sum()
                if "total_lines_removed" in commit_data
                else 0
            )
            create_metric_card(
                "Code Changes",
                f"+{lines_added}/-{lines_removed}",
                help_text="Lines added/removed",
            )
    except Exception as e:
        st.error(f"Error calculating development metrics: {str(e)}")


def display_jira_metrics_tab(jira_data):
    """Display JIRA metrics"""
    if jira_data is None:
        jira_data = pd.DataFrame()

    if not jira_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            create_metric_card(
                "Average Resolution Time",
                f"{jira_data['resolution_time_hours'].mean():.1f}h",
                help_text="Average time to resolve JIRAs",
            )
        with col2:
            create_metric_card(
                "Average Build Time",
                f"{jira_data['build_time_hours'].mean():.1f}h",
                help_text="Average build time per JIRA",
            )
        with col3:
            create_metric_card(
                "Total Story Points",
                f"{jira_data['story_points'].sum()}",
                help_text="Total story points completed",
            )
    else:
        st.info("No JIRA data available")


def display_cicd_tab(cicd_data):
    """Display CI/CD metrics"""
    if cicd_data is None:
        cicd_data = pd.DataFrame()

    if not cicd_data.empty:
        col1, col2 = st.columns(2)
        with col1:
            success_rate = (
                len(cicd_data[cicd_data["status"] == "success"]) / len(cicd_data) * 100
            )
            create_metric_card(
                "Build Success Rate",
                f"{success_rate:.1f}%",
                help_text="Successful builds percentage",
            )
        with col2:
            create_metric_card(
                "Average Build Duration",
                f"{cicd_data['avg_duration'].mean():.0f}s",
                help_text="Average build time in seconds",
            )
    else:
        st.info("No CI/CD data available")


def display_quality_tab(bug_data, release_bug_data):
    """Display quality metrics and release-bug correlation"""
    if bug_data is None:
        bug_data = pd.DataFrame()

    if release_bug_data is None:
        release_bug_data = pd.DataFrame()

    # Display metrics
    if not bug_data.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            create_metric_card(
                "Total P0 Bugs",
                bug_data["bug_count"].sum(),
                help_text="High priority bugs",
            )
        with col2:
            avg_resolution = bug_data["avg_resolution_time"].mean()
            if pd.notna(avg_resolution):
                create_metric_card(
                    "Average Resolution Time",
                    f"{avg_resolution:.1f}h",
                    help_text="Average time to fix P0 bugs",
                )
        with col3:
            if not release_bug_data.empty:
                bug_per_release = (
                    release_bug_data["bugs_count"].sum()
                    / release_bug_data["deployment_count"].sum()
                )
                create_metric_card(
                    "Bugs per Release",
                    f"{bug_per_release:.2f}",
                    help_text="Average number of bugs per release",
                )

    # Display release-bug correlation chart
    if not release_bug_data.empty:
        st.markdown("### Release-Bug Correlation")
        fig = create_release_bug_chart(release_bug_data)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

            # Add insights
            st.markdown("#### Key Insights")
            total_releases = release_bug_data["deployment_count"].sum()
            total_bugs = release_bug_data["bugs_count"].sum()
            total_p0_bugs = release_bug_data["p0_bugs_count"].sum()

            st.markdown(
                f"""
            - Total number of releases: {total_releases}
            - Total bugs reported: {total_bugs}
            - Total P0 bugs: {total_p0_bugs}
            - Percentage of P0 bugs: {(total_p0_bugs / total_bugs * 100):.1f}%
            """
            )
    else:
        st.info("No quality data available")


def display_project_timeline_tab(design_data, commit_data, pr_data, cicd_data):
    """Display project timeline visualization"""
    st.subheader("Project Timeline")
    if all(data is not None for data in [design_data, commit_data, pr_data, cicd_data]):
        timeline_fig = create_timeline_gantt(
            design_data, commit_data, pr_data, cicd_data
        )
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("Insufficient data to display project timeline")


def main():
    st.title("Software Development Lifecycle Timeline")

    try:
        projects_df = get_project_list()

        if projects_df.empty:
            st.error(
                "Unable to fetch project list. Please check your database connection."
            )
            return

        project_options = ["None"] + projects_df["id"].tolist()

        selected_project = st.selectbox(
            "Select Project",
            options=project_options,
            format_func=lambda x: (
                x
                if x == "None"
                else f"{x} - {projects_df[projects_df['id'] == x]['title'].iloc[0]}"
            ),
        )

        if selected_project and selected_project != "None":
            project_info = projects_df[projects_df["id"] == selected_project].iloc[0]

            # Project Information Header
            st.markdown(
                f"""
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
                """,
                unsafe_allow_html=True,
            )

            # Fetch all data with proper error handling
            with st.spinner("Loading project data..."):
                try:
                    design_data = get_design_phase_data(selected_project)
                    commit_data = get_commit_data(selected_project)
                    pr_data = get_pr_data(selected_project)
                    cicd_data = get_cicd_data(selected_project)
                    bug_data = get_bug_data(selected_project)
                    jira_data = get_jira_metrics(selected_project)
                    release_bug_data = get_release_bug_correlation(selected_project)
                except Exception as e:
                    st.error(f"Error fetching data: {str(e)}")
                    return

            # Create tabs
            tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
                [
                    "Project Timeline",
                    "Design",
                    "Development",
                    "JIRA Metrics",
                    "CI/CD",
                    "Quality",
                ]
            )

            try:
                with tab1:
                    display_project_timeline_tab(
                        design_data, commit_data, pr_data, cicd_data
                    )

                with tab2:
                    display_design_phase_tab(design_data)

                with tab3:
                    display_development_tab(commit_data)

                with tab4:
                    display_jira_metrics_tab(jira_data)

                with tab5:
                    display_cicd_tab(cicd_data)

                with tab6:
                    display_quality_tab(bug_data, release_bug_data)

            except Exception as e:
                st.error(f"Error displaying data: {str(e)}")
                st.exception(e)

        else:
            st.info("Please select a project to view its timeline and metrics.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check your database connection and try again.")
