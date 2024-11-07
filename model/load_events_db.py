# load_events_db.py
from typing import Any, Dict, List

from sqlalchemy import create_engine, text

from model.events_data_generator import generate_cicd_events, get_sample_data
from model.sdlc_events import (
    BuildMode,
    DatabaseManager,
    PRStatus,
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
    db_manager,
    db_name,
    server_connection_string,
)
from model.validators import (
    validate_bug_build_association,
    validate_bug_data,
    validate_cicd_event_timeline,
    validate_cicd_relationships,
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


def load_cicd_events(all_data) -> None:
    """Load CICD events into the database"""
    print("\nGenerating CICD events...")

    # Extract project IDs from the projects data
    project_ids = [project["id"] for project in all_data["projects"]]
    pull_requests = all_data["pull_requests"]

    cicd_events = generate_cicd_events(pull_requests, project_ids)

    print(f"Generated {len(cicd_events)} CICD events")
    print(
        f"- Automatic builds: {sum(1 for e in cicd_events if e['mode'] == BuildMode.AUTOMATIC.value)}"
    )
    print(
        f"- Manual builds: {sum(1 for e in cicd_events if e['mode'] == BuildMode.MANUAL.value)}"
    )

    # Validate CICD events before loading
    with db_manager.get_session() as session:
        # Validate timeline constraints
        timeline_errors = validate_cicd_event_timeline(session)
        if timeline_errors:
            print("CICD timeline validation errors:")
            for error in timeline_errors:
                print(f"  - {error}")
            raise ValueError("CICD timeline validation failed")

        # Validate relationships
        relationship_errors = validate_cicd_relationships(
            {
                "cicd_events": cicd_events,
                "pull_requests": pull_requests,
                "projects": all_data["projects"],
            }
        )
        if relationship_errors:
            print("CICD relationship validation errors:")
            for error in relationship_errors:
                print(f"  - {error}")
            raise ValueError("CICD relationship validation failed")

    # Create events in the database if validation passes
    for event in cicd_events:
        create_cicd_event(event)


def load_bugs(all_data):
    bugs = all_data["bugs"]
    # Validate bugs before loading
    validation_errors = []
    for bug in bugs:
        errors = validate_bug_data(bug)
        validation_errors.extend(errors)
    build_association_errors = validate_bug_build_association(
        bugs, all_data["cicd_events"]
    )
    validation_errors.extend(build_association_errors)
    if validation_errors:
        raise ValueError(f"Bug validation failed:\n" + "\n".join(validation_errors))
    # Load validated bugs
    for bug in bugs:
        create_bug(bug)
    print(f"Generated and loaded {len(bugs)} P0 bugs")


def load_pull_requests(all_data):
    pr_count = 0
    merged_count = 0
    for pr in all_data["pull_requests"]:
        create_pull_request(pr)
        pr_count += 1
        if (
            isinstance(pr["status"], str)
            and pr["status"] == "MERGED"
            or isinstance(pr["status"], PRStatus)
            and pr["status"] == PRStatus.MERGED
        ):
            merged_count += 1
    print(f"Loaded {pr_count} pull requests ({merged_count} merged)")


def load_project_data(all_data):
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
            "priority": project.get("priority"),
        }
        create_project(db_project)
    print(f"Stored {len(base_project_data)} projects with completion states")


def load_data(all_data: Dict[str, Any]):
    """Load data into the database handling all relationships and dependencies"""
    try:
        # Store original project data for reference
        print("\nPhase 1: Loading base entities...")
        load_project_data(all_data)

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

        for sprint_id, jira_ids in all_data["relationships"][
            "sprint_jira_associations"
        ].items():
            create_sprint_jira_associations(sprint_id, jira_ids)

        print("\nPhase 5: Loading commits...")
        for commit in all_data["commits"]:
            create_commit(commit)

        print("\nPhase 6: Loading pull requests...")
        load_pull_requests(all_data)

        print("\nPhase 7: Loading CICD events...")
        load_cicd_events(all_data)

        print("\nPhase 8: Generating and loading P0 bugs...")
        load_bugs(all_data)

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
        load_data(sample_data)
        print("Data has been loaded into the sdlc_timeseries schema.")

    except Exception as e:
        print(f"Failed to load sample data: {e}")
        raise
