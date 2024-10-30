# load_events_db.py
from sqlalchemy import create_engine, text

from model.events_data_generator import get_sample_data, generate_pull_requests
from model.sdlc_events import JiraItem, Sprint, create_project, create_design_event, create_jira_item, create_commit, \
    create_cicd_event, create_bug, create_sprint, create_sprint_jira_associations, create_team_metrics, DatabaseManager, \
    db_name, server_connection_string, connection_string, create_pull_request, create_pr_comment

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
    """Load data into the database handling all relationships and dependencies"""
    try:
        # Get the sample data
        all_data = get_sample_data()

        # First load projects (no dependencies)
        print("Loading projects...")
        for project in all_data["projects"]:
            create_project(project)

        # Group Jira items by type for ordered loading
        print("Grouping Jira items by type...")
        design_jiras = []
        epics = []
        stories = []
        tasks = []

        for jira in all_data["jira_items"]:
            if jira["type"] == "Design":
                design_jiras.append(jira)
            elif jira["type"] == "Epic":
                epics.append(jira)
            elif jira["type"] == "Story":
                stories.append(jira)
            elif jira["type"] == "Task":
                tasks.append(jira)

        # Load Jiras in hierarchical order
        print("Loading design Jiras...")
        for jira in design_jiras:
            create_jira_item(jira)

        print("Loading epics...")
        for jira in epics:
            create_jira_item(jira)

        print("Loading stories...")
        for jira in stories:
            # Verify parent epic exists
            with db_manager.get_session() as session:
                epic_exists = (
                    session.query(JiraItem)
                    .filter(JiraItem.id == jira["parent_id"])
                    .first()
                    is not None
                )

                if not epic_exists:
                    print(
                        f"Warning: Parent epic {jira['parent_id']} not found for story {jira['id']}"
                    )
                    continue

            create_jira_item(jira)

        print("Loading tasks...")
        for jira in tasks:
            # Verify parent story exists
            with db_manager.get_session() as session:
                story_exists = (
                    session.query(JiraItem)
                    .filter(JiraItem.id == jira["parent_id"])
                    .first()
                    is not None
                )

                if not story_exists:
                    print(
                        f"Warning: Parent story {jira['parent_id']} not found for task {jira['id']}"
                    )
                    continue

            create_jira_item(jira)

        # Now load design events (depends on design Jiras)
        print("Loading design events...")
        for design_event in all_data["design_events"]:
            # Verify referenced Jira exists
            with db_manager.get_session() as session:
                jira_exists = (
                    session.query(JiraItem)
                    .filter(JiraItem.id == design_event["jira"])
                    .first()
                    is not None
                )

                if not jira_exists:
                    print(
                        f"Warning: Jira {design_event['jira']} not found for design event {design_event['id']}"
                    )
                    continue

            create_design_event(design_event)

        # Load sprints
        print("Loading sprints...")
        for sprint in all_data["sprints"]:
            create_sprint(sprint)

        # Create sprint-jira associations
        print("Creating sprint-jira associations...")
        for sprint_id, jira_ids in all_data["relationships"][
            "sprint_jira_associations"
        ].items():
            # Verify sprint exists
            with db_manager.get_session() as session:
                sprint_exists = (
                    session.query(Sprint).filter(Sprint.id == sprint_id).first()
                    is not None
                )

                if not sprint_exists:
                    print(f"Warning: Sprint {sprint_id} not found for associations")
                    continue

                # Verify all referenced Jiras exist
                valid_jira_ids = []
                for jira_id in jira_ids:
                    jira_exists = (
                        session.query(JiraItem).filter(JiraItem.id == jira_id).first()
                        is not None
                    )

                    if jira_exists:
                        valid_jira_ids.append(jira_id)
                    else:
                        print(
                            f"Warning: Jira {jira_id} not found for sprint {sprint_id}"
                        )

                if valid_jira_ids:
                    create_sprint_jira_associations(sprint_id, valid_jira_ids)

        # Load remaining entities that depend on Jiras
        print("Loading commits...")
        for commit in all_data["commits"]:
            # Verify Jira exists
            with db_manager.get_session() as session:
                jira_exists = (
                    session.query(JiraItem)
                    .filter(JiraItem.id == commit["jira_id"])
                    .first()
                    is not None
                )

                if not jira_exists:
                    print(
                        f"Warning: Jira {commit['jira_id']} not found for commit {commit['id']}"
                    )
                    continue

            create_commit(commit)

        # loading commit and comments
        print("Generating and loading pull requests and comments...")
        pull_requests, pr_comments = generate_pull_requests(all_data["projects"], all_data["commits"])
        for pr in pull_requests:
            create_pull_request(pr)
        for comment in pr_comments:
            create_pr_comment(comment)

        print("Loading CICD events...")
        for cicd_event in all_data["cicd_events"]:
            create_cicd_event(cicd_event)

        print("Loading bugs...")
        for bug in all_data["bugs"]:
            # Verify Jira and build exist
            with db_manager.get_session() as session:
                jira_exists = (
                    session.query(JiraItem)
                    .filter(JiraItem.id == bug["jira_id"])
                    .first()
                    is not None
                )

                if not jira_exists:
                    print(
                        f"Warning: Jira {bug['jira_id']} not found for bug {bug['id']}"
                    )
                    continue

            create_bug(bug)

        print("Loading team metrics...")
        for team_metric in all_data["team_metrics"]:
            create_team_metrics(team_metric)

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

