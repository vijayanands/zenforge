# events_crud.py
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from model.events_schema import (
    Bug,
    CICDEvent,
    CodeCommit,
    DesignEvent,
    JiraItem,
    Project,
    Sprint,
    StageType,
    TeamMetrics, PullRequest, PullRequestComment, PRStatus,
)
from model.timescaledb_init import DatabaseManager


class CRUDManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def create_project(self, project_data: Dict[str, Any]) -> Project:
        with self.db_manager.get_session() as session:
            project = Project(**project_data)
            session.add(project)
            session.commit()
            return project

    def get_project(self, project_id: str) -> Optional[Project]:
        with self.db_manager.get_session() as session:
            return session.query(Project).filter(Project.id == project_id).first()

    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> bool:
        with self.db_manager.get_session() as session:
            result = (
                session.query(Project)
                .filter(Project.id == project_id)
                .update(update_data)
            )
            session.commit()
            return result > 0

    def delete_project(self, project_id: str) -> bool:
        with self.db_manager.get_session() as session:
            result = session.query(Project).filter(Project.id == project_id).delete()
            session.commit()
            return result > 0

    def create_design_event(self, event_data: Dict[str, Any]) -> DesignEvent:
        if "stage" in event_data:
            event_data["stage"] = StageType(event_data["stage"])
        with self.db_manager.get_session() as session:
            event = DesignEvent(**event_data)
            session.add(event)
            session.commit()
            return event

    def get_design_events(
        self, event_id: str, design_type: Optional[str] = None
    ) -> List[DesignEvent]:
        with self.db_manager.get_session() as session:
            query = session.query(DesignEvent).filter(DesignEvent.event_id == event_id)
            if design_type:
                query = query.filter(DesignEvent.design_type == design_type)
            return query.order_by(DesignEvent.timestamp).all()

    def create_jira_item(self, jira_data: Dict[str, Any]) -> JiraItem:
        with self.db_manager.get_session() as session:
            jira = JiraItem(**jira_data)
            session.add(jira)
            session.commit()
            return jira

    def get_jira_items(
        self, event_id: str, item_type: Optional[str] = None
    ) -> List[JiraItem]:
        with self.db_manager.get_session() as session:
            query = session.query(JiraItem).filter(JiraItem.event_id == event_id)
            if item_type:
                query = query.filter(JiraItem.type == item_type)
            return query.order_by(JiraItem.created_date).all()

    def update_jira_status(
        self, jira_id: str, new_status: str, completion_date: Optional[datetime] = None
    ) -> bool:
        with self.db_manager.get_session() as session:
            update_data = {"status": new_status}
            if completion_date:
                update_data["completed_date"] = completion_date
            result = (
                session.query(JiraItem)
                .filter(JiraItem.id == jira_id)
                .update(update_data)
            )
            session.commit()
            return result > 0

    def create_commit(self, commit_data: Dict[str, Any]) -> CodeCommit:
        with self.db_manager.get_session() as session:
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
        self,
        event_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[CodeCommit]:
        with self.db_manager.get_session() as session:
            query = session.query(CodeCommit).filter(CodeCommit.event_id == event_id)
            if start_date:
                query = query.filter(CodeCommit.timestamp >= start_date)
            if end_date:
                query = query.filter(CodeCommit.timestamp <= end_date)
            return query.order_by(CodeCommit.timestamp).all()

    def create_cicd_event(self, event_data: Dict[str, Any]) -> CICDEvent:
        with self.db_manager.get_session() as session:
            try:
                # Get commit associations from the data
                commit_pairs = event_data.pop("commit_pairs", [])

                # Create CICD event first
                event = CICDEvent(**event_data)
                session.add(event)
                session.flush()  # Flush to get the event ID

                # Associate commits if provided
                if commit_pairs:
                    for commit_id, timestamp in commit_pairs:
                        commit = (
                            session.query(CodeCommit)
                            .filter(
                                and_(
                                    CodeCommit.id == commit_id,
                                    CodeCommit.timestamp == timestamp,
                                    CodeCommit.timestamp < event.timestamp,
                                )
                            )
                            .first()
                        )

                        if commit:
                            event.commits.append(commit)
                        else:
                            print(
                                f"Warning: Commit {commit_id} at {timestamp} not found or is newer than CICD event"
                            )

                session.commit()
                return event

            except Exception as e:
                session.rollback()
                print(f"Error creating CICD event: {e}")
                raise

    def get_cicd_events(
        self,
        event_id: str,
        environment: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[CICDEvent]:
        with self.db_manager.get_session() as session:
            query = session.query(CICDEvent).filter(CICDEvent.event_id == event_id)
            if environment:
                query = query.filter(CICDEvent.environment == environment)
            if event_type:
                query = query.filter(CICDEvent.event_type == event_type)
            return query.order_by(CICDEvent.timestamp).all()

    def create_bug(self, bug_data: Dict[str, Any]) -> Bug:
        with self.db_manager.get_session() as session:
            bug = Bug(**bug_data)
            session.add(bug)
            session.commit()
            return bug

    def get_bugs(
        self,
        event_id: str,
        severity: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Bug]:
        with self.db_manager.get_session() as session:
            query = session.query(Bug).filter(Bug.event_id == event_id)
            if severity:
                query = query.filter(Bug.severity == severity)
            if status:
                query = query.filter(Bug.status == status)
            return query.order_by(Bug.created_date).all()

    def update_bug_status(
        self, bug_id: str, new_status: str, resolution_date: Optional[datetime] = None
    ) -> bool:
        with self.db_manager.get_session() as session:
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

    def create_sprint(self, sprint_data: Dict[str, Any]) -> Sprint:
        with self.db_manager.get_session() as session:
            # Remove jira_items from the data before creating Sprint
            jira_items = sprint_data.pop("jira_items", [])
            sprint = Sprint(**sprint_data)
            session.add(sprint)
            session.commit()
            return sprint

    def get_sprints(self, event_id: str, status: Optional[str] = None) -> List[Sprint]:
        with self.db_manager.get_session() as session:
            query = session.query(Sprint).filter(Sprint.event_id == event_id)
            if status:
                query = query.filter(Sprint.status == status)
            return query.order_by(Sprint.start_date).all()

    def create_sprint_jira_associations(
        self, sprint_id: str, jira_ids: List[str]
    ) -> bool:
        with self.db_manager.get_session() as session:
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

    def create_team_metrics(self, metrics_data: Dict[str, Any]) -> TeamMetrics:
        with self.db_manager.get_session() as session:
            metrics = TeamMetrics(**metrics_data)
            session.add(metrics)
            session.commit()
            return metrics

    def get_team_metrics(
        self,
        event_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[TeamMetrics]:
        with self.db_manager.get_session() as session:
            query = session.query(TeamMetrics).filter(TeamMetrics.event_id == event_id)
            if start_date:
                query = query.filter(TeamMetrics.week_starting >= start_date)
            if end_date:
                query = query.filter(TeamMetrics.week_starting <= end_date)
            return query.order_by(TeamMetrics.week_starting).all()

    def bulk_insert(self, model_class: Any, items: List[Dict[str, Any]]) -> bool:
        with self.db_manager.get_session() as session:
            try:
                session.bulk_insert_mappings(model_class, items)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                print(f"Bulk insert failed: {str(e)}")
                return False


def create_pull_request(self, pr_data: Dict[str, Any]) -> PullRequest:
    with self.db_manager.get_session() as session:
        try:
            # Extract commit associations if present
            commit_pairs = pr_data.pop("commit_pairs", [])

            # Set the status as enum
            if "status" in pr_data:
                pr_data["status"] = PRStatus(pr_data["status"])

            # Create PR
            pr = PullRequest(**pr_data)
            session.add(pr)
            session.flush()  # Flush to get the PR ID

            # Associate commits if provided
            if commit_pairs:
                for commit_id, timestamp in commit_pairs:
                    commit = (
                        session.query(CodeCommit)
                        .filter(
                            and_(
                                CodeCommit.id == commit_id,
                                CodeCommit.timestamp == timestamp,
                                CodeCommit.timestamp <= pr.created_at
                            )
                        )
                        .first()
                    )

                    if commit:
                        pr.commits.append(commit)
                    else:
                        print(f"Warning: Commit {commit_id} at {timestamp} not found or is newer than PR")

            session.commit()
            return pr

        except Exception as e:
            session.rollback()
            print(f"Error creating pull request: {e}")
            raise


def get_pull_requests(
        self,
        project_id: str,
        status: Optional[PRStatus] = None,
        author: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        include_comments: bool = False
) -> List[PullRequest]:
    with self.db_manager.get_session() as session:
        query = session.query(PullRequest).filter(PullRequest.project_id == project_id)

        if status:
            query = query.filter(PullRequest.status == status)
        if author:
            query = query.filter(PullRequest.author == author)
        if start_date:
            query = query.filter(PullRequest.created_at >= start_date)
        if end_date:
            query = query.filter(PullRequest.created_at <= end_date)

        # Optionally eager load comments
        if include_comments:
            query = query.options(joinedload(PullRequest.comments))

        return query.order_by(PullRequest.created_at.desc()).all()


def update_pull_request_status(
        self,
        pr_id: str,
        created_at: datetime,
        new_status: PRStatus,
        merged_at: Optional[datetime] = None
) -> bool:
    with self.db_manager.get_session() as session:
        try:
            update_data = {"status": new_status}
            if merged_at and new_status == PRStatus.MERGED:
                update_data["merged_at"] = merged_at

            result = (
                session.query(PullRequest)
                .filter(
                    and_(
                        PullRequest.event_id == pr_id,
                        PullRequest.created_at == created_at
                    )
                )
                .update(update_data)
            )
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            print(f"Error updating pull request status: {e}")
            return False


def create_pr_comment(self, comment_data: Dict[str, Any]) -> PullRequestComment:
    with self.db_manager.get_session() as session:
        try:
            # Extract PR identifiers to verify PR exists
            pr_id = comment_data.get('pr_id')
            pr_created_at = comment_data.get('pr_created_at')

            # Verify the PR exists first
            pr = (
                session.query(PullRequest)
                .filter(
                    and_(
                        PullRequest.event_id == pr_id,
                        PullRequest.created_at == pr_created_at
                    )
                )
                .first()
            )

            if not pr:
                raise ValueError(f"Pull Request {pr_id} created at {pr_created_at} not found")

            # Create comment with relationship to PR
            comment = PullRequestComment(**comment_data)

            # Explicitly set the relationship
            comment.pull_request = pr

            session.add(comment)
            session.commit()
            return comment
        except Exception as e:
            session.rollback()
            print(f"Error creating PR comment: {e}")
            raise


def get_pr_comments(
        self,
        pr_id: str,
        pr_created_at: datetime,
        author: Optional[str] = None,
        include_pr: bool = False
) -> List[PullRequestComment]:
    with self.db_manager.get_session() as session:
        query = session.query(PullRequestComment).filter(
            and_(
                PullRequestComment.pr_id == pr_id,
                PullRequestComment.pr_created_at == pr_created_at
            )
        )

        if author:
            query = query.filter(PullRequestComment.author == author)

        # Optionally eager load the parent PR
        if include_pr:
            query = query.options(joinedload(PullRequestComment.pull_request))

        return query.order_by(PullRequestComment.created_at).all()


def delete_pr_comment(self, comment_id: str) -> bool:
    with self.db_manager.get_session() as session:
        try:
            result = (
                session.query(PullRequestComment)
                .filter(PullRequestComment.id == comment_id)
                .delete()
            )
            session.commit()
            return result > 0
        except Exception as e:
            session.rollback()
            print(f"Error deleting PR comment: {e}")
            return False


def get_pr_with_comments(self, pr_id: str, pr_created_at: datetime) -> Optional[PullRequest]:
    """
    Get a specific PR with all its comments loaded
    """
    with self.db_manager.get_session() as session:
        return (
            session.query(PullRequest)
            .options(joinedload(PullRequest.comments))
            .filter(
                and_(
                    PullRequest.event_id == pr_id,
                    PullRequest.created_at == pr_created_at
                )
            )
            .first()
        )