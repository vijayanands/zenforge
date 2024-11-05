import enum
import json
from datetime import datetime
from operator import and_
from typing import Any, Dict, List, Optional

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    UniqueConstraint,
    and_,
    create_engine,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Junction tables
Base = declarative_base()

sprint_jira_association = Table(
    "sprint_jira_association",
    Base.metadata,
    Column("sprint_id", String, ForeignKey("sdlc_timeseries.sprints.id")),
    Column("jira_id", String, ForeignKey("sdlc_timeseries.jira_items.id")),
    schema="sdlc_timeseries",
)


class StageType(enum.Enum):
    START = "start"
    END = "end"
    BLOCKED = "blocked"
    RESUME = "resume"


# Regular tables
class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    start_date = Column(DateTime, nullable=False)
    status = Column(String)
    complexity = Column(String)
    team_size = Column(Integer)
    estimated_duration_weeks = Column(Integer)
    budget_allocated = Column(Float)
    priority = Column(String)
    total_commits = Column(Integer)
    avg_code_coverage = Column(Float)
    total_p0_bugs = Column(Integer)


class JiraItem(Base):
    __tablename__ = "jira_items"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    parent_id = Column(String, nullable=True)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    status = Column(String)
    created_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime)
    priority = Column(String)
    story_points = Column(Integer)
    assigned_team = Column(String)
    assigned_developer = Column(String)
    estimated_hours = Column(Integer)
    actual_hours = Column(Integer)

    sprints = relationship(
        "Sprint", secondary=sprint_jira_association, back_populates="jira_items"
    )


class Sprint(Base):
    __tablename__ = "sprints"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    planned_story_points = Column(Integer)
    completed_story_points = Column(Integer)
    planned_stories = Column(Integer)
    completed_stories = Column(Integer)
    team_velocity = Column(Float)
    burndown_efficiency = Column(Float)
    sprint_goals = Column(Text)
    retrospective_summary = Column(Text)
    blockers_encountered = Column(Integer)
    team_satisfaction_score = Column(Float)
    status = Column(String)

    jira_items = relationship(
        "JiraItem", secondary=sprint_jira_association, back_populates="sprints"
    )


class CodeCommit(Base):
    __tablename__ = "code_commits"
    __table_args__ = (
        UniqueConstraint("id", "timestamp"),
        {"schema": "sdlc_timeseries"},
    )

    id = Column(String)
    timestamp = Column(DateTime, nullable=False)
    __mapper_args__ = {"primary_key": [id, timestamp]}

    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    repository = Column(String)
    branch = Column(String)
    author = Column(String)
    commit_hash = Column(String)
    files_changed = Column(Integer)
    lines_added = Column(Integer)
    lines_removed = Column(Integer)
    code_coverage = Column(Float)
    lint_score = Column(Float)
    commit_type = Column(String)
    review_time_minutes = Column(Integer)
    comments_count = Column(Integer)
    approved_by = Column(String)
    jira_id = Column(
        String, ForeignKey("sdlc_timeseries.jira_items.id"), nullable=False
    )

class CICDEvent(Base):
    __tablename__ = "cicd_events"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    pr_id = Column(String)
    pr_created_at = Column(DateTime)
    timestamp = Column(DateTime, nullable=False)
    environment = Column(String)
    event_type = Column(String)
    build_id = Column(String, nullable=False, unique=True)
    status = Column(String)
    duration_seconds = Column(Integer)
    metrics = Column(JSONB)
    reason = Column(String, nullable=False)
    branch = Column(String, nullable=False)
    tag = Column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['pr_id', 'pr_created_at'],
            ['sdlc_timeseries.pull_requests.id', 'sdlc_timeseries.pull_requests.created_at']
        ),
        {"schema": "sdlc_timeseries"}
    )


