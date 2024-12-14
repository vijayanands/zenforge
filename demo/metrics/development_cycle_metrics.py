import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from model.sdlc_events import Project, Environment
import psycopg2
import matplotlib.pyplot as plt
import os  # Make sure to import os at the top of your file
from dotenv import load_dotenv  # Import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Set DEBUG_MODE based on the environment variable
DEBUG_MODE = os.getenv("LOAD_SYNTHETIC_DATA", "false").lower() in [
    "true",
    "1",
    "yes",
    "t",
]

def get_database_connection():
    try:
        db_name = "zenforge_sample_data"
        user = "postgres"
        password = "postgres"
        host = "localhost"
        port = "5432"
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
        engine = create_engine(connection_string)
        return engine
    except SQLAlchemyError as e:
        st.error(f"Database connection failed: {str(e)}")
        return None

def get_projects():
    engine = get_database_connection()
    if engine is None:
        return pd.DataFrame()

    query = "SELECT id, title FROM sdlc_timeseries.projects;"
    try:
        projects_df = pd.read_sql_query(text(query), engine)
        return projects_df
    except SQLAlchemyError as e:
        st.error(f"Query execution failed: {str(e)}")
        return pd.DataFrame()



def get_production_builds(project_id, env: Environment):
    """Get production builds for the specified project_id"""
    query = """
        SELECT * FROM sdlc_timeseries.cicd_events
        WHERE project_id = :project_id
        AND environment::text = :env
        ORDER BY timestamp
    """

    connection = get_database_connection()
    if connection is None:
        return []

    try:
        with connection.connect() as conn:
            # Execute query with parameters, convert enum to string
            result = conn.execute(
                text(query),
                {
                    "project_id": project_id,
                    "env": env.value.upper()  # Convert to uppercase
                }
            )

            # convert result proxy to list of dictionaries
            releases = [dict(row._mapping) for row in result]
            return releases
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        raise e


def get_pull_requests(project_id):
    """Get pull requests for the specified project_id"""
    query = """
        SELECT * FROM sdlc_timeseries.pull_requests
        WHERE project_id = :project_id
        ORDER BY created_at;
    """

    connection = get_database_connection()
    if connection is None:
        return []

    try:
        with connection.connect() as conn:
            result = conn.execute(text(query), {"project_id": project_id})
            prs = [dict(row._mapping) for row in result]
            return prs
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        raise e

def get_coding_metrics(project_id):
    """Get code commits for the specified project_id"""
    query = """
        SELECT * FROM sdlc_timeseries.code_commits 
        WHERE event_id = :project_id
        ORDER BY timestamp;
    """

    connection = get_database_connection()
    if connection is None:
        return []

    try:
        with connection.connect() as conn:
            # Execute query with parameters
            result = conn.execute(text(query), {"project_id": project_id})

            # Convert result proxy to list of dictionaries
            commits = [dict(row._mapping) for row in result]
            return commits

    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        raise e

def get_data_for_display(project_id):
    commits = get_coding_metrics(project_id)
    prs = get_pull_requests(project_id)
    return commits, prs

