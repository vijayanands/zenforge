from typing import Any, Dict

from sqlalchemy import create_engine, text

from model.events_data_generator import generate_cicd_events, generate_all_data
from model.sdlc_events import (
    BuildMode,
    DatabaseManager,
    connection_string,
    create_bug,
    create_cicd_event,
    create_commit,
    create_design_event,
    create_jira_item,
    create_project,
    create_pull_request,
    create_sprint,
    create_sprint_jira_associations,
    db_name,
    server_connection_string,
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


def initialize_db():
    # Create the DatabaseManager instance and initialize the database
    db_manager = DatabaseManager(connection_string)
    try:
        db_manager.init_db()
        print("Schemas created successfully.")
    except Exception as e:
        print(f"Error creating schemas: {e}")


def load_cicd_events(all_data) -> None:
    cicd_events = all_data["cicd_events"]
    for event in cicd_events:
        create_cicd_event(event)


def load_bugs(all_data):
    bugs = all_data["bugs"]
    for bug in bugs:
        create_bug(bug)


def load_pull_requests(all_data):
    for pr in all_data["pull_requests"]:
        create_pull_request(pr)


def load_project_data(all_data):
    base_project_data = {}
    for project in all_data["projects"]:
        base_project_data[project["id"]] = project.copy()

        # Create project record with database fields only
        db_project = {
            "id": project["id"],
            "title": project["title"],
            "description": project["description"],
            "start_date": project["start_date"],
            "status": project["status"],
            "complexity": project["complexity"],
            "estimated_duration_weeks": project.get("estimated_duration_weeks"),
            "priority": project.get("priority"),
        }
        create_project(db_project)


def load_data(all_data: Dict[str, Any]):
    """Load data into the database handling all relationships and dependencies"""
    try:
        # Store original project data for reference
        print("Phase 1: Loading projects...")
        load_project_data(all_data)

        # Group Jira items by type for ordered loading
        print("Phase 2: Loading Jiras...")
        for jira in all_data["jira_items"]:
            create_jira_item(jira)

        print("Phase 3: Loading design events...")
        for design_event in all_data["design_events"]:
            create_design_event(design_event)

        print("Phase 4: Loading sprints and associations...")
        for sprint in all_data["sprints"]:
            create_sprint(sprint)
        for sprint_id, jira_ids in all_data["relationships"][
            "sprint_jira_associations"
        ].items():
            create_sprint_jira_associations(sprint_id, jira_ids)

        print("Phase 5: Loading commits...")
        for commit in all_data["commits"]:
            create_commit(commit)

        print("Phase 6: Loading pull requests...")
        load_pull_requests(all_data)

        print("Phase 7: Loading CICD events...")
        load_cicd_events(all_data)

        print("Phase 8: Loading Bugs...")
        load_bugs(all_data)

    except Exception as e:
        print(f"Error loading data: {e}")
        raise


def load_sample_data_into_timeseries_db():
    """Load sample data into the timeseries database"""
    try:
        print("\nCreate Database and Initialize DB...")
        # Create database if it doesn't exist
        create_database_if_not_exists()

        # Initialize the Database
        initialize_db()

        # Get sample data once
        print("\nGenerating synthetic data...")
        all_data = generate_all_data()

        # Load the data
        print("\nLoad synthetic data to Timeseries DB...")
        load_data(all_data)
        print("\nBootstapping Complete.")

    except Exception as e:
        print(f"Failed to load sample data: {e}")
        raise
