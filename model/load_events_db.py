# load_events_db.py
import json
import random
from typing import Dict, Any, List

from sqlalchemy import create_engine, text

from model.events_data_generator import generate_pull_requests, get_sample_data, generate_cicd_events, adjust_cicd_dates
from model.sdlc_events import (
    DatabaseManager,
    JiraItem,
    Sprint,
    connection_string,
    create_bug,
    create_cicd_event,
    create_commit,
    create_design_event,
    create_jira_item,
    create_pr_comment,
    create_project,
    create_pull_request,
    create_sprint,
    create_sprint_jira_associations,
    create_team_metrics,
    db_name,
    server_connection_string, PullRequest, PRStatus, CICDEvent, verify_pr_exists,
)

# Create an engine for the server connection
engine = create_engine(server_connection_string)


def create_database_if_not_exists():
    # Connect to the server and check if the database exists
    with engine.connect() as connection:
        connection.execute(text("commit"))  # Commit any existing transaction
        result = connection.execute(
            text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}';")
        )
        db_exists = result.scalar() is not None

    if not db_exists:
        # Connect to the server and create the database
        with engine.connect() as connection:
            connection.execute(text("commit"))  # Commit any existing transaction
            connection.execute(text(f"CREATE DATABASE {db_name}"))
            print(f"Database {db_name} created successfully")


def initialize_db_manager():
    # Create the DatabaseManager instance and initialize the database
    db_manager = DatabaseManager(connection_string)
    try:
        db_manager.init_db()
        print("Schemas created successfully.")
    except Exception as e:
        print(f"Error creating schemas: {e}")
    return db_manager


def load_cicd_events(db_manager, cicd_events: List[Dict[str, Any]]) -> int:
    """
    Load CICD events with proper PR verification and error handling.

    Args:
        db_manager: Database manager instance
        cicd_events: List of CICD event dictionaries

    Returns:
        int: Number of successfully loaded events
    """
    success_count = 0

    with db_manager.get_session() as session:
        for event in cicd_events:
            try:
                # Verify PR exists if PR reference is provided
                if event.get('pr_id') and event.get('pr_created_at'):
                    pr_exists = verify_pr_exists(
                        session,
                        event['pr_id'],
                        event['pr_created_at']
                    )
                    if not pr_exists:
                        print(
                            f"Warning: Removing PR reference for CICD event {event['id']} - PR {event['pr_id']} not found")
                        event['pr_id'] = None
                        event['pr_created_at'] = None

                # Create CICD event
                create_cicd_event(event)
                success_count += 1

                if success_count % 100 == 0:
                    print(f"Loaded {success_count} CICD events...")

            except Exception as e:
                print(f"Error loading CICD event {event.get('id')}: {str(e)}")
                continue

    return success_count