def get_development_cycle_metrics(project_id):
    # get a list of code commits for the project

    engine = get_database_connection()
    if engine is None:
        return None

    # Query to get successful releases and associated metrics
    query = """
    WITH successful_releases AS (
        SELECT 
            release_version,
            MIN(timestamp) AS release_start,
            MAX(timestamp) AS release_end
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = :project_id
        AND status = 'success'
        AND LOWER(branch) = 'main'
        GROUP BY release_version
    ),
    jira_metrics AS (
        SELECT 
            j.id AS jira_id,
            j.created_date AS sprint_start,
            j.completed_date AS pr_opened,
            j.type AS jira_type
        FROM sdlc_timeseries.jira_items j
        JOIN successful_releases sr ON j.event_id = sr.release_version
    ),
    pr_metrics AS (
        SELECT 
            pr.id AS pr_id,
            pr.created_at AS pr_created,
            pr.merged_at AS pr_merged,
            pr.project_id
        FROM sdlc_timeseries.pull_requests pr
        JOIN successful_releases sr ON pr.project_id = sr.release_version
    ),
    build_metrics AS (
        SELECT 
            c.environment,
            c.timestamp AS build_time,
            c.status,
            c.release_version
        FROM sdlc_timeseries.cicd_events c
        JOIN successful_releases sr ON c.release_version = sr.release_version
        WHERE c.status = 'success'
    )
    SELECT 
        sr.release_version,
        MIN(j.sprint_start) AS development_time,
        MAX(pr.pr_merged) - MIN(pr.pr_created) AS pr_time,
        SUM(CASE WHEN bm.environment = 'dev' THEN bm.build_time END) AS dev_build_time,
        SUM(CASE WHEN bm.environment = 'qa' THEN bm.build_time END) AS qa_build_time,
        SUM(CASE WHEN bm.environment = 'staging' THEN bm.build_time END) AS staging_build_time,
        SUM(CASE WHEN bm.environment = 'production' THEN bm.build_time END) AS production_build_time
    FROM successful_releases sr
    LEFT JOIN jira_metrics j ON sr.release_version = j.jira_id
    LEFT JOIN pr_metrics pr ON sr.release_version = pr.project_id
    LEFT JOIN build_metrics bm ON sr.release_version = bm.release_version
    GROUP BY sr.release_version;
    """

    try:
        result = pd.read_sql_query(text(query), engine, params={"project_id": project_id})
        return result
    except SQLAlchemyError as e:
        st.error(f"Query execution failed: {str(e)}")
        return None

def get_releases_for_project(project_id):
    query = """
        SELECT *
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = :project_id
            AND environment::text = 'PRODUCTION'
            AND status::text = 'SUCCESS'
        ORDER BY timestamp DESC
    """
    
    connection = get_database_connection()
    if connection is None:
        return []

    try:
        with connection.connect() as conn:
            result = conn.execute(text(query), {"project_id": project_id})
            releases = [dict(row._mapping) for row in result]
            return releases
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return []


def get_commit_record(commit_id):
    """Get the commit record for the given commit hash"""
    query = """
        SELECT 
            commit_hash,
            commit_type,
            author,
            timestamp,
            files_changed,
            lines_added,
            lines_removed,
            code_coverage,
            lint_score,
            review_time_minutes,
            comments_count
        FROM sdlc_timeseries.code_commits
        WHERE id = :commit_id
        LIMIT 1;
    """

    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"commit_id": commit_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return None


def display_commit_metrics(project_id, release_version):
    """Display commit metrics for the selected release"""
    st.subheader("Commit Analysis")
    pr_metrics = get_pr_metrics_for_display(project_id, release_version)
    commit_ids = set(pr['commit_id'] for pr in pr_metrics)
    commit_records = [get_commit_record(commit_id) for commit_id in commit_ids if get_commit_record(commit_id)]
    if commit_records:
        st.dataframe(pd.DataFrame(commit_records))


def get_cicd_record(release_version):
    """Get the cicd record for the given release version"""
    query = """
        SELECT 
            event_id
        FROM sdlc_timeseries.cicd_events
        WHERE release_version = :release_version
        LIMIT 1;
    """
    result = db.execute(query, release_version=release_version)
    return result.fetchone()

def get_pr_record(pr_id):
    """Get the pull request record for the given pull request id"""
    query = """
        SELECT 
            title,
            description,
            created_at,
            merged_at,
            author,
            commit_id
        FROM sdlc_timeseries.pull_requests
        WHERE id = :pr_id
        LIMIT 1;
    """

    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"pr_id": pr_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return None

def get_pr_metrics_for_display(project_id, release_version):
    builds = get_builds_for_release(project_id, release_version)
    prs = get_prs_that_triggered(builds)
    return prs

def get_prs_that_triggered(builds):
    """Get the pull requests that triggered the builds"""
    pr_metrics = []
    for build in builds:
        pr_record = get_pr_record(build['event_id'])
        if pr_record:
            pr_duration = (pr_record['merged_at'] - pr_record['created_at']).total_seconds()
            pr_metrics.append({
                'pr_id': build['event_id'],
                'environment': build['environment'],
                'build_time': build['duration_seconds'],
                'title': pr_record['title'],
                'author': pr_record['author'],
                'created_at': pr_record['created_at'],
                'merged_at': pr_record['merged_at'],
                'commit_id': pr_record['commit_id'],
                'pr_duration': pr_duration
            })
    return pr_metrics

