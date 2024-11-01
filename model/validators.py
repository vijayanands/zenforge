from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import and_
from sqlalchemy.orm import Session

from model.sdlc_events import (
    Bug,
    CICDEvent,
    CodeCommit,
    DesignEvent,
    JiraItem,
    PRStatus,
    PullRequest,
    Sprint,
)

def validate_pr_comment_consistency() -> List[str]:
    """
    Validate PR comment relationships even without foreign key constraints.

    Returns:
        List[str]: List of validation errors found
    """
    errors = []
    with db_manager.get_session() as session:
        # Get all comments
        comments = session.query(PRComment).all()

        # Check each comment's PR reference
        for comment in comments:
            pr = session.query(PullRequest).filter(
                and_(
                    PullRequest.id == comment.pr_id,
                    PullRequest.created_at == comment.pr_created_at
                )
            ).first()

            if not pr:
                errors.append(
                    f"Comment {comment.id} references non-existent PR "
                    f"{comment.pr_id} (created_at: {comment.pr_created_at})"
                )

    return errors

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
            design_end_times[event.event_id] = max(
                design_end_times[event.event_id], event.timestamp
            )

    # Check sprint start times against design end times
    sprints = session.query(Sprint).order_by(Sprint.start_date).all()
    for sprint in sprints:
        if sprint.event_id in design_end_times:
            if sprint.start_date < design_end_times[sprint.event_id]:
                errors.append(
                    f"Sprint {sprint.id} starts at {sprint.start_date} before design phase completion at {design_end_times[sprint.event_id]}"
                )

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
        latest_jira = max(
            (j.completed_date for j in sprint.jira_items if j.completed_date),
            default=None,
        )

        if sprint.start_date < earliest_jira:
            errors.append(
                f"Sprint {sprint.id} starts at {sprint.start_date} before its earliest Jira at {earliest_jira}"
            )

        if latest_jira and sprint.end_date and sprint.end_date < latest_jira:
            errors.append(
                f"Sprint {sprint.id} ends at {sprint.end_date} before its latest Jira completion at {latest_jira}"
            )

    return errors


def validate_commit_jira_timeline(session: Session) -> List[str]:
    """Validate that commits only happen after or at Jira completion"""
    errors = []

    commits = session.query(CodeCommit).order_by(CodeCommit.timestamp).all()
    for commit in commits:
        jira = session.query(JiraItem).filter(JiraItem.id == commit.jira_id).first()
        if jira and jira.completed_date and commit.timestamp < jira.completed_date:
            errors.append(
                f"Commit {commit.id} at {commit.timestamp} happens before Jira {jira.id} completion at {jira.completed_date}"
            )

    return errors


def validate_pr_commit_timeline(session: Session) -> List[str]:
    """Validate that PRs don't start before their associated commits"""
    errors = []

    prs = session.query(PullRequest).order_by(PullRequest.created_at).all()
    for pr in prs:
        if pr.commit_timestamp and pr.created_at < pr.commit_timestamp:
            errors.append(
                f"PR {pr.id} created at {pr.created_at} before its commit at {pr.commit_timestamp}"
            )

    return errors


def validate_cicd_pr_timeline(session: Session) -> List[str]:
    """Validate that CI/CD builds start only after PR completion"""
    errors = []

    cicd_events = session.query(CICDEvent).order_by(CICDEvent.timestamp).all()
    for event in cicd_events:
        # Find associated commits and their PRs
        for commit in event.commits:
            prs = (
                session.query(PullRequest)
                .filter(
                    and_(
                        PullRequest.commit_id == commit.id,
                        PullRequest.commit_timestamp == commit.timestamp,
                    )
                )
                .all()
            )

            for pr in prs:
                if pr.status != PRStatus.MERGED or event.timestamp < pr.merged_at:
                    errors.append(
                        f"CICD event {event.id} at {event.timestamp} started before PR {pr.id} was merged at {pr.merged_at}"
                    )

    return errors


