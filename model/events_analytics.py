import json
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import Integer, and_, case, func

from model.sdlc_events import (
    Bug,
    CICDEvent,
    CodeCommit,
    DesignEvent,
    Sprint,
    TeamMetrics, DatabaseManager,
)
from model.load_events_db import initialize_db_manager


class EventAnalytics:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def get_commit_statistics(
        self, event_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Get commit statistics for a given time period"""
        with self.db_manager.get_session() as session:
            stats = (
                session.query(
                    func.count(CodeCommit.id).label("total_commits"),
                    func.sum(CodeCommit.files_changed).label("total_files_changed"),
                    func.sum(CodeCommit.lines_added).label("total_lines_added"),
                    func.sum(CodeCommit.lines_removed).label("total_lines_removed"),
                    func.avg(CodeCommit.code_coverage).label("avg_code_coverage"),
                    func.avg(CodeCommit.lint_score).label("avg_lint_score"),
                    func.avg(CodeCommit.review_time_minutes).label("avg_review_time"),
                    func.sum(CodeCommit.comments_count).label("total_comments"),
                )
                .filter(
                    and_(
                        CodeCommit.event_id == event_id,
                        CodeCommit.timestamp >= start_date,
                        CodeCommit.timestamp <= end_date,
                    )
                )
                .first()
            )

            if not stats:
                return {
                    "total_commits": 0,
                    "total_files_changed": 0,
                    "total_lines_added": 0,
                    "total_lines_removed": 0,
                    "avg_code_coverage": None,
                    "avg_lint_score": None,
                    "avg_review_time_minutes": None,
                    "total_review_comments": 0,
                }
            return {
                "total_commits": stats.total_commits,
                "total_files_changed": stats.total_files_changed,
                "total_lines_added": stats.total_lines_added,
                "total_lines_removed": stats.total_lines_removed,
                "avg_code_coverage": (
                    float(stats.avg_code_coverage) if stats.avg_code_coverage else None
                ),
                "avg_lint_score": (
                    float(stats.avg_lint_score) if stats.avg_lint_score else None
                ),
                "avg_review_time_minutes": (
                    float(stats.avg_review_time) if stats.avg_review_time else None
                ),
                "total_review_comments": stats.total_comments,
            }

    def get_deployment_success_rate(
        self, event_id: str, environment: str, time_window: timedelta
    ) -> float:
        """Calculate deployment success rate for a given environment"""
        with self.db_manager.get_session() as session:
            end_date = datetime.now()
            start_date = end_date - time_window

            deployments = (
                session.query(
                    func.count(CICDEvent.id).label("total"),
                    func.sum(
                        case((CICDEvent.status == "success", 1), else_=0).cast(Integer)
                    ).label("successful"),
                )
                .filter(
                    and_(
                        CICDEvent.event_id == event_id,
                        CICDEvent.environment == environment,
                        CICDEvent.event_type == "deployment",
                        CICDEvent.timestamp.between(start_date, end_date),
                    )
                )
                .first()
            )

            if not deployments or deployments.total == 0:
                return 0.0
            return (deployments.successful / deployments.total) * 100

    def get_project_timeline(self, event_id: str) -> List[Dict[str, Any]]:
        """Get a complete timeline of events for a specific project"""
        with self.db_manager.get_session() as session:
            # Query all relevant events
            design_events = (
                session.query(DesignEvent)
                .filter(DesignEvent.event_id == event_id)
                .all()
            )

            commit_events = (
                session.query(CodeCommit).filter(CodeCommit.event_id == event_id).all()
            )

            cicd_events = (
                session.query(CICDEvent).filter(CICDEvent.event_id == event_id).all()
            )

            bug_events = session.query(Bug).filter(Bug.event_id == event_id).all()

            sprint_events = (
                session.query(Sprint).filter(Sprint.event_id == event_id).all()
            )

            # Combine and sort all events
            timeline = []
            for event in (
                design_events + commit_events + cicd_events + bug_events + sprint_events
            ):
                event_data = {
                    "timestamp": getattr(event, "timestamp", None)
                    or getattr(event, "created_date", None),
                    "event_type": event.__class__.__name__,
                    "details": {
                        column.name: getattr(event, column.name)
                        for column in event.__table__.columns
                        if column.name not in ("id", "timestamp", "created_date")
                    },
                }
                if event_data["timestamp"]:  # Only add events with valid timestamps
                    timeline.append(event_data)

            return sorted(timeline, key=lambda x: x["timestamp"])

    def get_bug_report(
        self, event_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate a report on bugs"""
        with self.db_manager.get_session() as session:
            bugs = (
                session.query(Bug)
                .filter(
                    and_(
                        Bug.event_id == event_id,
                        Bug.created_date.between(start_date, end_date),
                    )
                )
                .all()
            )

            fixed_bugs = (
                session.query(Bug)
                .filter(
                    and_(
                        Bug.event_id == event_id,
                        Bug.created_date.between(start_date, end_date),
                        Bug.status == "resolved",
                    )
                )
                .count()
            )

            resolution_times = [
                bug.resolution_time_hours
                for bug in bugs
                if bug.status == "resolved" and bug.resolution_time_hours is not None
            ]
            avg_resolution_time = None  # Initialize avg_resolution_time
            if resolution_times:  # Check if resolution_times is not empty
                avg_resolution_time = sum(resolution_times) / len(resolution_times)

            # Group by severity
            severity_counts = {}
            for bug in bugs:
                severity_counts[bug.severity] = severity_counts.get(bug.severity, 0) + 1

            return {
                "total_bugs": len(bugs),
                "fixed_bugs": fixed_bugs,
                "fix_rate": (fixed_bugs / len(bugs) * 100) if len(bugs) > 0 else 0,
                "avg_resolution_time_hours": avg_resolution_time,
                "severity_distribution": severity_counts,
            }

    def get_team_performance_metrics(
        self, event_id: str, time_window: timedelta
    ) -> Dict[str, Any]:
        """Get team performance metrics over time"""
        with self.db_manager.get_session() as session:
            end_date = datetime.now()
            start_date = end_date - time_window

            metrics = (
                session.query(TeamMetrics)
                .filter(
                    and_(
                        TeamMetrics.event_id == event_id,
                        TeamMetrics.week_starting.between(start_date, end_date),
                    )
                )
                .order_by(TeamMetrics.week_starting)
                .all()
            )

            if not metrics:
                return {}

            return {
                "avg_velocity": sum(
                    m.velocity for m in metrics if m.velocity is not None
                )
                / len(metrics),
                "avg_code_review_turnaround": sum(
                    m.code_review_turnaround_hours
                    for m in metrics
                    if m.code_review_turnaround_hours is not None
                )
                / len(metrics),
                "avg_build_success_rate": sum(
                    m.build_success_rate
                    for m in metrics
                    if m.build_success_rate is not None
                )
                / len(metrics),
                "avg_test_coverage": sum(
                    m.test_coverage for m in metrics if m.test_coverage is not None
                )
                / len(metrics),
            }


def main():
    db_manager = (
        initialize_db_manager()
    )  # Use initialize_db_manager to initialize db_manager

    event_id = "example_event_id"
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    environment = "production"
    time_window = timedelta(days=30)

    analytics = EventAnalytics(db_manager)

    commit_stats = analytics.get_commit_statistics(event_id, start_date, end_date)
    deployment_success_rate = analytics.get_deployment_success_rate(
        event_id, environment, time_window
    )
    project_timeline = analytics.get_project_timeline(event_id)
    bug_report = analytics.get_bug_report(event_id, start_date, end_date)
    team_performance_metrics = analytics.get_team_performance_metrics(
        event_id, time_window
    )

    results = {
        "commit_statistics": commit_stats,
        "deployment_success_rate": deployment_success_rate,
        "project_timeline": project_timeline,
        "bug_report": bug_report,
        "team_performance_metrics": team_performance_metrics,
    }

    print(json.dumps(results, indent=4, default=str))


if __name__ == "__main__":
    main()
