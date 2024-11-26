import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

from model.sdlc_events import BuildStatus, Environment


def safe_dataframe_check(df):
    """Safely check if a dataframe is empty or None"""
    return df is not None and not df.empty


def show_debug_info(data, title):
    """Helper function to conditionally show debug information"""
    if st.session_state.get("show_debug", False):
        st.write(f"Debug: {title}", data)


def get_database_connection():
    try:
        db_name = "zenforge_sample_data"
        user = "postgres"
        password = "postgres"
        host = "localhost"
        port = "5432"
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        engine = create_engine(connection_string)
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


def get_project_list():
    """Get list of all projects"""
    engine = get_database_connection()
    query = """
    SELECT id, title, start_date, status 
    FROM sdlc_timeseries.projects
    ORDER BY start_date DESC
    """
    return safe_read_sql(query, engine)


def get_release_list(project_id):
    """Get list of successful releases on main branch"""
    engine = get_database_connection()

    # First debug query to show all CICD events for the project
    raw_data_query = """
    SELECT 
        project_id,
        environment::text,
        branch,
        status::text,
        mode::text,
        release_version,
        timestamp,
        COUNT(*) as event_count
    FROM sdlc_timeseries.cicd_events
    WHERE project_id = %(project_id)s
    GROUP BY 
        project_id,
        environment::text,
        branch,
        status::text,
        mode::text,
        release_version,
        timestamp
    ORDER BY timestamp;
    """

    raw_data = safe_read_sql(raw_data_query, engine, params={"project_id": project_id})
    show_debug_info(raw_data, "Raw CICD Events")

    query = """
    WITH environment_matrix AS (
        SELECT 
            release_version,
            COUNT(DISTINCT CASE 
                WHEN LOWER(environment::text) = 'dev' 
                AND LOWER(status::text) = 'success' 
                THEN 1 END) as has_dev,
            COUNT(DISTINCT CASE 
                WHEN LOWER(environment::text) = 'qa' 
                AND LOWER(status::text) = 'success' 
                THEN 1 END) as has_qa,
            COUNT(DISTINCT CASE 
                WHEN LOWER(environment::text) = 'staging' 
                AND LOWER(status::text) = 'success' 
                THEN 1 END) as has_staging,
            COUNT(DISTINCT CASE 
                WHEN LOWER(environment::text) = 'production' 
                AND LOWER(status::text) = 'success' 
                THEN 1 END) as has_prod,
            MIN(timestamp) as release_start,
            MAX(timestamp) as release_end
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = %(project_id)s
        AND LOWER(branch) = 'main'
        AND LOWER(mode::text) = 'automatic'
        GROUP BY release_version
    )
    SELECT 
        release_version,
        release_start,
        release_end,
        (has_dev + has_qa + has_staging + has_prod) as successful_envs
    FROM environment_matrix
    WHERE 
        has_dev = 1 
        AND has_qa = 1 
        AND has_staging = 1 
        AND has_prod = 1
    ORDER BY release_start DESC;
    """

    releases = safe_read_sql(query, engine, params={"project_id": project_id})

    if releases.empty:
        if st.session_state.get("show_debug", False):
            st.warning(
                f"Debug: No complete release chains found for project {project_id}"
            )
    else:
        show_debug_info(releases, "Found Release Chains")

    return releases


def get_release_timeline_data(project_id, release_version):
    """Get timeline data for a specific release"""
    engine = get_database_connection()

    # Debug query to see what we're looking for
    debug_query = """
    SELECT 
        environment::text,
        status::text,
        mode::text,
        timestamp,
        build_id,
        branch
    FROM sdlc_timeseries.cicd_events
    WHERE project_id = %(project_id)s
    AND release_version = %(release_version)s
    ORDER BY timestamp;
    """

    debug_data = safe_read_sql(
        debug_query,
        engine,
        params={"project_id": project_id, "release_version": release_version},
    )

    show_debug_info(debug_data, "Release Events")

    # Get CICD events
    cicd_query = """
    WITH release_window AS (
        SELECT 
            release_version,
            MIN(timestamp) as release_start,
            MAX(timestamp) as release_end
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = %(project_id)s
        AND release_version = %(release_version)s
        GROUP BY release_version
    )
    SELECT 
        c.*
    FROM sdlc_timeseries.cicd_events c
    JOIN release_window rw ON 
        c.release_version = rw.release_version
    WHERE c.project_id = %(project_id)s
    AND c.release_version = %(release_version)s
    ORDER BY c.timestamp;
    """

    # Get associated commits
    commit_query = """
    WITH release_window AS (
        SELECT 
            release_version,
            MIN(timestamp) as release_start,
            MAX(timestamp) as release_end
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = %(project_id)s
        AND release_version = %(release_version)s
        GROUP BY release_version
    )
    SELECT DISTINCT
        cc.*
    FROM sdlc_timeseries.code_commits cc
    JOIN release_window rw ON 
        cc.timestamp BETWEEN rw.release_start AND rw.release_end
    WHERE cc.event_id = %(project_id)s
    AND LOWER(cc.branch) = 'main'
    ORDER BY cc.timestamp;
    """

    # Get associated PRs
    pr_query = """
    WITH release_window AS (
        SELECT 
            release_version,
            MIN(timestamp) as release_start,
            MAX(timestamp) as release_end
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = %(project_id)s
        AND release_version = %(release_version)s
        GROUP BY release_version
    )
    SELECT DISTINCT
        pr.*
    FROM sdlc_timeseries.pull_requests pr
    JOIN release_window rw ON 
        pr.created_at BETWEEN rw.release_start AND rw.release_end
    WHERE pr.project_id = %(project_id)s
    AND LOWER(pr.branch_to) = 'main'
    ORDER BY pr.created_at;
    """

    params = {"project_id": project_id, "release_version": release_version}

    return {
        "cicd_events": safe_read_sql(cicd_query, engine, params=params),
        "commits": safe_read_sql(commit_query, engine, params=params),
        "pull_requests": safe_read_sql(pr_query, engine, params=params),
    }