def get_builds_for_release(project_id, release_version):
    """Get the cicd records for the given project and release version"""
    query = """
        SELECT 
            event_id,
            environment,
            status,
            duration_seconds,
            build_id
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = :project_id
        AND release_version = :release_version;
    """
    
    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"project_id": project_id, "release_version": release_version}
            )
            return [dict(row._mapping) for row in result]
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return []



def display_pr_metrics(project_id, release_version):
    """Display PR metrics for the selected release"""
    st.subheader("Pull Request Analysis")

    pr_metrics = get_pr_metrics_for_display(project_id, release_version)
    if not pr_metrics:
        st.info("No pull requests found for builds in this release")
        return
    prs_df = pd.DataFrame(pr_metrics)
    # Convert 'pr_duration' from seconds to hours, minutes, and seconds
    prs_df['pr_duration'] = prs_df['pr_duration'].apply(lambda x: f"{x//3600}h {x%3600//60}m {x%60}s")
    # Selecting specific columns to display including the formatted 'pr_duration'
    selected_columns = ['pr_id', 'environment', 'title', 'author', 'pr_duration', 'created_at', 'merged_at', 'commit_id']
    st.dataframe(prs_df[selected_columns])



def get_builds_for_pr(pr_id):
    """Get all builds associated with a PR across environments"""
    query = """
        SELECT *
        FROM sdlc_timeseries.cicd_events
        WHERE event_id = :pr_id
        ORDER BY timestamp;
    """
    
    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"pr_id": pr_id})
            return [dict(row._mapping) for row in result]
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return []

def display_build_timeline(pr_id):
    """Display build durations across environments for a specific PR"""
    st.subheader("Build Timeline")
    
    # Get builds for this PR
    builds = get_builds_for_pr(pr_id)
    
    if not builds:
        st.warning("No build data found for this PR.")
        return

    # Create a dictionary of environment durations
    env_durations = {}
    for build in builds:
        env = build['environment']
        duration = build['duration_seconds']
        env_durations[env] = duration

    # Environment sequence
    envs = ['DEV', 'QA', 'STAGING', 'PRODUCTION']
    durations = [env_durations.get(env, 0) for env in envs]

    # Set colors for the bars - using a professional color scheme
    colors = ['#2196F3', '#4CAF50', '#FFC107', '#F44336']  # Blue, Green, Amber, Red

    # Create figure with specific dimensions
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.bar(envs, durations, color=colors)
    
    # Customize the chart
    ax.set_title('Build Duration by Environment', pad=20)
    ax.set_xlabel('Environment')
    ax.set_ylabel('Duration (seconds)')
    
    # Add value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        if height > 0:  # Only show label if there's a duration
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{int(height)}s',
                ha='center',
                va='bottom'
            )

    # Customize grid and spines
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Adjust layout and display
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)

    # Show detailed build information
    if builds:
        st.subheader("Build Details")
        builds_df = pd.DataFrame(builds)
        builds_df['timestamp'] = pd.to_datetime(builds_df['timestamp'])
        builds_df = builds_df.sort_values('timestamp')
        
        # Format the dataframe for display with more columns
        display_df = builds_df[[
            'environment', 
            'status', 
            'build_id',
            'duration_seconds',
            'branch',
            'mode',
            'release_version',
            'timestamp'
        ]]
        
        # Rename columns for better display
        display_df.columns = [
            'Environment',
            'Status',
            'Build ID',
            'Duration (s)',
            'Branch',
            'Mode',
            'Release Version',
            'Timestamp'
        ]
        
        # Add duration in minutes for better readability
        display_df['Duration (min)'] = display_df['Duration (s)'].apply(
            lambda x: f"{x/60:.1f}"
        )
        
        # Reorder columns to put timestamp at the end
        final_columns = [
            'Environment',
            'Status',
            'Build ID',
            'Duration (s)',
            'Duration (min)',
            'Branch',
            'Mode',
            'Release Version',
            'Timestamp'
        ]
        
        st.dataframe(display_df[final_columns])

