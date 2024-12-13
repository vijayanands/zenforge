from typing import Any, Dict

from sqlalchemy import create_engine, text

from model.events_data_generator import generate_all_data, generate_cicd_events
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
    User,
    Team,
    Designation,
    UserMapping,
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


def create_user(user_data: Dict[str, Any]) -> None:
    """Create a user record"""
    try:
        with DatabaseManager(connection_string).get_session() as session:
            # Convert designation from Enum to value
            if isinstance(user_data["designation"], Designation):
                user_data = user_data.copy()
                user_data["designation"] = user_data["designation"].value
                
            user = User(**user_data)
            session.add(user)
            session.commit()
            print(f"Created user: {user_data['name']} ({user_data['email']})")
    except Exception as e:
        print(f"Error creating user {user_data.get('email')}: {e}")
        raise

def create_team(team_data: Dict[str, Any]) -> None:
    """Create a team record"""
    try:
        with DatabaseManager(connection_string).get_session() as session:
            team = Team(**team_data)
            session.add(team)
            session.commit()
            print(f"Created team: {team_data['name']}")
    except Exception as e:
        print(f"Error creating team {team_data.get('name')}: {e}")
        raise

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

        print("Phase 9: Loading users...")
        for user in all_data["users"]:
            create_user(user)

        print("Phase 10: Loading teams...")
        for team in all_data["teams"]:
            create_team(team)

    except Exception as e:
        print(f"Error loading data: {e}")
        raise


def verify_data_loaded():
    """Verify that data was properly loaded into the database"""
    with DatabaseManager(connection_string).get_session() as session:
        # Check users
        user_count = session.query(User).count()
        print(f"\nVerification Results:")
        print(f"Users in database: {user_count}")
        
        # Check teams
        team_count = session.query(Team).count()
        print(f"Teams in database: {team_count}")
        
        # Check user mappings table
        mapping_count = session.query(UserMapping).count()
        print(f"User mappings in database: {mapping_count}")
        
        if user_count == 0:
            print("Warning: No users found in database!")
        if team_count == 0:
            print("Warning: No teams found in database!")
            
        # Sample user data
        sample_user = session.query(User).first()
        if sample_user:
            print(f"\nSample user data:")
            print(f"Name: {sample_user.name}")
            print(f"Email: {sample_user.email}")
            print(f"Designation: {sample_user.designation}")
            print(f"Supervisor: {sample_user.supervisor}")

def load_sample_data_into_timeseries_db():
    """Load sample data into the timeseries database"""
    try:
        print("\nCreate Database and Initialize DB...")
        create_database_if_not_exists()

        db_manager = DatabaseManager(connection_string)
        print("\nDropping existing tables...")
        db_manager.drop_all_tables()
        
        print("\nInitializing database...")
        db_manager.init_db()  # This will now create the user_mappings table along with other tables

        print("\nGenerating synthetic data...")
        all_data = generate_all_data()

        print("\nLoad synthetic data to Timeseries DB...")
        load_data(all_data)
        
        print("\nVerifying data loaded...")
        verify_data_loaded()
        
        print("\nBootstrapping Complete.")

    except Exception as e:
        print(f"Failed to load sample data: {e}")
        raise
