import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError
import sys
import os
# Add the parent directory of the current file to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.timescaledb_init import DatabaseManager
from events_crud import CRUDManager
from events_entity_generators import get_sample_data

# Define your database connection details
db_name = 'zenforge_sample_data'
user = 'postgres'
password = 'postgres'
host = 'localhost'  # or your database host
port = '5432'  # default PostgreSQL port

# Create a connection string for the PostgreSQL server (not a specific database)
server_connection_string = f'postgresql://{user}:{password}@{host}:{port}/postgres'

# Create an engine for the server connection
engine = create_engine(server_connection_string)

def create_database_if_not_exists(engine, db_name):
    # Connect to the server and check if the database exists
    with engine.connect() as connection:
        connection.execute(text("commit"))  # Commit any existing transaction
        result = connection.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}';"))
        db_exists = result.scalar() is not None

    if not db_exists:
        # Connect to the server and create the database
        with engine.connect() as connection:
            connection.execute(text("commit"))  # Commit any existing transaction
            connection.execute(text(f'CREATE DATABASE {db_name}'))
            print(f"Database {db_name} created successfully")

# Call the function to create the database if it does not exist
create_database_if_not_exists(engine, db_name)

# Create a connection string for the new database
connection_string = f'postgresql://{user}:{password}@{host}:{port}/{db_name}'

# Create the DatabaseManager instance and initialize the database
db_manager = DatabaseManager(connection_string)
try:
    db_manager.init_db()
    print("Schemas created successfully.")
except Exception as e:
    print(f"Error creating schemas: {e}")

def load_data(db_manager):
    # Initialize the CRUD manager
    crud_manager = CRUDManager(db_manager)

    # Get the sample data
    all_data = get_sample_data()

    # Load projects
    for project in all_data['projects']:
        crud_manager.create_project(project)

    # Load design events
    for design_event in all_data['design_events']:
        crud_manager.create_design_event(design_event)

    # Load Jira items
    for jira_item in all_data['jira_items']:
        crud_manager.create_jira_item(jira_item)

    # Load code commits
    for commit in all_data['commits']:
        crud_manager.create_commit(commit)

    # Load CI/CD events
    for cicd_event in all_data['cicd_events']:
        crud_manager.create_cicd_event(cicd_event)

    # Load bugs
    for bug in all_data['bugs']:
        crud_manager.create_bug(bug)

    # Load sprints
    for sprint in all_data['sprints']:
        crud_manager.create_sprint(sprint)

    # Load team metrics
    for team_metric in all_data['team_metrics']:
        crud_manager.create_team_metrics(team_metric)

if __name__ == "__main__":
    # Call the function to create the database if it does not exist
    create_database_if_not_exists(engine, db_name)

    # Create a connection string for the new database
    connection_string = f'postgresql://{user}:{password}@{host}:{port}/{db_name}'

    # Create the DatabaseManager instance and initialize the database
    db_manager = DatabaseManager(connection_string)
    try:
        db_manager.init_db()
        print("Schemas created successfully.")
    except Exception as e:
        print(f"Error creating schemas: {e}")

    load_data(db_manager)
    print("Data has been loaded into the sdlc_timeseries schema.")
