from datetime import datetime
from typing import Any, Dict, List, Optional

from model.events_schema import (Bug, CICDEvent, CodeCommit, DesignEvent,
                                 JiraItem, Project, Sprint, StageType,
                                 TeamMetrics)
from model.timescaledb_init import DatabaseManager


class CRUDManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    # Project Operations (unchanged as they use 'id')
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

    # Design Event Operations
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

    # Jira Operations
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

    # Code Commit Operations
    def create_commit(self, commit_data: Dict[str, Any]) -> CodeCommit:
        with self.db_manager.get_session() as session:
            commit = CodeCommit(**commit_data)
            session.add(commit)
            session.commit()
            return commit

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

    # CICD Event Operations
    def create_cicd_event(self, event_data: Dict[str, Any]) -> CICDEvent:
        with self.db_manager.get_session() as session:
            event = CICDEvent(**event_data)
            session.add(event)
            session.commit()
            return event

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

    # Bug Operations
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

    # Sprint Operations
    def create_sprint(self, sprint_data: Dict[str, Any]) -> Sprint:
        with self.db_manager.get_session() as session:
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

    # Team Metrics Operations
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

    # Batch Operations
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
