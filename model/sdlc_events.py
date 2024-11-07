import enum
from datetime import datetime
from operator import and_
from typing import Any, Dict, List, Optional, Type

from sqlalchemy import Boolean, Column, DateTime
from sqlalchemy import Enum
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Float,
    ForeignKey,
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


# Add new enum for PR status
class PRStatus(enum.Enum):
    OPEN = "OPEN"
    BLOCKED = "BLOCKED"
    MERGED = "MERGED"


class Environment(enum.Enum):
    DEV = "dev"
    QA = "qa"
    STAGING = "staging"
    UAT = "uat"
    PRODUCTION = "production"


class BuildStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILURE = "failure"


class BuildMode(enum.Enum):
    MANUAL = "manual"
    AUTOMATIC = "automatic"


# Enums for Bug table
class BugType(enum.Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    FUNCTIONALITY = "functionality"
    DATA = "data"
    UI_UX = "ui_ux"


class ImpactArea(enum.Enum):
    CUSTOMER = "customer"
    INTERNAL = "internal"
    INTEGRATION = "integration"
    INFRASTRUCTURE = "infrastructure"


class BugStatus(enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    FIXED = "FIXED"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"


# Regular tables
class CICDEvent(Base):
    __tablename__ = "cicd_events"
    __table_args__ = (
        PrimaryKeyConstraint("event_id", "timestamp"),
        {"schema": "sdlc_timeseries"},
    )

    event_id = Column(String)
    timestamp = Column(DateTime, nullable=False)
    project_id = Column(
        String, ForeignKey("sdlc_timeseries.projects.id"), nullable=False
    )  # Add this line
    environment = Column(SQLEnum(Environment), nullable=False)
    event_type = Column(String, default="build", nullable=False)
    build_id = Column(String, nullable=False)
    status = Column(SQLEnum(BuildStatus), nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    branch = Column(String, nullable=False)
    tag = Column(String, nullable=True)
    mode = Column(SQLEnum(BuildMode), nullable=False)
    release_version = Column(String, nullable=True)


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


class Bug(Base):
    __tablename__ = "bugs"
    __table_args__ = {"schema": "sdlc_timeseries"}

    id = Column(String, primary_key=True)
    project_id = Column(
        String, ForeignKey("sdlc_timeseries.projects.id"), nullable=False
    )
    bug_type = Column(SQLEnum(BugType), nullable=False)
    impact_area = Column(SQLEnum(ImpactArea), nullable=False)
    severity = Column(String, default="P0", nullable=False)
    title = Column(String, nullable=False)
    status = Column(SQLEnum(BugStatus), nullable=False)
    created_date = Column(DateTime, nullable=False)
    resolved_date = Column(DateTime)
    close_date = Column(DateTime)
    resolution_time_hours = Column(Float)
    assigned_to = Column(String, nullable=False)
    environment_found = Column(SQLEnum(Environment), nullable=False)
    build_id = Column(String, nullable=False)
    release_id = Column(String, nullable=False)


"""
CICD Related CRUD
"""


# Add CRUD functions for CICD events
def create_cicd_event(event_data: Dict[str, Any]) -> CICDEvent:
    """Create a new CICD event"""
    with db_manager.get_session() as session:
        if "environment" in event_data:
            event_data["environment"] = Environment(event_data["environment"])
        if "status" in event_data:
            event_data["status"] = BuildStatus(event_data["status"])
        if "mode" in event_data:
            event_data["mode"] = BuildMode(event_data["mode"])

        event = CICDEvent(**event_data)
        session.add(event)
        session.commit()
        return event


def get_cicd_events(
    event_id: Optional[str] = None,
    environment: Optional[Environment] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[CICDEvent]:
    """Get CICD events with optional filters"""
    with db_manager.get_session() as session:
        query = session.query(CICDEvent)

        if event_id:
            query = query.filter(CICDEvent.event_id == event_id)
        if environment:
            query = query.filter(CICDEvent.environment == environment)
        if start_date:
            query = query.filter(CICDEvent.timestamp >= start_date)
        if end_date:
            query = query.filter(CICDEvent.timestamp <= end_date)

        return query.order_by(CICDEvent.timestamp).all()


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
) -> list[Type[DesignEvent]]:
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


def get_jira_items(
    event_id: str, item_type: Optional[str] = None
) -> list[Type[JiraItem]]:
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
) -> list[Type[CodeCommit]]:
    with db_manager.get_session() as session:
        query = session.query(CodeCommit).filter(CodeCommit.event_id == event_id)
        if start_date:
            query = query.filter(CodeCommit.timestamp >= start_date)
        if end_date:
            query = query.filter(CodeCommit.timestamp <= end_date)
        return query.order_by(CodeCommit.timestamp).all()


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


def get_sprints(event_id: str, status: Optional[str] = None) -> list[Type[Sprint]]:
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
) -> list[Type[PullRequest]]:
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


# CRUD Operations
def create_bug(bug_data: Dict[str, Any]) -> Bug:
    """Create a new bug record"""
    with db_manager.get_session() as session:
        if isinstance(bug_data.get("bug_type"), str):
            bug_data["bug_type"] = BugType(bug_data["bug_type"])
        if isinstance(bug_data.get("impact_area"), str):
            bug_data["impact_area"] = ImpactArea(bug_data["impact_area"])
        if isinstance(bug_data.get("status"), str):
            bug_data["status"] = BugStatus(bug_data["status"])
        if isinstance(bug_data.get("environment_found"), str):
            bug_data["environment_found"] = Environment(bug_data["environment_found"])

        bug = Bug(**bug_data)
        session.add(bug)
        session.commit()
        return bug


def get_bug(bug_id: str) -> Optional[Bug]:
    """Retrieve a bug by ID"""
    with db_manager.get_session() as session:
        return session.query(Bug).filter(Bug.id == bug_id).first()


def get_bugs_by_project(
    project_id: str,
    status: Optional[BugStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[Bug]:
    """Get bugs for a project with optional filters"""
    with db_manager.get_session() as session:
        query = session.query(Bug).filter(Bug.project_id == project_id)

        if status:
            query = query.filter(Bug.status == status)
        if start_date:
            query = query.filter(Bug.created_date >= start_date)
        if end_date:
            query = query.filter(Bug.created_date <= end_date)

        return query.order_by(Bug.created_date).all()


def update_bug_status(
    bug_id: str,
    new_status: BugStatus,
    resolution_time_hours: Optional[float] = None,
    resolved_date: Optional[datetime] = None,
    close_date: Optional[datetime] = None,
) -> bool:
    """Update bug status and related fields"""
    with db_manager.get_session() as session:
        update_data = {"status": new_status}
        if resolution_time_hours is not None:
            update_data["resolution_time_hours"] = resolution_time_hours
        if resolved_date is not None:
            update_data["resolved_date"] = resolved_date
        if close_date is not None:
            update_data["close_date"] = close_date

        result = session.query(Bug).filter(Bug.id == bug_id).update(update_data)
        session.commit()
        return result > 0


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

                # Add bug-related indexes
                connection.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_bugs_created_date 
                        ON sdlc_timeseries.bugs (created_date);

                        CREATE INDEX IF NOT EXISTS idx_bugs_project_build 
                        ON sdlc_timeseries.bugs (project_id, build_id);
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
            ("pull_requests", "created_at"),
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


def verify_temporal_consistency(
    commits: List[Dict[str, Any]], jira_items: List[Dict[str, Any]]
) -> List[str]:
    """Verify temporal consistency between commits and Jira items"""
    errors = []

    # Create completion date lookup for Jiras
    jira_completion_dates = {
        jira["id"]: jira.get("completed_date") for jira in jira_items
    }

    # Check commit-Jira temporal relationship
    for commit in commits:
        jira_completion_date = jira_completion_dates.get(commit["jira_id"])
        if jira_completion_date is None:
            errors.append(
                f"Commit {commit['id']} references Jira {commit['jira_id']} which has no completion date"
            )
        elif commit["timestamp"] <= jira_completion_date:
            errors.append(
                f"Commit {commit['id']} timestamp ({commit['timestamp']}) is not after "
                f"its Jira {commit['jira_id']} completion date ({jira_completion_date})"
            )

    return errors


def verify_project_references(all_data: Dict[str, Any]) -> List[str]:
    """Verify all project references are valid"""
    errors = []

    # Get set of valid project IDs
    project_ids = {proj["id"] for proj in all_data["projects"]}

    # Check commits
    for commit in all_data["commits"]:
        if commit["event_id"] not in project_ids:
            errors.append(
                f"Commit {commit['id']} references invalid project {commit['event_id']}"
            )

    # Check sprints
    for sprint in all_data["sprints"]:
        if sprint["event_id"] not in project_ids:
            errors.append(
                f"Sprint {sprint['id']} references invalid project {sprint['event_id']}"
            )

    return errors


def verify_jira_references(all_data: Dict[str, Any]) -> List[str]:
    """Verify all Jira references are valid"""
    errors = []

    # Get set of valid Jira IDs
    jira_ids = {jira["id"] for jira in all_data["jira_items"]}

    # Check commits
    for commit in all_data["commits"]:
        if commit["jira_id"] not in jira_ids:
            errors.append(
                f"Commit {commit['id']} references invalid Jira {commit['jira_id']}"
            )

    # Check sprint associations
    for sprint_id, sprint_jiras in all_data["relationships"][
        "sprint_jira_associations"
    ].items():
        for jira_id in sprint_jiras:
            if jira_id not in jira_ids:
                errors.append(f"Sprint {sprint_id} references invalid Jira {jira_id}")

    return errors


def verify_pr_exists(session, pr_id: str, pr_created_at: datetime) -> bool:
    """
    Verify that a pull request exists in the database.

    Args:
        session: SQLAlchemy session
        pr_id: Pull request ID
        pr_created_at: Pull request creation timestamp

    Returns:
        bool: True if the PR exists, False otherwise
    """
    return (
        session.query(PullRequest)
        .filter(and_(PullRequest.id == pr_id, PullRequest.created_at == pr_created_at))
        .first()
        is not None
    )
