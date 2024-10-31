from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy import and_
from sqlalchemy.orm import Session

from model.sdlc_events import DesignEvent, Sprint, CodeCommit, JiraItem, PullRequest, CICDEvent, PRStatus, Bug


def validate_design_sprint_timeline(session: Session) -> List[str]:
    """Validate that design phases complete before sprint timelines start"""
    errors = []
    
    # Get all design events grouped by project
    design_events = session.query(DesignEvent).order_by(DesignEvent.timestamp).all()
    design_end_times = {}
    
    # Find the last design event for each project
    for event in design_events:
        if event.event_id not in design_end_times:
            design_end_times[event.event_id] = event.timestamp
        else:
            design_end_times[event.event_id] = max(design_end_times[event.event_id], event.timestamp)
    
    # Check sprint start times against design end times
    sprints = session.query(Sprint).order_by(Sprint.start_date).all()
    for sprint in sprints:
        if sprint.event_id in design_end_times:
            if sprint.start_date < design_end_times[sprint.event_id]:
                errors.append(f"Sprint {sprint.id} starts at {sprint.start_date} before design phase completion at {design_end_times[sprint.event_id]}")
    
    return errors

def validate_sprint_jira_timeline(session: Session) -> List[str]:
    """Validate that sprint timelines align with their Jira items"""
    errors = []
    
    sprints = session.query(Sprint).all()
    for sprint in sprints:
        if not sprint.jira_items:
            continue
            
        # Find earliest and latest Jira dates
        earliest_jira = min(j.created_date for j in sprint.jira_items)
        latest_jira = max((j.completed_date for j in sprint.jira_items if j.completed_date), default=None)
        
        if sprint.start_date < earliest_jira:
            errors.append(f"Sprint {sprint.id} starts at {sprint.start_date} before its earliest Jira at {earliest_jira}")
            
        if latest_jira and sprint.end_date and sprint.end_date < latest_jira:
            errors.append(f"Sprint {sprint.id} ends at {sprint.end_date} before its latest Jira completion at {latest_jira}")
    
    return errors

def validate_commit_jira_timeline(session: Session) -> List[str]:
    """Validate that commits only happen after or at Jira completion"""
    errors = []
    
    commits = session.query(CodeCommit).order_by(CodeCommit.timestamp).all()
    for commit in commits:
        jira = session.query(JiraItem).filter(JiraItem.id == commit.jira_id).first()
        if jira and jira.completed_date and commit.timestamp < jira.completed_date:
            errors.append(f"Commit {commit.id} at {commit.timestamp} happens before Jira {jira.id} completion at {jira.completed_date}")
    
    return errors

def validate_pr_commit_timeline(session: Session) -> List[str]:
    """Validate that PRs don't start before their associated commits"""
    errors = []
    
    prs = session.query(PullRequest).order_by(PullRequest.created_at).all()
    for pr in prs:
        if pr.commit_timestamp and pr.created_at < pr.commit_timestamp:
            errors.append(f"PR {pr.id} created at {pr.created_at} before its commit at {pr.commit_timestamp}")
    
    return errors

def validate_cicd_pr_timeline(session: Session) -> List[str]:
    """Validate that CI/CD builds start only after PR completion"""
    errors = []
    
    cicd_events = session.query(CICDEvent).order_by(CICDEvent.timestamp).all()
    for event in cicd_events:
        # Find associated commits and their PRs
        for commit in event.commits:
            prs = session.query(PullRequest).filter(
                and_(
                    PullRequest.commit_id == commit.id,
                    PullRequest.commit_timestamp == commit.timestamp
                )
            ).all()
            
            for pr in prs:
                if pr.status != PRStatus.MERGED or event.timestamp < pr.merged_at:
                    errors.append(f"CICD event {event.id} at {event.timestamp} started before PR {pr.id} was merged at {pr.merged_at}")
    
    return errors

def validate_bug_build_timeline(session: Session) -> List[str]:
    """Validate that P0 bugs and releases only happen after CI/CD build completion"""
    errors = []
    
    bugs = session.query(Bug).filter(Bug.severity == 'P0').order_by(Bug.created_date).all()
    for bug in bugs:
        build = session.query(CICDEvent).filter(CICDEvent.build_id == bug.build_id).first()
        if build and bug.created_date < build.timestamp:
            errors.append(f"P0 Bug {bug.id} created at {bug.created_date} before build {build.id} completion at {build.timestamp}")
    
    return errors

def validate_all_timelines(session: Session) -> Dict[str, List[str]]:
    """Run all timeline validations and return results"""
    return {
        "design_sprint": validate_design_sprint_timeline(session),
        "sprint_jira": validate_sprint_jira_timeline(session),
        "commit_jira": validate_commit_jira_timeline(session),
        "pr_commit": validate_pr_commit_timeline(session),
        "cicd_pr": validate_cicd_pr_timeline(session),
        "bug_build": validate_bug_build_timeline(session)
    }
