import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from model.sdlc_events import Project, Environment
import psycopg2

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
    """Get list of releases for the project with at least two events"""
    query = """
        WITH release_counts AS (
            SELECT 
                release_version,
                MIN(timestamp) as first_seen,
                COUNT(*) as total_events,
                COUNT(DISTINCT build_id) as distinct_builds
            FROM sdlc_timeseries.cicd_events
            WHERE project_id = :project_id
            AND release_version IS NOT NULL
            GROUP BY release_version
            HAVING COUNT(DISTINCT build_id) >= 2  -- Only releases with at least 2 distinct builds
        )
        SELECT 
            release_version,
            first_seen,
            total_events,
            distinct_builds
        FROM release_counts
        ORDER BY first_seen DESC;
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

def display_development_cycle_metrics(project_id, releases, commits, prs):
    st.title("Development Cycle Metrics")
    
    # Get list of releases and create selector
    release_list = get_releases_for_project(project_id)
    
    if not release_list:
        st.warning("No releases found for this project.")
        return
        
    # Create release selector
    release_options = {r['release_version']: f"Release {r['release_version']} ({r['first_seen'].strftime('%Y-%m-%d')})" 
                      for r in release_list}
    selected_release = st.selectbox(
        "Select Release",
        options=list(release_options.keys()),
        format_func=lambda x: release_options[x]
    )
    
    if selected_release:
        # Filter data for selected release
        release_commits = [c for c in commits if any(
            r['release_version'] == selected_release for r in releases
            if r['timestamp'] >= c['timestamp']
        )]
        
        release_prs = [pr for pr in prs if any(
            r['release_version'] == selected_release for r in releases
            if r['timestamp'] >= pr['created_at']
        )]
        
        release_builds = [r for r in releases if r['release_version'] == selected_release]
        
        # Display metrics for selected release
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Development Time",
                f"{len(release_commits)} commits",
                help="Number of commits in this release"
            )
            
        with col2:
            if release_prs:
                avg_pr_time = sum(
                    (pr['merged_at'] - pr['created_at']).total_seconds() / 3600 
                    for pr in release_prs 
                    if pr['merged_at'] is not None
                ) / len(release_prs)
                st.metric(
                    "PR Review Time",
                    f"{avg_pr_time:.1f} hours",
                    help="Average time from PR creation to merge"
                )
            
        with col3:
            if release_builds:
                build_time = sum(
                    build['duration_seconds'] for build in release_builds
                ) / 3600
                st.metric(
                    "Total Build Time",
                    f"{build_time:.1f} hours",
                    help="Total time spent in builds"
                )
        
        # Display detailed metrics
        tabs = st.tabs(["Commits", "Pull Requests", "Builds"])
        
        with tabs[0]:
            if release_commits:
                commits_df = pd.DataFrame(release_commits)
                st.dataframe(
                    commits_df[[
                        'timestamp', 'author', 'commit_hash', 
                        'files_changed', 'lines_added', 'lines_removed'
                    ]]
                )
            else:
                st.info("No commits found for this release")
                
        with tabs[1]:
            if release_prs:
                prs_df = pd.DataFrame(release_prs)
                st.dataframe(
                    prs_df[[
                        'created_at', 'merged_at', 'author', 
                        'title', 'status'
                    ]]
                )
            else:
                st.info("No pull requests found for this release")
                
        with tabs[2]:
            if release_builds:
                builds_df = pd.DataFrame(release_builds)
                st.dataframe(
                    builds_df[[
                        'timestamp', 'environment', 'status',
                        'duration_seconds', 'build_id'
                    ]]
                )
            else:
                st.info("No builds found for this release")

def main():
    st.title("Development Cycle Metrics")
    
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
            f"({r['first_seen'].strftime('%Y-%m-%d')}) "
            f"- {r['total_events']} events"
        ) for r in releases
    }
    
    selected_release = st.selectbox(
        "Select Release",
        options=[""] + list(release_options.keys()),
        format_func=lambda x: "Select a release..." if x == "" else release_options[x]
    )
    
    if not selected_release:
        st.info("Please select a release to view metrics.")
        return

    # Step 3: Display Metrics
    commits, prs = get_data_for_display(project_id)
    
    # Create tabs for different metric views
    tabs = st.tabs(["Overview", "Commits", "Pull Requests", "Build Timeline"])
    
    with tabs[0]:
        display_release_overview(project_id, selected_release, commits, prs)
    
    with tabs[1]:
        display_commit_metrics(commits, selected_release)
    
    with tabs[2]:
        display_pr_metrics(prs, selected_release)
    
    with tabs[3]:
        display_build_timeline(project_id, selected_release)

def display_release_overview(project_id, release_version, commits, prs):
    """Display overview metrics for the selected release"""
    st.subheader("Release Overview")
    # Implementation to follow...

def display_commit_metrics(commits, release_version):
    """Display commit metrics for the selected release"""
    st.subheader("Commit Analysis")
    # Implementation to follow...

def display_pr_metrics(prs, release_version):
    """Display PR metrics for the selected release"""
    st.subheader("Pull Request Analysis")
    # Implementation to follow...

def display_build_timeline(project_id, release_version):
    """Display build timeline for the selected release"""
    st.subheader("Build Timeline")
    # Implementation to follow...

if __name__ == "__main__":
    main() 