from typing import Any, Dict, List

from sqlalchemy.orm import Session

from model.sdlc_events import (
    CICDEvent,
    CodeCommit,
    DesignEvent,
    JiraItem,
    PRStatus,
    PullRequest,
    Sprint,
    sprint_jira_association,
    Bug,
)


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


def validate_commit_jira_completion_dates(data: Dict[str, Any]) -> List[str]:
    """
    Validate that all commit timestamps are after their associated Jira completion dates.

    Args:
        data (Dict[str, Any]): Dictionary containing 'commits' and 'jira_items' lists

    Returns:
        List[str]: List of validation error messages
    """
    errors = []

    # Create a map of Jira completion dates
    jira_completion_dates = {
        jira["id"]: jira.get("completed_date") for jira in data["jira_items"]
    }

    # Check each commit
    for commit in data["commits"]:
        jira_id = commit["jira_id"]
        commit_timestamp = commit["timestamp"]
        jira_completion_date = jira_completion_dates.get(jira_id)

        # Validate the temporal relationship
        if jira_completion_date is None:
            errors.append(
                f"Commit {commit['id']} references Jira {jira_id} which has no completion date"
            )
        elif commit_timestamp <= jira_completion_date:
            errors.append(
                f"Commit {commit['id']} timestamp ({commit_timestamp}) is not after "
                f"its associated Jira {jira_id} completion date ({jira_completion_date})"
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
    """Validate CICD build timestamps against PR merge times"""
    errors = []

    cicd_events = session.query(CICDEvent).filter(CICDEvent.pr_id.isnot(None)).all()

    for event in cicd_events:
        pr = session.query(PullRequest).filter(PullRequest.id == event.pr_id).first()
        if pr and pr.status == PRStatus.MERGED:
            if event.timestamp <= pr.merged_at:
                errors.append(
                    f"CICD event {event.id} at {event.timestamp} started before "
                    f"its associated PR {pr.id} was merged at {pr.merged_at}"
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

    return validation_errors


def validate_jira_date_hierarchy(session: Session) -> List[str]:
    """
    Validate JIRA item date hierarchies:
    1. Epics must start after their sprint start date
    2. Stories must start after their parent epic start date
    3. Tasks must start after their parent story start date

    Args:
        session: SQLAlchemy session

    Returns:
        List of validation error messages
    """
    errors = []

    # Get all sprints for reference
    sprints = {sprint.id: sprint for sprint in session.query(Sprint).all()}

    # Get all JIRA items
    jiras = session.query(JiraItem).all()

    # Create maps for quick lookup
    jira_map = {jira.id: jira for jira in jiras}

    # Create sprint-jira map from the association table
    sprint_jira_map = {}
    for assoc in session.query(sprint_jira_association).all():
        if assoc.sprint_id not in sprint_jira_map:
            sprint_jira_map[assoc.sprint_id] = []
        sprint_jira_map[assoc.sprint_id].append(assoc.jira_id)

    # Validate each JIRA item
    for jira in jiras:
        if jira.type == "Epic":
            # Find associated sprint(s)
            for sprint_id, jira_ids in sprint_jira_map.items():
                if jira.id in jira_ids:
                    sprint = sprints.get(sprint_id)
                    if sprint and jira.created_date < sprint.start_date:
                        errors.append(
                            f"Epic {jira.id} starts at {jira.created_date} before "
                            f"its sprint {sprint_id} which starts at {sprint.start_date}"
                        )

        elif jira.type == "Story":
            # Validate against parent epic
            parent_epic = jira_map.get(jira.parent_id)
            if parent_epic:
                if jira.created_date < parent_epic.created_date:
                    errors.append(
                        f"Story {jira.id} starts at {jira.created_date} before "
                        f"its parent epic {parent_epic.id} which starts at {parent_epic.created_date}"
                    )

                # Also check sprint dates for stories
                for sprint_id, jira_ids in sprint_jira_map.items():
                    if jira.id in jira_ids:
                        sprint = sprints.get(sprint_id)
                        if sprint and jira.created_date < sprint.start_date:
                            errors.append(
                                f"Story {jira.id} starts at {jira.created_date} before "
                                f"its sprint {sprint_id} which starts at {sprint.start_date}"
                            )

        elif jira.type == "Task":
            # Validate against parent story
            parent_story = jira_map.get(jira.parent_id)
            if parent_story:
                if jira.created_date < parent_story.created_date:
                    errors.append(
                        f"Task {jira.id} starts at {jira.created_date} before "
                        f"its parent story {parent_story.id} which starts at {parent_story.created_date}"
                    )

                # Also check sprint dates for tasks
                for sprint_id, jira_ids in sprint_jira_map.items():
                    if jira.id in jira_ids:
                        sprint = sprints.get(sprint_id)
                        if sprint and jira.created_date < sprint.start_date:
                            errors.append(
                                f"Task {jira.id} starts at {jira.created_date} before "
                                f"its sprint {sprint_id} which starts at {sprint.start_date}"
                            )

        # Validate completion dates if they exist
        if jira.completed_date and jira.completed_date < jira.created_date:
            errors.append(
                f"JIRA {jira.id} has completion date {jira.completed_date} "
                f"before its start date {jira.created_date}"
            )

    return errors


def validate_all_timelines(session: Session) -> Dict[str, List[str]]:
    """Run all timeline validations and return results"""
    return {
        "design_sprint": validate_design_sprint_timeline(session),
        "sprint_jira": validate_sprint_jira_timeline(session),
        "commit_jira": validate_commit_jira_timeline(session),
        "commit_jira_completion": validate_commit_jira_completion_dates(
            {
                "commits": session.query(CodeCommit).all(),
                "jira_items": session.query(JiraItem).all(),
            }
        ),  # Added new validation
        "pr_commit": validate_pr_commit_timeline(session),
        "cicd_pr": validate_cicd_pr_timeline(session),
        "bug_build": validate_bug_build_timeline(session),
        "jira_hierarchy": validate_jira_date_hierarchy(session),
    }
