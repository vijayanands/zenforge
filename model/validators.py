from typing import Any, Dict, List

from sqlalchemy.orm import Session

from model.sdlc_events import (
    BugStatus,
    BuildMode,
    BuildStatus,
    CICDEvent,
    CodeCommit,
    DesignEvent,
    Environment,
    JiraItem,
    PRStatus,
    PullRequest,
    Sprint,
    sprint_jira_association,
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
        "jira_hierarchy": validate_jira_date_hierarchy(session),
        "cicd_timeline": validate_cicd_event_timeline(session),
    }


def validate_cicd_event_timeline(session: Session) -> List[str]:
    """
    Validate CICD event timelines:
    1. Automatic builds must start after their associated PR merge time
    2. Events must have valid environment progression
    3. Build durations must be positive
    """
    errors = []

    # Get all CICD events
    cicd_events = session.query(CICDEvent).order_by(CICDEvent.timestamp).all()

    # Get all PRs for reference
    prs = {pr.id: pr for pr in session.query(PullRequest).all()}

    # Track environment progression for each PR/manual build
    env_order = {
        Environment.DEV: 0,
        Environment.QA: 1,
        Environment.STAGING: 2,
        Environment.UAT: 3,
        Environment.PRODUCTION: 4,
    }

    build_env_progress = {}

    for event in cicd_events:
        # Validate build duration
        if event.duration_seconds <= 0:
            errors.append(
                f"CICD event {event.build_id} has invalid duration: {event.duration_seconds}"
            )

        # Validate automatic builds against PR merge times
        if event.mode == BuildMode.AUTOMATIC:
            pr = prs.get(event.event_id)
            if pr and pr.merged_at:
                if event.timestamp <= pr.merged_at:
                    errors.append(
                        f"CICD event {event.build_id} timestamp ({event.timestamp}) "
                        f"is before its PR merge time ({pr.merged_at})"
                    )

        # Track environment progression
        if event.event_id not in build_env_progress:
            build_env_progress[event.event_id] = env_order[event.environment]
        else:
            # Environment can stay the same or go up, but not go down
            if env_order[event.environment] < build_env_progress[event.event_id]:
                errors.append(
                    f"CICD event {event.build_id} has invalid environment progression: "
                    f"went from higher environment to {event.environment.value}"
                )
            build_env_progress[event.event_id] = max(
                build_env_progress[event.event_id], env_order[event.environment]
            )

    return errors


def validate_cicd_relationships(data: Dict[str, Any]) -> List[str]:
    """Validate relationships between CICD events and other entities"""
    errors = []

    # Get relevant data
    cicd_events = data.get("cicd_events", [])
    pull_requests = {pr["id"]: pr for pr in data.get("pull_requests", [])}
    project_ids = {proj["id"] for proj in data.get("projects", [])}

    for event in cicd_events:
        # Validate project_id exists
        if event["project_id"] not in project_ids:
            errors.append(
                f"CICD event {event['build_id']} references non-existent project {event['project_id']}"
            )

            if event["mode"] == BuildMode.AUTOMATIC.value:
                # Validate PR references for automatic builds
                pr = pull_requests.get(event["event_id"])
                if not pr:
                    errors.append(
                        f"CICD event {event['build_id']} references non-existent PR {event['event_id']}"
                    )
                elif pr["status"] != PRStatus.MERGED.value:
                    errors.append(
                        f"CICD event {event['build_id']} references non-merged PR {event['event_id']}"
                    )
                # Validate project_id matches PR's project_id
                elif pr["project_id"] != event["project_id"]:
                    errors.append(
                        f"CICD event {event['build_id']} project_id ({event['project_id']}) "
                        f"doesn't match PR project_id ({pr['project_id']})"
                    )

                # Validate branch matches PR's target branch
                if pr and event["branch"] != pr["branch_to"]:
                    errors.append(
                        f"CICD event {event['build_id']} branch ({event['branch']}) "
                        f"doesn't match PR target branch ({pr['branch_to']})"
                    )

        return errors