def display_release_timeline(project_id, releases_df, selected_release):
    """Display timeline for selected release"""
    # First show the raw CICD events for the selected release
    engine = get_database_connection()
    debug_query = """
    SELECT 
        environment::text,
        status::text,
        mode::text,
        timestamp,
        build_id,
        branch
    FROM sdlc_timeseries.cicd_events
    WHERE project_id = %(project_id)s
    AND release_version = %(release_version)s
    ORDER BY timestamp;
    """

    debug_data = safe_read_sql(
        debug_query,
        engine,
        params={"project_id": project_id, "release_version": selected_release},
    )

    show_debug_info(debug_data, "Selected Release Events")

    timeline_data = get_release_timeline_data(project_id, selected_release)

    if all(df.empty for df in timeline_data.values()):
        st.warning("No timeline data available for this release")
        return

    # Create Gantt chart for release timeline
    fig = go.Figure()

    # Add environment bands
    environments = ["DEV", "QA", "STAGING", "PRODUCTION"]
    env_colors = {
        "DEV": "rgba(144, 238, 144, 0.2)",
        "QA": "rgba(135, 206, 235, 0.2)",
        "STAGING": "rgba(255, 182, 193, 0.2)",
        "PRODUCTION": "rgba(255, 215, 0, 0.2)",
    }

    # Get overall timeline range
    all_dates = []
    for df in timeline_data.values():
        if not df.empty:
            date_cols = [
                col
                for col in df.columns
                if "date" in col.lower() or "time" in col.lower()
            ]
            for col in date_cols:
                all_dates.extend(df[col].dropna().tolist())

    if not all_dates:
        st.warning("No date information available for timeline")
        return

    timeline_start = min(all_dates)
    timeline_end = max(all_dates)

    # Add environment background colors
    for env in environments:
        fig.add_hrect(
            y0=env,
            y1=env,
            x0=timeline_start,
            x1=timeline_end,
            fillcolor=env_colors[env],
            line_width=0,
            layer="below",
        )

    # Add CICD events
    if not timeline_data["cicd_events"].empty:
        show_debug_info(
            timeline_data["cicd_events"][["environment", "status", "timestamp"]].head(),
            "Processing CICD Events",
        )

        for env in environments:
            env_events = timeline_data["cicd_events"][
                timeline_data["cicd_events"]["environment"].str.upper() == env
            ]

            show_debug_info(len(env_events), f"{env} Events Count")

            # Add successful builds
            success_events = env_events[env_events["status"].str.upper() == "SUCCESS"]
            if not success_events.empty:
                fig.add_trace(
                    go.Scatter(
                        x=success_events["timestamp"],
                        y=[env] * len(success_events),
                        mode="markers",
                        marker=dict(symbol="circle", size=12, color="green"),
                        name=f"{env} Success",
                        hovertemplate="Environment: %{y}<br>Time: %{x}<br>Status: Success<br>Build ID: %{customdata}",
                        customdata=success_events["build_id"],
                    )
                )

            # Add failed builds
            failed_events = env_events[env_events["status"].str.upper() == "FAILURE"]
            if not failed_events.empty:
                fig.add_trace(
                    go.Scatter(
                        x=failed_events["timestamp"],
                        y=[env] * len(failed_events),
                        mode="markers",
                        marker=dict(symbol="x", size=12, color="red"),
                        name=f"{env} Failure",
                        hovertemplate="Environment: %{y}<br>Time: %{x}<br>Status: Failure<br>Build ID: %{customdata}",
                        customdata=failed_events["build_id"],
                    )
                )

    # Add PR merges
    if not timeline_data["pull_requests"].empty:
        show_debug_info(
            timeline_data["pull_requests"][["created_at", "status", "title"]].head(),
            "Processing PRs",
        )
        merged_prs = timeline_data["pull_requests"][
            timeline_data["pull_requests"]["status"].str.upper() == "MERGED"
        ]
        if not merged_prs.empty:
            fig.add_trace(
                go.Scatter(
                    x=merged_prs["merged_at"],
                    y=["PR_MERGE"] * len(merged_prs),
                    mode="markers",
                    marker=dict(symbol="triangle-up", size=12, color="purple"),
                    name="PR Merges",
                    hovertemplate="PR Merged: %{x}<br>Title: %{text}",
                    text=merged_prs["title"],
                )
            )

    # Add commits
    if not timeline_data["commits"].empty:
        show_debug_info(
            timeline_data["commits"][["timestamp", "commit_hash", "author"]].head(),
            "Processing Commits",
        )
        fig.add_trace(
            go.Scatter(
                x=timeline_data["commits"]["timestamp"],
                y=["COMMITS"] * len(timeline_data["commits"]),
                mode="markers",
                marker=dict(symbol="circle", size=8, color="blue"),
                name="Commits",
                hovertemplate="Commit: %{x}<br>Hash: %{customdata[0]}<br>Author: %{customdata[1]}",
                customdata=timeline_data["commits"][["commit_hash", "author"]].values,
            )
        )

    # Update layout
    fig.update_layout(
        title=f"Release Timeline - {selected_release}",
        height=600,
        showlegend=True,
        hovermode="closest",
        xaxis=dict(title="Timeline", showgrid=True, gridwidth=1, gridcolor="LightGrey"),
        yaxis=dict(
            title="",
            showgrid=False,
            categoryarray=["COMMITS", "PR_MERGE"] + environments,
            categoryorder="array",
        ),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Display release metrics
    with st.expander("Release Metrics"):
        col1, col2 = st.columns(2)

        with col1:
            create_metric_card(
                "Release Duration",
                f"{(timeline_end - timeline_start).total_seconds() / 3600:.1f} hours",
                "Total time from first commit to production deployment",
            )

        with col2:
            success_count = (
                len(
                    timeline_data["cicd_events"][
                        timeline_data["cicd_events"]["status"].str.upper() == "SUCCESS"
                    ]
                )
                if not timeline_data["cicd_events"].empty
                else 0
            )
            total_builds = (
                len(timeline_data["cicd_events"])
                if not timeline_data["cicd_events"].empty
                else 0
            )
            success_rate = (
                (success_count / total_builds * 100) if total_builds > 0 else 0
            )
            create_metric_card(
                "Build Success Rate",
                f"{success_rate:.1f}%",
                f"Successful: {success_count} / Total: {total_builds}",
            )


def main():
    st.title("Software Development Lifecycle Timeline")

    # Add debug toggle in sidebar when SDLC Timeline is selected
    with st.sidebar:
        st.radio(
            "Debug Mode",
            options=["OFF", "ON"],
            key="debug_mode",
            index=0,
            on_change=lambda: st.session_state.update(
                show_debug=(st.session_state.debug_mode == "ON")
            ),
        )
        st.markdown("---")  # Add a separator

    try:
        projects_df = get_project_list()

        if projects_df.empty:
            st.error(
                "Unable to fetch project list. Please check your database connection."
            )
            return

        # Debug: Show available projects and their status
        show_debug_info(projects_df, "Available Projects")

        # Project selection
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
            # Get releases for selected project
            releases_df = get_release_list(selected_project)

            if releases_df.empty:
                st.info(f"No releases found for project {selected_project}")
                # Debug: Show project status
                if st.session_state.get("show_debug", False):
                    project_status = projects_df[projects_df["id"] == selected_project][
                        "status"
                    ].iloc[0]
                    st.write(f"Debug: Project Status - {project_status}")
                return

            # Release selection
            selected_release = st.selectbox(
                "Select Release",
                options=releases_df["release_version"].tolist(),
                format_func=lambda x: (
                    f"Release {x} ({releases_df[releases_df['release_version'] == x]['release_start'].iloc[0].strftime('%Y-%m-%d')})"
                ),
            )

            # Display release timeline
            if selected_release:
                display_release_timeline(
                    selected_project, releases_df, selected_release
                )

        else:
            st.info("Please select a project to view its timeline and metrics.")

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        if st.session_state.get("show_debug", False):
            st.exception(e)


if __name__ == "__main__":
    main()