class Bug(Base):
    __tablename__ = "bugs"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    bug_type = Column(String)
    impact_area = Column(String)
    severity = Column(String)
    title = Column(String)
    status = Column(String)
    created_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime)
    resolution_time_hours = Column(Integer)
    assigned_to = Column(String)
    environment_found = Column(String)
    number_of_customers_affected = Column(Integer)
    root_cause = Column(String)
    fix_version = Column(String)
    regression_test_status = Column(String)
    customer_communication_needed = Column(Boolean)
    postmortem_link = Column(String)
    jira_id = Column(
        String, ForeignKey("sdlc_timeseries.jira_items.id"), nullable=False
    )
    build_id = Column(
        String, ForeignKey("sdlc_timeseries.cicd_events.build_id"), nullable=False
    )


class DesignEvent(Base):
    __tablename__ = "design_events"
    __table_args__ = (
        PrimaryKeyConstraint("id", "timestamp"),
        {"schema": "sdlc_timeseries"},
    )

    id = Column(String)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    timestamp = Column(DateTime, nullable=False)
    design_type = Column(String, nullable=False)
    stage = Column(Enum(StageType), nullable=False)
    author = Column(String)
    jira = Column(String, ForeignKey("sdlc_timeseries.jira_items.id"), nullable=True)
    stakeholders = Column(String)
    review_status = Column(String)


class TeamMetrics(Base):
    __tablename__ = "team_metrics"
    __table_args__ = (
        PrimaryKeyConstraint("id", "week_starting"),
        {"schema": "sdlc_timeseries"},
    )

    id = Column(String)
    event_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    week_starting = Column(DateTime, nullable=False)
    team_size = Column(Integer)
    velocity = Column(Float)
    code_review_turnaround_hours = Column(Float)
    build_success_rate = Column(Float)
    test_coverage = Column(Float)
    bugs_reported = Column(Integer)
    bugs_fixed = Column(Integer)
    technical_debt_hours = Column(Integer)
    pair_programming_hours = Column(Integer)
    code_review_comments = Column(Integer)
    documentation_updates = Column(Integer)
    knowledge_sharing_sessions = Column(Integer)
    team_satisfaction = Column(Float)
    sprint_completion_rate = Column(Float)


"""
Project Related CRUD
"""


def create_project(project_data: Dict[str, Any]) -> Project:
    with db_manager.get_session() as session:
        project = Project(**project_data)
        session.add(project)
        session.commit()
        return project


def get_project(project_id: str) -> Optional[Project]:
    with db_manager.get_session() as session:
        return session.query(Project).filter(Project.id == project_id).first()


def update_project(project_id: str, update_data: Dict[str, Any]) -> bool:
    with db_manager.get_session() as session:
        result = (
            session.query(Project).filter(Project.id == project_id).update(update_data)
        )
        session.commit()
        return result > 0


def delete_project(project_id: str) -> bool:
    with db_manager.get_session() as session:
        result = session.query(Project).filter(Project.id == project_id).delete()
        session.commit()
        return result > 0


"""
Design Related CRUD
"""


def create_design_event(event_data: Dict[str, Any]) -> DesignEvent:
    if "stage" in event_data:
        event_data["stage"] = StageType(event_data["stage"])
    with db_manager.get_session() as session:
        event = DesignEvent(**event_data)
        session.add(event)
        session.commit()
        return event


def get_design_events(
    event_id: str, design_type: Optional[str] = None
) -> List[DesignEvent]:
    with db_manager.get_session() as session:
        query = session.query(DesignEvent).filter(DesignEvent.event_id == event_id)
        if design_type:
            query = query.filter(DesignEvent.design_type == design_type)
        return query.order_by(DesignEvent.timestamp).all()


"""
JIRA Related CRUD
"""


def create_jira_item(jira_data: Dict[str, Any]) -> JiraItem:
    with db_manager.get_session() as session:
        jira = JiraItem(**jira_data)
        session.add(jira)
        session.commit()
        return jira