def validate_bug_build_association(
    bugs: List[Dict[str, Any]], cicd_events: List[Dict[str, Any]]
) -> List[str]:
    """Validate that bugs are only associated with successful builds"""
    errors = []

    # Create a map of successful builds
    successful_builds = {
        event["build_id"]: event
        for event in cicd_events
        if event["status"] == BuildStatus.SUCCESS.value
    }

    for bug in bugs:
        if bug["build_id"] not in successful_builds:
            errors.append(
                f"Bug {bug['id']} is associated with non-successful or non-existent build {bug['build_id']}"
            )
        else:
            build = successful_builds[bug["build_id"]]
            if bug["environment_found"] != build["environment"]:
                errors.append(
                    f"Bug {bug['id']} environment doesn't match build environment"
                )
            if bug["release_id"] != build["release_version"]:
                errors.append(
                    f"Bug {bug['id']} release version doesn't match build release version"
                )

    return errors


def validate_bug_data(bug_data: Dict[str, Any]) -> List[str]:
    """Validate bug data before creation"""
    errors = []

    # Validate dates
    if bug_data.get("resolved_date"):
        if bug_data["resolved_date"] <= bug_data["created_date"]:
            errors.append("Resolved date must be after created date")

    if bug_data.get("close_date"):
        if not bug_data.get("resolved_date"):
            errors.append("Bug cannot have close date without resolved date")
        elif bug_data["close_date"] <= bug_data["resolved_date"]:
            errors.append("Close date must be after resolved date")

    # Validate resolution time
    if bug_data.get("resolution_time_hours"):
        if not bug_data.get("resolved_date"):
            errors.append("Resolution time cannot be set without resolved date")
        else:
            time_diff = (
                bug_data["resolved_date"] - bug_data["created_date"]
            ).total_seconds() / 3600
            if bug_data["resolution_time_hours"] > time_diff:
                errors.append(
                    "Resolution time cannot be greater than time between creation and resolution"
                )

    # Validate status transitions
    if bug_data["status"] == BugStatus.CLOSED and not bug_data.get("close_date"):
        errors.append("Closed status requires close date")
    if bug_data["status"] == BugStatus.FIXED and not bug_data.get("resolved_date"):
        errors.append("Fixed status requires resolved date")

    return errors


def validate_bug_timelines(
    bugs: List[Dict[str, Any]], cicd_events: List[Dict[str, Any]]
) -> List[str]:
    """Validate temporal consistency of bugs with respect to their associated builds"""
    errors = []

    # Create a map of builds for quick lookup
    builds = {event["build_id"]: event for event in cicd_events}

    for bug in bugs:
        build = builds.get(bug["build_id"])
        if not build:
            continue

        # Bug must be created after its associated build
        if bug["created_date"] <= build["timestamp"]:
            errors.append(
                f"Bug {bug['id']} created at {bug['created_date']} before its "
                f"associated build {build['build_id']} at {build['timestamp']}"
            )

        # Validate resolution timeline
        if bug["resolved_date"]:
            if bug["resolved_date"] <= bug["created_date"]:
                errors.append(
                    f"Bug {bug['id']} resolved at {bug['resolved_date']} before "
                    f"its creation at {bug['created_date']}"
                )

            # Validate resolution time against actual time difference
            time_diff = (
                bug["resolved_date"] - bug["created_date"]
            ).total_seconds() / 3600
            if bug["resolution_time_hours"] > time_diff:
                errors.append(
                    f"Bug {bug['id']} resolution time ({bug['resolution_time_hours']} hours) "
                    f"greater than actual time difference ({time_diff:.2f} hours)"
                )

        # Validate closure timeline
        if bug["close_date"]:
            if not bug["resolved_date"]:
                errors.append(f"Bug {bug['id']} has close date but no resolution date")
            elif bug["close_date"] <= bug["resolved_date"]:
                errors.append(
                    f"Bug {bug['id']} closed at {bug['close_date']} before "
                    f"resolution at {bug['resolved_date']}"
                )

    return errors