def load_data(db_manager, all_data: Dict[str, Any]):
    """Load data into the database handling all relationships and dependencies"""
    try:
        # Store original project data for reference
        print("\nPhase 1: Loading base entities...")
        print("Loading projects...")
        base_project_data = {}
        for project in all_data["projects"]:
            # Store the full project data including completion_state
            base_project_data[project["id"]] = project.copy()

            # Create project record with database fields only
            db_project = {
                "id": project["id"],
                "title": project["title"],
                "description": project["description"],
                "start_date": project["start_date"],
                "status": project["status"],
                "complexity": project["complexity"],
                "team_size": project["team_size"],
                "estimated_duration_weeks": project.get("estimated_duration_weeks"),
                "budget_allocated": project.get("budget_allocated"),
                "priority": project.get("priority")
            }
            create_project(db_project)

        print(f"Stored {len(base_project_data)} projects with completion states")

        # Group Jira items by type for ordered loading
        print("\nPhase 2: Loading Jira hierarchy...")
        jira_types = ["Design", "Epic", "Story", "Task"]
        for jira_type in jira_types:
            print(f"Loading {jira_type} items...")
            type_jiras = [j for j in all_data["jira_items"] if j["type"] == jira_type]
            for jira in type_jiras:
                create_jira_item(jira)

        print("\nPhase 3: Loading design events...")
        for design_event in all_data["design_events"]:
            create_design_event(design_event)

        print("\nPhase 4: Loading sprints and associations...")
        for sprint in all_data["sprints"]:
            create_sprint(sprint)

        for sprint_id, jira_ids in all_data["relationships"]["sprint_jira_associations"].items():
            create_sprint_jira_associations(sprint_id, jira_ids)

        print("\nPhase 5: Loading commits...")
        for commit in all_data["commits"]:
            create_commit(commit)

        print("\nPhase 6: Loading pull requests...")
        pr_count = 0
        merged_count = 0
        for pr in all_data["pull_requests"]:
            create_pull_request(pr)
            pr_count += 1
            if isinstance(pr["status"], str) and pr["status"] == "MERGED" or \
                    isinstance(pr["status"], PRStatus) and pr["status"] == PRStatus.MERGED:
                merged_count += 1
        print(f"Loaded {pr_count} pull requests ({merged_count} merged)")

        print("Loading PR comments...")
        comment_count = 0
        for comment in all_data["pr_comments"]:
            create_pr_comment(comment)
            comment_count += 1
        print(f"Loaded {comment_count} PR comments")

        print("\nPhase 7: Loading CICD events...")
        with db_manager.get_session() as session:
            # Get actual PR data for CICD event generation
            print("Retrieving merged PRs from database...")
            merged_prs = session.query(PullRequest).filter(
                PullRequest.status == PRStatus.MERGED,
                PullRequest.merged_at.isnot(None)
            ).all()

            print(f"Found {len(merged_prs)} merged PRs in database")

            # Convert PR objects to dictionaries for CICD generation
            pr_dicts = [{
                "id": pr.id,
                "created_at": pr.created_at,
                "merged_at": pr.merged_at,
                "project_id": pr.project_id,
                "branch_to": pr.branch_to,
                "status": pr.status
            } for pr in merged_prs]

            print("Generating CICD events...")
            cicd_events = generate_cicd_events(base_project_data, pr_dicts)
            print(f"Generated {len(cicd_events)} CICD events")

            print("Loading CICD events...")
            success_count = load_cicd_events(db_manager, cicd_events)
            print(f"Successfully loaded {success_count} CICD events")

            # Verify final count
            actual_count = session.query(CICDEvent).count()
            print(f"Actual CICD events in database: {actual_count}")

        print("\nPhase 8: Loading remaining entities...")
        print("Loading bugs...")
        # Get actual CICD builds from database for bug associations
        with db_manager.get_session() as session:
            available_builds = session.query(CICDEvent.build_id, CICDEvent.event_id).all()

            if available_builds:
                print(f"Found {len(available_builds)} CICD builds in database")

                # Create lookup of build IDs by project
                project_builds = {}
                for build_id, event_id in available_builds:
                    if event_id not in project_builds:
                        project_builds[event_id] = []
                    project_builds[event_id].append(build_id)

                print("Loading bugs with valid build references...")
                bug_count = 0
                for bug in all_data["bugs"]:
                    project_id = bug["event_id"]
                    if project_id in project_builds and project_builds[project_id]:
                        # Assign a valid build ID from the project's builds
                        modified_bug = bug.copy()
                        modified_bug["build_id"] = random.choice(project_builds[project_id])

                        # Verify Jira exists
                        jira_exists = session.query(JiraItem).filter(
                            JiraItem.id == modified_bug["jira_id"]
                        ).first() is not None

                        if jira_exists:
                            create_bug(modified_bug)
                            bug_count += 1
                            if bug_count % 10 == 0:
                                print(f"Loaded {bug_count} bugs...")
                        else:
                            print(f"Skipping bug {modified_bug['id']} - Jira {modified_bug['jira_id']} not found")
                    else:
                        print(f"Skipping bug for project {project_id} - no builds available")

                print(f"Successfully loaded {bug_count} bugs")
            else:
                print("No CICD builds found in database. Skipping bug loading.")

        print("Loading team metrics...")
        for metric in all_data["team_metrics"]:
            create_team_metrics(metric)

        print("\nData loading completed successfully")

    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def load_sample_data_into_timeseries_db():
    """Load sample data into the timeseries database"""
    try:
        # Create database if it doesn't exist
        create_database_if_not_exists()

        # Initialize the DatabaseManager
        db_manager = initialize_db_manager()

        # Get sample data once
        print("Getting sample data...")
        sample_data = get_sample_data()

        # Load the data
        load_data(db_manager, sample_data)
        print("Data has been loaded into the sdlc_timeseries schema.")

    except Exception as e:
        print(f"Failed to load sample data: {e}")
        raise