def get_jira_items(event_id: str, item_type: Optional[str] = None) -> List[JiraItem]:
    with db_manager.get_session() as session:
        query = session.query(JiraItem).filter(JiraItem.event_id == event_id)
        if item_type:
            query = query.filter(JiraItem.type == item_type)
        return query.order_by(JiraItem.created_date).all()


def update_jira_status(
    jira_id: str, new_status: str, completion_date: Optional[datetime] = None
) -> bool:
    with db_manager.get_session() as session:
        update_data = {"status": new_status}
        if completion_date:
            update_data["completed_date"] = completion_date
        result = (
            session.query(JiraItem).filter(JiraItem.id == jira_id).update(update_data)
        )
        session.commit()
        return result > 0


"""
Commit Related CRUD
"""


def create_commit(commit_data: Dict[str, Any]) -> CodeCommit:
    with db_manager.get_session() as session:
        try:
            commit = CodeCommit(**commit_data)
            session.add(commit)
            session.commit()
            return commit
        except Exception as e:
            session.rollback()
            print(f"Error creating commit: {e}")
            raise


def get_commits(
    event_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[CodeCommit]:
    with db_manager.get_session() as session:
        query = session.query(CodeCommit).filter(CodeCommit.event_id == event_id)
        if start_date:
            query = query.filter(CodeCommit.timestamp >= start_date)
        if end_date:
            query = query.filter(CodeCommit.timestamp <= end_date)
        return query.order_by(CodeCommit.timestamp).all()


"""
CI/CD Related CRUD
"""


def create_cicd_event(event_data: Dict[str, Any]) -> CICDEvent:
    """Create a CICD event with better error handling and logging"""
    with db_manager.get_session() as session:
        try:
            # Convert numpy string to regular string if needed
            if hasattr(event_data.get('status'), 'item'):
                event_data['status'] = event_data['status'].item()
            if hasattr(event_data.get('branch'), 'item'):
                event_data['branch'] = event_data['branch'].item()

            # Convert metrics to JSON string if it isn't already
            if isinstance(event_data.get('metrics'), dict):
                event_data['metrics'] = json.dumps(event_data['metrics'])

            # Create the event
            event = CICDEvent(**event_data)
            session.add(event)
            session.commit()
            print(f"Successfully created CICD event {event.id}")
            return event
        except Exception as e:
            session.rollback()
            print(f"Error creating CICD event {event_data.get('id')}: {str(e)}")
            print(f"Event data: {json.dumps(event_data, default=str)}")
            raise

def get_cicd_events(
    event_id: str, environment: Optional[str] = None, event_type: Optional[str] = None
) -> List[CICDEvent]:
    with db_manager.get_session() as session:
        query = session.query(CICDEvent).filter(CICDEvent.event_id == event_id)
        if environment:
            query = query.filter(CICDEvent.environment == environment)
        if event_type:
            query = query.filter(CICDEvent.event_type == event_type)
        return query.order_by(CICDEvent.timestamp).all()


"""
Bug Related CRUD
"""


def create_bug(bug_data: Dict[str, Any]) -> Bug:
    with db_manager.get_session() as session:
        bug = Bug(**bug_data)
        session.add(bug)
        session.commit()
        return bug


def get_bugs(
    event_id: str, severity: Optional[str] = None, status: Optional[str] = None
) -> List[Bug]:
    with db_manager.get_session() as session:
        query = session.query(Bug).filter(Bug.event_id == event_id)
        if severity:
            query = query.filter(Bug.severity == severity)
        if status:
            query = query.filter(Bug.status == status)
        return query.order_by(Bug.created_date).all()


def update_bug_status(
    bug_id: str, new_status: str, resolution_date: Optional[datetime] = None
) -> bool:
    with db_manager.get_session() as session:
        update_data = {"status": new_status}
        if resolution_date:
            update_data["resolved_date"] = resolution_date
            # Calculate resolution time
            bug = session.query(Bug).filter(Bug.id == bug_id).first()
            if bug and bug.created_date:
                hours = (resolution_date - bug.created_date).total_seconds() / 3600
                update_data["resolution_time_hours"] = int(hours)

        result = session.query(Bug).filter(Bug.id == bug_id).update(update_data)
        session.commit()
        return result > 0


"""
Sprint Related CRUD
"""


def create_sprint(sprint_data: Dict[str, Any]) -> Sprint:
    with db_manager.get_session() as session:
        # Remove jira_items from the data before creating Sprint
        _ = sprint_data.pop("jira_items", [])
        sprint = Sprint(**sprint_data)
        session.add(sprint)
        session.commit()
        return sprint


def get_sprints(event_id: str, status: Optional[str] = None) -> List[Sprint]:
    with db_manager.get_session() as session:
        query = session.query(Sprint).filter(Sprint.event_id == event_id)
        if status:
            query = query.filter(Sprint.status == status)
        return query.order_by(Sprint.start_date).all()


def create_sprint_jira_associations(sprint_id: str, jira_ids: List[str]) -> bool:
    with db_manager.get_session() as session:
        try:
            sprint = session.query(Sprint).filter(Sprint.id == sprint_id).first()
            if not sprint:
                return False

            jiras = session.query(JiraItem).filter(JiraItem.id.in_(jira_ids)).all()
            sprint.jira_items.extend(jiras)
            session.commit()
            return True
        except Exception as e:
            print(f"Error creating sprint-jira associations: {e}")
            session.rollback()
            return False


"""
Team Related CRUD
"""


def create_team_metrics(metrics_data: Dict[str, Any]) -> TeamMetrics:
    with db_manager.get_session() as session:
        metrics = TeamMetrics(**metrics_data)
        session.add(metrics)
        session.commit()
        return metrics


def get_team_metrics(
    event_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[TeamMetrics]:
    with db_manager.get_session() as session:
        query = session.query(TeamMetrics).filter(TeamMetrics.event_id == event_id)
        if start_date:
            query = query.filter(TeamMetrics.week_starting >= start_date)
        if end_date:
            query = query.filter(TeamMetrics.week_starting <= end_date)
        return query.order_by(TeamMetrics.week_starting).all()


# Add new enum for PR status
class PRStatus(enum.Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    MERGED = "MERGED"

class PullRequest(Base):
    __tablename__ = "pull_requests"
    __table_args__ = (
        PrimaryKeyConstraint("id", "created_at"),
        {"schema": "sdlc_timeseries"},
    )

    id = Column(String)
    created_at = Column(DateTime, nullable=False)
    project_id = Column(String, ForeignKey("sdlc_timeseries.projects.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    branch_from = Column(String, nullable=False)
    branch_to = Column(String, nullable=False)
    author = Column(String, nullable=False)
    status = Column(SQLEnum(PRStatus), nullable=False)
    merged_at = Column(DateTime)
    commit_id = Column(String)
    commit_timestamp = Column(DateTime)

class PRComment(Base):
    __tablename__ = "pr_comments"
    __table_args__ = (
        PrimaryKeyConstraint("id", "created_at"),
        # Remove the foreign key constraint but keep the columns for logical relationship
        {"schema": "sdlc_timeseries"},
    )

    id = Column(String)
    created_at = Column(DateTime, nullable=False)
    pr_id = Column(String, nullable=False)
    pr_created_at = Column(DateTime, nullable=False)  # Keep for data consistency
    author = Column(String, nullable=False)
    content = Column(Text, nullable=False)


def create_pr_comment(comment_data: Dict[str, Any]) -> PRComment:
    """
    Create a new PR comment with validation of PR existence.

    Args:
        comment_data (Dict[str, Any]): Dictionary containing comment data

    Returns:
        PRComment: Created comment object

    Raises:
        ValueError: If the referenced PR doesn't exist
    """
    valid_fields = {"id", "pr_id", "created_at", "author", "content"}
    filtered_data = {k: v for k, v in comment_data.items() if k in valid_fields}

    with db_manager.get_session() as session:
        # Verify PR exists but handle relationship manually
        pr = (
            session.query(PullRequest)
            .filter(PullRequest.id == filtered_data["pr_id"])
            .first()
        )

        if not pr:
            raise ValueError(f"Pull request {filtered_data['pr_id']} not found")

        # Add PR created_at to maintain relationship
        filtered_data["pr_created_at"] = pr.created_at

        comment = PRComment(**filtered_data)
        session.add(comment)
        session.commit()
        return comment


def get_pr_comments(
    pr_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[PRComment]:
    """
    Get comments for a specific PR.

    Args:
        pr_id (str): Pull request ID
        start_date (Optional[datetime]): Start date filter
        end_date (Optional[datetime]): End date filter

    Returns:
        List[PRComment]: List of matching comments
    """
    with db_manager.get_session() as session:
        query = session.query(PRComment).filter(PRComment.pr_id == pr_id)

        if start_date:
            query = query.filter(PRComment.created_at >= start_date)
        if end_date:
            query = query.filter(PRComment.created_at <= end_date)

        return query.order_by(PRComment.created_at).all()


# Add CRUD functions for Pull Requests
# Update CRUD functions for Pull Requests and Comments
def create_pull_request(pr_data: Dict[str, Any]) -> PullRequest:
    """Create a pull request with the updated schema"""
    with db_manager.get_session() as session:
        if "status" in pr_data:
            pr_data["status"] = PRStatus(pr_data["status"])
        pr = PullRequest(**pr_data)
        session.add(pr)
        session.commit()
        return pr


def get_pull_requests(
    project_id: str,
    status: Optional[PRStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[PullRequest]:
    """Get pull requests with the updated schema"""
    with db_manager.get_session() as session:
        query = session.query(PullRequest).filter(PullRequest.project_id == project_id)
        if status:
            query = query.filter(PullRequest.status == status)
        if start_date:
            query = query.filter(PullRequest.created_at >= start_date)
        if end_date:
            query = query.filter(PullRequest.created_at <= end_date)
        return query.order_by(PullRequest.created_at).all()


def update_pull_request_status(
    pr_id: str,
    created_at: datetime,
    new_status: PRStatus,
    merged_at: Optional[datetime] = None,
) -> bool:
    """Update pull request status with the updated schema"""
    with db_manager.get_session() as session:
        update_data = {"status": new_status}
        if merged_at:
            update_data["merged_at"] = merged_at
        result = (
            session.query(PullRequest)
            .filter(and_(PullRequest.id == pr_id, PullRequest.created_at == created_at))
            .update(update_data)
        )
        session.commit()
        return result > 0


def update_pr_comment(comment_id: str, created_at: datetime, new_content: str) -> bool:
    """
    Update a PR comment's content.

    Args:
        comment_id (str): ID of the comment to update
        created_at (datetime): Creation timestamp of the comment
        new_content (str): New content for the comment

    Returns:
        bool: True if the comment was updated, False otherwise
    """
    with db_manager.get_session() as session:
        result = (
            session.query(PRComment)
            .filter(
                and_(PRComment.id == comment_id, PRComment.created_at == created_at)
            )
            .update({"content": new_content})
        )
        session.commit()
        return result > 0


def delete_pr_comment(comment_id: str, created_at: datetime) -> bool:
    """
    Delete a PR comment.

    Args:
        comment_id (str): ID of the comment to delete
        created_at (datetime): Creation timestamp of the comment

    Returns:
        bool: True if the comment was deleted, False otherwise
    """
    with db_manager.get_session() as session:
        result = (
            session.query(PRComment)
            .filter(
                and_(PRComment.id == comment_id, PRComment.created_at == created_at)
            )
            .delete()
        )
        session.commit()
        return result > 0


# Helper function to convert PRComment object to dictionary
def pr_comment_to_dict(comment: PRComment) -> Dict[str, Any]:
    """
    Convert a PRComment object to a dictionary.

    Args:
        comment (PRComment): The PRComment object to convert

    Returns:
        Dict[str, Any]: Dictionary representation of the comment
    """
    return {
        "id": comment.id,
        "pr_id": comment.pr_id,
        "created_at": comment.created_at,
        "author": comment.author,
        "content": comment.content,
        "pr_created_at": comment.pr_created_at,
    }


class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def _verify_timescaledb(self):
        """Verify TimescaleDB is properly installed and enabled"""
        with self.engine.connect() as connection:
            try:
                result = connection.execute(
                    text(
                        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
                    )
                ).scalar()

                if not result:
                    connection.execute(
                        text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
                    )
                return True
            except Exception as e:
                print(f"Error verifying TimescaleDB: {e}")
                return False

    def _create_regular_indexes(self):
        """Create indexes for non-hypertables"""
        with self.engine.begin() as connection:
            try:
                # Create indexes for timestamp columns in regular tables
                connection.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_cicd_events_timestamp 
                        ON sdlc_timeseries.cicd_events (timestamp);

                        CREATE INDEX IF NOT EXISTS idx_bugs_created_date 
                        ON sdlc_timeseries.bugs (created_date);

                        CREATE INDEX IF NOT EXISTS idx_jira_items_created_date 
                        ON sdlc_timeseries.jira_items (created_date);

                        CREATE INDEX IF NOT EXISTS idx_sprints_start_date 
                        ON sdlc_timeseries.sprints (start_date);
                        """
                    )
                )

                # Create indexes for sprint_jira_association only
                connection.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_sprint_jira_assoc_sprint 
                        ON sdlc_timeseries.sprint_jira_association (sprint_id);

                        CREATE INDEX IF NOT EXISTS idx_sprint_jira_assoc_jira 
                        ON sdlc_timeseries.sprint_jira_association (jira_id);
                        """
                    )
                )

                print("Created regular indexes")
            except Exception as e:
                print(f"Error creating indexes: {e}")
                raise

    def _create_hypertables(self):
        """Convert specific tables to hypertables"""
        hypertables = [
            ("design_events", "timestamp"),
            ("code_commits", "timestamp"),
            ("team_metrics", "week_starting"),
            ("pull_requests", "created_at"),
            ("pr_comments", "created_at"),
        ]

        with self.engine.begin() as connection:
            for table, time_column in hypertables:
                try:
                    # Create the hypertable without enforcing foreign key relationships
                    connection.execute(
                        text(
                            f"""
                            SELECT create_hypertable(
                                'sdlc_timeseries.{table}',
                                '{time_column}',
                                if_not_exists => TRUE,
                                migrate_data => TRUE,
                                create_default_indexes => TRUE
                            );
                            """
                        )
                    )
                    print(f"Created hypertable for {table}")
                except Exception as e:
                    print(f"Error creating hypertable for {table}: {e}")
                    raise

    def init_db(self):
        """Initialize the database schema"""
        if not self._verify_timescaledb():
            raise RuntimeError("TimescaleDB verification failed")

        try:
            # Drop and recreate schema
            with self.engine.begin() as connection:
                connection.execute(
                    text("DROP SCHEMA IF EXISTS sdlc_timeseries CASCADE")
                )
                connection.execute(text("CREATE SCHEMA sdlc_timeseries"))
                connection.execute(text("COMMIT"))

            # Create all tables first
            Base.metadata.create_all(self.engine)

            # Create regular indexes
            self._create_regular_indexes()

            # Create hypertables
            self._create_hypertables()

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def get_session(self):
        return self.Session()


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

db_manager = DatabaseManager(connection_string)


def bulk_insert(model_class: Any, items: List[Dict[str, Any]]) -> bool:
    with db_manager.get_session() as session:
        try:
            session.bulk_insert_mappings(model_class, items)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Bulk insert failed: {str(e)}")
            return False
