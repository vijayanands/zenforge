# events_schema.py
import enum
from operator import and_

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
    Table,
    ForeignKeyConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Junction tables
cicd_commit_association = Table(
    "cicd_commit_association",
    Base.metadata,
    Column("cicd_id", String, ForeignKey("sdlc_timeseries.cicd_events.id")),
    Column("commit_id", String),
    Column("commit_timestamp", DateTime),
    ForeignKeyConstraint(
        ["commit_id", "commit_timestamp"],
        ["sdlc_timeseries.code_commits.id", "sdlc_timeseries.code_commits.timestamp"],
    ),
    schema="sdlc_timeseries",
)

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
    timestamp = Column(DateTime, nullable=False)
    environment = Column(String)
    event_type = Column(String)
    build_id = Column(String, nullable=False, unique=True)
    status = Column(String)
    duration_seconds = Column(Integer)
    metrics = Column(JSONB)
    reason = Column(String, nullable=True)

    commits = relationship(
        "CodeCommit",
        secondary=cicd_commit_association,
        primaryjoin=(id == cicd_commit_association.c.cicd_id),
        secondaryjoin=and_(
            CodeCommit.id == cicd_commit_association.c.commit_id,
            CodeCommit.timestamp == cicd_commit_association.c.commit_timestamp,
        ),
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