def validate_bug_build_timeline(session: Session) -> List[str]:
    """Validate that P0 bugs and releases only happen after CI/CD build completion"""
    errors = []

    bugs = (
        session.query(Bug).filter(Bug.severity == "P0").order_by(Bug.created_date).all()
    )
    for bug in bugs:
        build = (
            session.query(CICDEvent).filter(CICDEvent.build_id == bug.build_id).first()
        )
        if build and bug.created_date < build.timestamp:
            errors.append(
                f"P0 Bug {bug.id} created at {bug.created_date} before build {build.id} completion at {build.timestamp}"
            )

    return errors


def validate_all_timelines(session: Session) -> Dict[str, List[str]]:
    """Run all timeline validations and return results"""
    return {
        "design_sprint": validate_design_sprint_timeline(session),
        "sprint_jira": validate_sprint_jira_timeline(session),
        "commit_jira": validate_commit_jira_timeline(session),
        "pr_commit": validate_pr_commit_timeline(session),
        "cicd_pr": validate_cicd_pr_timeline(session),
        "bug_build": validate_bug_build_timeline(session),
    }


def verify_temporal_consistency(
    commits: List[Dict[str, Any]],
    cicd_events: List[Dict[str, Any]],
    cicd_commit_map: Dict[str, List[str]],
) -> List[str]:
    """Verify temporal consistency between commits and CICD events"""
    errors = []

    # Create timestamp lookup for commits
    commit_timestamps = {commit["id"]: commit["timestamp"] for commit in commits}

    # Check each CICD event
    for event in cicd_events:
        associated_commits = cicd_commit_map.get(event["id"], [])
        for commit_id in associated_commits:
            if commit_id not in commit_timestamps:
                errors.append(
                    f"CICD event {event['id']} references non-existent commit {commit_id}"
                )
                continue

            commit_time = commit_timestamps[commit_id]
            if commit_time >= event["timestamp"]:
                errors.append(
                    f"Temporal inconsistency: Commit {commit_id} ({commit_time.isoformat()}) "
                    f"is newer than CICD event {event['id']} ({event['timestamp'].isoformat()})"
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

    # Check CICD events
    for event in all_data["cicd_events"]:
        if event["event_id"] not in project_ids:
            errors.append(
                f"CICD event {event['id']} references invalid project {event['event_id']}"
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


def validate_relationships(data: Dict[str, Any]) -> List[str]:
    """Validate all relationships in the generated data"""
    validation_errors = []

    # Validate commits have valid Jira IDs
    jira_ids = set(jira["id"] for jira in data["jira_items"])
    for commit in data["commits"]:
        if commit["jira_id"] not in jira_ids:
            validation_errors.append(
                f"Commit {commit['id']} has invalid jira_id {commit['jira_id']}"
            )

    # Validate bugs have valid Jira IDs and build IDs
    build_ids = set()
    for cicd in data["cicd_events"]:
        if cicd["build_id"]:
            build_ids.add(cicd["build_id"])

    for bug in data["bugs"]:
        if bug["jira_id"] not in jira_ids:
            validation_errors.append(
                f"Bug {bug['id']} has invalid jira_id {bug['jira_id']}"
            )
        if bug["build_id"] not in build_ids:
            validation_errors.append(
                f"Bug {bug['id']} has invalid build_id {bug['build_id']}"
            )

    # Validate sprint-jira associations
    sprint_ids = set(sprint["id"] for sprint in data["sprints"])
    for sprint_id, associated_jiras in data["relationships"][
        "sprint_jira_associations"
    ].items():
        if sprint_id not in sprint_ids:
            validation_errors.append(
                f"Invalid sprint_id {sprint_id} in sprint-jira associations"
            )
        for jira_id in associated_jiras:
            if jira_id not in jira_ids:
                validation_errors.append(
                    f"Invalid jira_id {jira_id} in sprint-jira associations"
                )

    # Validate CICD-commit associations
    commit_ids = set(commit["id"] for commit in data["commits"])
    cicd_ids = set(cicd["id"] for cicd in data["cicd_events"])
    for cicd_id, associated_commits in data["relationships"][
        "cicd_commit_associations"
    ].items():
        if cicd_id not in cicd_ids:
            validation_errors.append(
                f"Invalid cicd_id {cicd_id} in cicd-commit associations"
            )
        for commit_id in associated_commits:
            if commit_id not in commit_ids:
                validation_errors.append(
                    f"Invalid commit_id {commit_id} in cicd-commit associations"
                )

    return validation_errors
