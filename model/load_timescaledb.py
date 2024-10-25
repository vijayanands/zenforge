# load_timescaledb.py
from sqlalchemy import create_engine, text

from model.events_crud import CRUDManager
from model.events_entity_generators import get_sample_data
from model.timescaledb_init import DatabaseManager

# Define your database connection details
db_name = "zenforge_sample_data"
user = "postgres"
password = "postgres"
host = "localhost"  # or your database host
port = "5432"  # default PostgreSQL port

# Create a connection string for the PostgreSQL server (not a specific database)
server_connection_string = f"postgresql://{user}:{password}@{host}:{port}/postgres"

# Create a connection string for the new database
connection_string = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

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

def load_data(db_manager):
    # Initialize the CRUD manager
    crud_manager = CRUDManager(db_manager)

    try:
        # Get the sample data
        all_data = get_sample_data()

        # First load projects (no dependencies)
        print("Loading projects...")
        for project in all_data["projects"]:
            crud_manager.create_project(project)

        # Then load Jira items (depends on projects)
        print("Loading Jira items...")
        for jira_item in all_data["jira_items"]:
            crud_manager.create_jira_item(jira_item)

        # Create a map of design event IDs to their corresponding Jira IDs
        design_jira_map = {}
        for jira in all_data["jira_items"]:
            if jira["type"] == "Design":  # Assuming design Jiras are marked with type "Design"
                design_jira_map[jira["id"].replace("-1", "")] = jira["id"]

        # Load design events with correct Jira references
        print("Loading design events...")
        for design_event in all_data["design_events"]:
            # Only set the jira field if we have a matching Jira item
            event_base_id = design_event["id"]
            if event_base_id in design_jira_map:
                design_event["jira"] = design_jira_map[event_base_id]
            else:
                design_event["jira"] = None  # Set to None if no matching Jira exists
            crud_manager.create_design_event(design_event)

        # Load remaining entities
        print("Loading commits...")
        for commit in all_data["commits"]:
            crud_manager.create_commit(commit)

        print("Loading CICD events...")
        for cicd_event in all_data["cicd_events"]:
            crud_manager.create_cicd_event(cicd_event)

        print("Loading bugs...")
        for bug in all_data["bugs"]:
            crud_manager.create_bug(bug)

        print("Loading sprints...")
        for sprint in all_data["sprints"]:
            crud_manager.create_sprint(sprint)

        print("Loading team metrics...")
        for team_metric in all_data["team_metrics"]:
            crud_manager.create_team_metrics(team_metric)

        print("Data loading completed successfully")

    except Exception as e:
        print(f"Error loading data: {e}")
        raise


def load_sample_data_into_timeseries_db():
    try:
        # Call the function to create the database if it does not exist
        create_database_if_not_exists()

        # Initialize the DatabaseManager using the new function
        db_manager = initialize_db_manager()

        # Load the data
        load_data(db_manager)
        print("Data has been loaded into the sdlc_timeseries schema.")

    except Exception as e:
        print(f"Failed to load sample data: {e}")
        raise

if __name__ == "__main__":
    load_sample_data_into_timeseries_db()