def get_env_durations(project_id, release_version):
    """Get build durations for each environment in a release"""
    query = """
        SELECT 
            environment::text as env,
            SUM(duration_seconds) as total_duration
        FROM sdlc_timeseries.cicd_events
        WHERE project_id = :project_id
        AND release_version = :release_version
        GROUP BY environment
        ORDER BY environment;
    """

    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(query),
                {"project_id": project_id, "release_version": release_version}
            )
            durations = {row.env: row.total_duration for row in result}
            # Debugging: Log the retrieved durations only if DEBUG_MODE is set
            if DEBUG_MODE:
                st.write("Retrieved durations:", durations)
            return durations
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return None

def get_pr_details(pr_id):
    """Get detailed information for a specific PR"""
    query = """
        SELECT 
            pr.id as pr_id,
            pr.title,
            pr.description,
            pr.author,
            pr.status,
            pr.created_at,
            pr.merged_at,
            pr.branch_from,
            pr.branch_to,
            pr.commit_id,
            EXTRACT(EPOCH FROM (pr.merged_at - pr.created_at)) as duration_seconds
        FROM sdlc_timeseries.pull_requests pr
        WHERE pr.id = :pr_id;
    """
    
    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"pr_id": pr_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return None

def display_pr_metrics(pr_id):
    """Display PR metrics for the selected PR"""
    st.subheader("Pull Request Details")
    
    # Get PR details
    pr_details = get_pr_details(pr_id)
    
    if not pr_details:
        st.warning("No pull request found with this ID.")
        return
        
    # Create two columns for PR information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Basic Information")
        st.markdown(f"**PR ID:** {pr_details['pr_id']}")
        st.markdown(f"**Title:** {pr_details['title']}")
        st.markdown(f"**Author:** {pr_details['author']}")
        st.markdown(f"**Status:** {pr_details['status']}")
        
        # Calculate duration in a readable format
        if pr_details['duration_seconds'] and pr_details['duration_seconds'] > 0:
            duration_hours = pr_details['duration_seconds'] / 3600
            duration_str = f"{duration_hours:.1f} hours"
            st.markdown(f"**Duration:** {duration_str}")
            
    with col2:
        st.markdown("#### Branch Information")
        st.markdown(f"**From Branch:** {pr_details['branch_from']}")
        st.markdown(f"**To Branch:** {pr_details['branch_to']}")
        st.markdown(f"**Commit ID:** {pr_details['commit_id']}")
        
    # Show timestamps in their own section
    st.markdown("#### Timeline")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Created:** {pr_details['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
    with col2:
        if pr_details['merged_at']:
            st.markdown(f"**Merged:** {pr_details['merged_at'].strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.markdown("**Merged:** Not merged yet")
            
    # Show PR description if available
    if pr_details['description']:
        st.markdown("#### Description")
        st.markdown(pr_details['description'])
        
    # Add a divider
    st.markdown("---")
    
    # Get and display associated commits
    commits_query = """
        SELECT 
            cc.commit_hash,
            cc.author,
            cc.timestamp,
            cc.files_changed,
            cc.lines_added,
            cc.lines_removed,
            cc.code_coverage,
            cc.lint_score,
            cc.review_time_minutes,
            cc.comments_count
        FROM sdlc_timeseries.code_commits cc
        WHERE cc.commit_hash = :commit_id
        ORDER BY cc.timestamp DESC;
    """
    
    try:
        with get_database_connection().connect() as conn:
            commits = pd.read_sql(
                text(commits_query), 
                conn, 
                params={"commit_id": pr_details['commit_id']}
            )
            
            if not commits.empty:
                st.markdown("#### Associated Commits")
                st.dataframe(
                    commits[[
                        'commit_hash', 'author', 'timestamp', 
                        'files_changed', 'lines_added', 'lines_removed'
                    ]],
                    hide_index=True
                )
    except Exception as e:
        st.error(f"Failed to fetch commit information: {str(e)}")

def get_commit_details_for_pr(pr_id):
    """Get commit details associated with a PR"""
    query = """
        WITH pr_commit AS (
            SELECT commit_id 
            FROM sdlc_timeseries.pull_requests 
            WHERE id = :pr_id
        )
        SELECT 
            cc.commit_hash,
            cc.author,
            cc.timestamp,
            cc.commit_type,
            cc.files_changed,
            cc.lines_added,
            cc.lines_removed,
            cc.code_coverage,
            cc.lint_score,
            cc.review_time_minutes,
            cc.comments_count
        FROM sdlc_timeseries.code_commits cc
        JOIN pr_commit pc ON cc.commit_hash = pc.commit_id
        ORDER BY cc.timestamp DESC;
    """
    
    engine = get_database_connection()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query), {"pr_id": pr_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None
    except Exception as e:
        st.error(f"Query execution failed: {str(e)}")
        return None

def display_commit_metrics(pr_id):
    """Display commit metrics for the selected PR"""
    st.subheader("Commit Analysis")
    
    # Get commit details
    commit = get_commit_details_for_pr(pr_id)
    
    if not commit:
        st.warning("No commit found for this PR.")
        return
        
    # Create columns for commit information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Commit Information")
        st.markdown(f"**Hash:** `{commit['commit_hash']}`")
        st.markdown(f"**Author:** {commit['author']}")
        st.markdown(f"**Timestamp:** {commit['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**Type:** {commit['commit_type']}")
        
    with col2:
        st.markdown("#### Code Metrics")
        st.markdown(f"**Files Changed:** {commit['files_changed']}")
        st.markdown(f"**Lines Added:** {commit['lines_added']}")
        st.markdown(f"**Lines Removed:** {commit['lines_removed']}")
        
        # Calculate net change
        net_change = commit['lines_added'] - commit['lines_removed']
        net_change_str = f"+{net_change}" if net_change > 0 else str(net_change)
        st.markdown(f"**Net Change:** {net_change_str} lines")
    
    # Create a second row of columns for quality metrics
    st.markdown("#### Quality Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if commit['code_coverage'] is not None:
            st.metric("Code Coverage", f"{commit['code_coverage']:.1f}%")
    
    with col2:
        if commit['lint_score'] is not None:
            st.metric("Lint Score", f"{commit['lint_score']:.1f}")
    
    with col3:
        if commit['review_time_minutes'] is not None:
            hours = commit['review_time_minutes'] // 60
            minutes = commit['review_time_minutes'] % 60
            st.metric("Review Time", f"{hours}h {minutes}m")
    
    # Show comments count if available
    if commit['comments_count'] and commit['comments_count'] > 0:
        st.markdown(f"**Comments:** {commit['comments_count']}")

def display_development_cycle_metrics():
    st.title("Development Cycle Metrics")

    # Initialize session states
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 0

    # Move project selector to main window
    projects_df = get_projects()

    if projects_df.empty:
        st.error("No projects found in the database.")
        return

    # Step 1: Project Selection
    project_options = projects_df.set_index('id')['title'].to_dict()
    project_id = st.selectbox(
        "Select Project",
        options=[""] + list(project_options.keys()),
        format_func=lambda x: "Select a project..." if x == "" else project_options[x]
    )

    if not project_id:
        st.info("Please select a project to continue.")
        return

    # Step 2: Release Selection
    releases = get_releases_for_project(project_id)
    if not releases:
        st.warning("No releases found for this project.")
        return

    release_options = {
        r['release_version']: (
            f"Release {r['release_version']} "
        ) for r in releases
    }

    selected_release = st.selectbox(
        "Select Release",
        options=[""] + list(release_options.keys()),
        format_func=lambda x: "Select a release..." if x == "" else release_options[x],
        key="release_selector"
    )

    # Reset tab when release changes
    if selected_release != st.session_state.get('last_release'):
        st.session_state.active_tab = 0
        st.session_state.last_release = selected_release
        st.rerun()

    if not selected_release:
        st.info("Please select a release to view metrics.")
        return

    # Check if selected release is tag-based
    if selected_release:
        # Find the release record for the selected release version
        release_records = [r for r in releases if r['release_version'] == selected_release]
        if not release_records:
            st.warning("No release records found.")
            return
            
        # Get the first record for this release
        release_record = release_records[0]

        pr_id = release_record['event_id']
        
        if release_record['tag'] is not None:
            # For tag-based releases, only show build timeline
            st.info("This is a tag-based release. Only build timeline is available.")
            display_build_timeline(pr_id)
        else:
            # For PR-based releases, show all tabs
            tab1, tab2, tab3 = st.tabs(["Build Timeline", "Pull Requests", "Commits"])
            # Display content in respective tabs
            with tab1:
                display_build_timeline(pr_id)
            with tab2:
                display_pr_metrics(pr_id)
            with tab3:
                display_commit_metrics(pr_id)            



if __name__ == "__main__":
    display_development_cycle_metrics()