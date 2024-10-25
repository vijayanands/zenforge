# events_entity_generators.py
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import random

import numpy as np

from model.events_data_generation_core import DataGenerator
from model.events_schema import StageType

data_generator = DataGenerator()


def generate_design_related_jiras(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Jira items specifically for design phases"""
    design_jiras = []
    design_phases = data_generator.generate_design_phases()

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        completion_state = details["completion_state"]

        for phase in design_phases:
            jira_id = f"{proj_id}-{phase.upper()}-1"

            # Determine status based on completion state
            if completion_state in ["design_only", "design_and_sprint", "pre_release", "all_complete"]:
                status = "Done"
                completed_date = start_date + timedelta(days=14)
                actual_hours = np.random.randint(16, 32)
            elif completion_state == "mixed":
                status = np.random.choice(["Done", "In Progress"], p=[0.7, 0.3])
                completed_date = start_date + timedelta(days=14) if status == "Done" else None
                actual_hours = np.random.randint(16, 32) if status == "Done" else None
            else:  # mixed_all
                status = np.random.choice(["Done", "In Progress", "To Do"], p=[0.5, 0.3, 0.2])
                completed_date = start_date + timedelta(days=14) if status == "Done" else None
                actual_hours = np.random.randint(16, 32) if status == "Done" else None

            design_jiras.append({
                "id": jira_id,
                "event_id": proj_id,
                "type": "Design",
                "title": f"{phase.replace('_', ' ').title()} Design for {details['title']}",
                "status": status,
                "created_date": start_date,
                "completed_date": completed_date,
                "priority": "High",
                "story_points": np.random.randint(5, 13),
                "assigned_team": f"Team {chr(65 + np.random.randint(0, 3))}",
                "assigned_developer": f"{phase.split('_')[0]}@example.com",
                "estimated_hours": np.random.randint(8, 24),
                "actual_hours": actual_hours
            })

    return design_jiras


def generate_design_events(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate design events for all projects with proper Jira linking and status transitions"""
    design_events = []
    design_phases = data_generator.generate_design_phases()

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        completion_state = details["completion_state"]

        for phase in design_phases:
            phase_status = data_generator.get_design_event_status(completion_state, phase)
            jira_id = f"{proj_id}-{phase.upper()}-1"  # Matches the ID format from generate_design_related_jiras

            # Initial event (START)
            design_events.append({
                "id": f"{proj_id}-{phase.upper()}",
                "event_id": proj_id,
                "design_type": phase,
                "stage": StageType.START,
                "timestamp": start_date,
                "author": f"{phase.split('_')[0]}@example.com",
                "jira": jira_id,
                "stakeholders": data_generator.generate_stakeholders(),
                "review_status": "Pending"
            })

            current_date = start_date + timedelta(days=2)  # Base date for subsequent events

            if phase_status["stage"] != "start":
                if phase_status["stage"] in ["blocked", "resume"]:
                    # Generate blocked-resume cycles
                    num_revisions = np.random.randint(1, 3)
                    days_between_events = np.random.randint(2, 4)  # 2-4 days between status changes

                    for rev_idx in range(num_revisions):
                        # Blocked state
                        design_events.append({
                            "id": f"{proj_id}-{phase.upper()}-BLOCK{rev_idx + 1}",
                            "event_id": proj_id,
                            "design_type": phase,
                            "stage": StageType.BLOCKED,
                            "timestamp": current_date,
                            "author": f"{phase.split('_')[0]}@example.com",
                            "jira": jira_id,
                            "stakeholders": data_generator.generate_stakeholders(),
                            "review_status": "In Review"
                        })
                        current_date += timedelta(days=days_between_events)

                        # Resume state
                        design_events.append({
                            "id": f"{proj_id}-{phase.upper()}-RESUME{rev_idx + 1}",
                            "event_id": proj_id,
                            "design_type": phase,
                            "stage": StageType.RESUME,
                            "timestamp": current_date,
                            "author": f"{phase.split('_')[0]}@example.com",
                            "jira": jira_id,
                            "stakeholders": data_generator.generate_stakeholders(),
                            "review_status": "In Review"
                        })
                        current_date += timedelta(days=days_between_events)

                # Final completion event (END)
                if phase_status["stage"] == "end" or completion_state in ["design_only", "design_and_sprint",
                                                                          "pre_release", "all_complete"]:
                    final_date = max(current_date,
                                     start_date + timedelta(days=7))  # Ensure minimum 7 days for completion
                    design_events.append({
                        "id": f"{proj_id}-{phase.upper()}-FINAL",
                        "event_id": proj_id,
                        "design_type": phase,
                        "stage": StageType.END,
                        "timestamp": final_date,
                        "author": f"{phase.split('_')[0]}@example.com",
                        "jira": jira_id,
                        "stakeholders": data_generator.generate_stakeholders(),
                        "review_status": phase_status["review_status"]
                    })

            # Move start date for next phase
            start_date += timedelta(days=15)  # Each phase starts 15 days after the previous one

    # Sort all events by timestamp to ensure chronological order
    design_events.sort(key=lambda x: (x["event_id"], x["design_type"], x["timestamp"]))

    return design_events


def get_design_event_status(completion_state: str, phase: str) -> Dict[str, Any]:
    """Helper function to get design event status based on completion state"""
    if completion_state in ["design_only", "design_and_sprint", "pre_release", "all_complete"]:
        return {
            "stage": "end",
            "review_status": "Approved"
        }
    elif completion_state == "mixed":
        if np.random.random() < 0.7:
            status = np.random.choice(["end", "blocked"], p=[0.7, 0.3])
            return {
                "stage": status,
                "review_status": "Approved" if status == "end" else "In Review"
            }
        else:
            return {
                "stage": "start",
                "review_status": "Pending"
            }
    else:  # mixed_all
        status = np.random.choice(["start", "end", "blocked"], p=[0.2, 0.5, 0.3])
        return {
            "stage": status,
            "review_status": {
                "start": "Pending",
                "end": "Approved",
                "blocked": "In Review"
            }[status]
        }

def generate_jira_items(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Jira items for all projects, including design, epics, stories and tasks"""
    # First generate design-related Jiras
    all_jiras = generate_design_related_jiras(projects)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        start_date = details["start_date"] + timedelta(days=13)

        # Generate Epics
        for epic_num in range(1, 6):
            status = data_generator.get_jira_status(completion_state)
            epic_completion = start_date + timedelta(days=epic_num + 25) if status == "Done" else None

            epic_id = f"{proj_id}-E{epic_num}"
            epic_data = {
                "id": epic_id,
                "event_id": proj_id,
                "parent_id": None,
                "type": "Epic",
                "title": f"Epic {epic_num} for {details['title']}",
                "status": status,
                "created_date": start_date + timedelta(days=epic_num),
                "completed_date": epic_completion,
                "priority": np.random.choice(["High", "Medium", "Low"]),
                "story_points": np.random.randint(20, 40),
                "assigned_team": f"Team {chr(65 + np.random.randint(0, 3))}",
                "assigned_developer": None,
                "estimated_hours": None,
                "actual_hours": None
            }
            all_jiras.append(epic_data)

            # Generate Stories for Epic
            for story_num in range(1, 6):
                story_status = data_generator.get_jira_status(completion_state)
                story_completion = start_date + timedelta(
                    days=epic_num + story_num + 20) if story_status == "Done" else None
                story_id = f"{epic_id}-S{story_num}"

                story_data = {
                    "id": story_id,
                    "event_id": proj_id,
                    "parent_id": epic_id,
                    "type": "Story",
                    "title": f"Story {story_num} for Epic {epic_num}",
                    "status": story_status,
                    "created_date": start_date + timedelta(days=epic_num + story_num),
                    "completed_date": story_completion,
                    "priority": np.random.choice(["High", "Medium", "Low"]),
                    "story_points": np.random.randint(5, 13),
                    "assigned_team": f"Team {chr(65 + np.random.randint(0, 3))}",
                    "assigned_developer": None,
                    "estimated_hours": None,
                    "actual_hours": None
                }
                all_jiras.append(story_data)

                # Generate Tasks for Story
                for task_num in range(1, 6):
                    task_status = data_generator.get_jira_status(completion_state)
                    estimated_hours = np.random.randint(4, 16)
                    actual_hours = int(estimated_hours * np.random.uniform(0.8, 1.3)) if task_status == "Done" else None
                    task_completion = start_date + timedelta(
                        days=epic_num + story_num + task_num + 15) if task_status == "Done" else None

                    task_data = {
                        "id": f"{story_id}-T{task_num}",
                        "event_id": proj_id,
                        "parent_id": story_id,
                        "type": "Task",
                        "title": f"Task {task_num} for Story {story_num}",
                        "status": task_status,
                        "created_date": start_date + timedelta(days=epic_num + story_num + task_num),
                        "completed_date": task_completion,
                        "priority": np.random.choice(["High", "Medium", "Low"]),
                        "story_points": np.random.randint(1, 5),
                        "assigned_developer": f"dev{np.random.randint(1, 6)}@example.com",
                        "estimated_hours": estimated_hours,
                        "actual_hours": actual_hours,
                    }
                    all_jiras.append(task_data)

                    # Update story and epic completion based on task status
                    if task_status != "Done" and story_data["status"] == "Done":
                        story_data["status"] = "In Progress"
                        story_data["completed_date"] = None
                    if task_status != "Done" and epic_data["status"] == "Done":
                        epic_data["status"] = "In Progress"
                        epic_data["completed_date"] = None

    # For completed projects, ensure all non-design Jiras are marked as Done
    for jira in all_jiras:
        project_details = projects.get(jira["event_id"])
        if project_details and project_details["completion_state"] == "all_complete":
            if jira["type"] != "Design":  # Don't modify design Jiras
                jira["status"] = "Done"
                jira["completed_date"] = jira["created_date"] + timedelta(days=np.random.randint(5, 15))
                if jira["type"] == "Task":
                    jira["actual_hours"] = int(jira["estimated_hours"] * np.random.uniform(0.8, 1.3))

    return all_jiras


def generate_commits(projects: Dict[str, Dict[str, Any]], jira_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate code commits for all projects with Jira associations"""
    commits = []
    commit_types = ["feature", "bugfix", "refactor", "docs", "test"]

    # Create a map of project to available Jira IDs
    project_jiras = {}
    for jira in jira_items:
        if jira['event_id'] not in project_jiras:
            project_jiras[jira['event_id']] = []
        project_jiras[jira['event_id']].append(jira['id'])

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        start_date = details["start_date"] + timedelta(days=20)
        available_jiras = project_jiras.get(proj_id, [])

        if not available_jiras:
            continue

        commit_count = 200 if completion_state in ["pre_release", "all_complete"] else np.random.randint(50, 150)

        for i in range(commit_count):
            commit_date = start_date + timedelta(days=i // 4)
            commit_metrics = data_generator.get_commit_status(completion_state)

            # Assign a random Jira ID from the project
            associated_jira = random.choice(available_jiras)

            files_changed, lines_added, lines_removed, _, _ = data_generator.generate_commit_metrics()

            commits.append({
                "id": data_generator.generate_unique_id("commit_"),
                "event_id": proj_id,
                "jira_id": associated_jira,  # New field
                "timestamp": commit_date,
                "repository": f"{proj_id.lower()}-repo",
                "branch": f"feature/sprint-{i // 40 + 1}",
                "author": f"dev{i % 5 + 1}@example.com",
                "commit_hash": uuid.uuid4().hex[:8],
                "files_changed": files_changed,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "code_coverage": commit_metrics["code_coverage"],
                "lint_score": commit_metrics["lint_score"],
                "commit_type": np.random.choice(commit_types, p=[0.4, 0.3, 0.15, 0.1, 0.05]),
                "review_time_minutes": commit_metrics["review_time_minutes"],
                "comments_count": np.random.randint(0, 10),
                "approved_by": f"reviewer{np.random.randint(1, 4)}@example.com"
            })

    return commits


def generate_cicd_events(projects: Dict[str, Dict[str, Any]], commits: List[Dict[str, Any]]) -> Tuple[
    List[Dict[str, Any]], Dict[str, List[str]]]:
    """Generate CI/CD events for all projects with commit associations"""
    cicd_events = []
    environments = ["dev", "staging", "qa", "uat", "production"]

    # Create a map of project to available commits
    project_commits = {}
    for commit in commits:
        if commit['event_id'] not in project_commits:
            project_commits[commit['event_id']] = []
        project_commits[commit['event_id']].append(commit['id'])

    # Track build IDs to ensure uniqueness
    used_build_ids = set()

    # Will store CICD to commit associations
    cicd_commit_map = {}

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        deploy_start = details["start_date"] + timedelta(days=25)
        available_commits = project_commits.get(proj_id, [])

        if not available_commits:
            continue

        for i in range(50):
            deploy_date = deploy_start + timedelta(days=i)

            for env in environments:
                cicd_status = data_generator.get_cicd_status(completion_state)

                # Create unique build ID
                while True:
                    build_id = data_generator.generate_unique_id("build_")
                    if build_id not in used_build_ids:
                        used_build_ids.add(build_id)
                        break

                build_success = cicd_status["status"] == "success"

                # Associate commits with this build
                associated_commits = data_generator.get_random_commit_ids(
                    available_commits,
                    min_count=1,
                    max_count=5
                )

                # Build event
                build_event_id = data_generator.generate_unique_id("cicd_")
                build_event = {
                    "id": build_event_id,
                    "event_id": proj_id,
                    "timestamp": deploy_date,
                    "environment": env,
                    "event_type": "build",
                    "build_id": build_id,
                    "status": cicd_status["status"],
                    "duration_seconds": np.random.randint(180, 900),
                    "metrics": cicd_status["metrics"],
                    "reason": None
                }
                cicd_events.append(build_event)
                cicd_commit_map[build_event_id] = associated_commits

                if build_success:
                    deploy_success = completion_state in ["pre_release", "all_complete"]

                    # Deployment event
                    deploy_event_id = data_generator.generate_unique_id("cicd_")
                    deploy_event = {
                        "id": deploy_event_id,
                        "event_id": proj_id,
                        "timestamp": deploy_date + timedelta(minutes=15),
                        "environment": env,
                        "event_type": "deployment",
                        "build_id": data_generator.generate_unique_id("build_"),  # New unique build ID for deployment
                        "status": "success" if deploy_success else "failed",
                        "duration_seconds": np.random.randint(300, 1200),
                        "metrics": cicd_status["metrics"],
                        "reason": None
                    }
                    cicd_events.append(deploy_event)
                    cicd_commit_map[deploy_event_id] = associated_commits

                    if not deploy_success:
                        rollback_reasons = [
                            "Performance degradation",
                            "Critical bug found",
                            "Integration test failure",
                            "Database migration issue",
                            "Memory leak detected",
                            "API compatibility issue"
                        ]

                        # Rollback event
                        rollback_event_id = data_generator.generate_unique_id("cicd_")
                        rollback_event = {
                            "id": rollback_event_id,
                            "event_id": proj_id,
                            "timestamp": deploy_date + timedelta(minutes=30),
                            "environment": env,
                            "event_type": "rollback",
                            "build_id": data_generator.generate_unique_id("build_"),  # New unique build ID for rollback
                            "status": "success",
                            "reason": np.random.choice(rollback_reasons),
                            "duration_seconds": np.random.randint(180, 600),
                            "metrics": cicd_status["metrics"]
                        }
                        cicd_events.append(rollback_event)
                        cicd_commit_map[rollback_event_id] = associated_commits

    return cicd_events, cicd_commit_map

def generate_bugs(projects: Dict[str, Dict[str, Any]],
                  jira_items: List[Dict[str, Any]],
                  cicd_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate bugs for all projects with Jira and CICD associations"""
    bugs = []
    bug_types = ["Security", "Performance", "Functionality", "Data", "UI/UX"]
    impact_areas = ["Customer", "Internal", "Integration", "Infrastructure"]

    # Create maps for available Jiras and build IDs by project
    project_jiras = {}
    for jira in jira_items:
        if jira['event_id'] not in project_jiras:
            project_jiras[jira['event_id']] = []
        project_jiras[jira['event_id']].append(jira['id'])

    build_ids_by_project = data_generator.get_build_ids_by_project(cicd_events)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]

        # Skip P0 bugs for all_complete state
        if completion_state == "all_complete":
            continue

        available_jiras = project_jiras.get(proj_id, [])
        available_builds = build_ids_by_project.get(proj_id, [])

        if not available_jiras or not available_builds:
            continue

        bug_start = details["start_date"] + timedelta(days=30)
        num_bugs = np.random.randint(5, 15)

        for i in range(num_bugs):
            bug_date = bug_start + timedelta(days=i * 2)
            resolution_time = np.random.randint(4, 72)

            status = "Fixed" if completion_state in ["pre_release", "all_complete"] else \
                np.random.choice(["Fixed", "In Progress", "Open"], p=[0.6, 0.3, 0.1])

            # Associate with a random Jira and build ID
            associated_jira = random.choice(available_jiras)
            associated_build = random.choice(available_builds)

            bugs.append({
                "id": f"{proj_id}-BUG-{i + 1}",
                "event_id": proj_id,
                "jira_id": associated_jira,
                "build_id": associated_build,
                "bug_type": np.random.choice(bug_types),
                "impact_area": np.random.choice(impact_areas),
                "severity": "P0",
                "title": f"Critical bug in {details['title']}",
                "status": status,
                "created_date": bug_date,
                "resolved_date": bug_date + timedelta(hours=resolution_time) if status == "Fixed" else None,
                "resolution_time_hours": resolution_time if status == "Fixed" else None,
                "assigned_to": f"dev{np.random.randint(1, 6)}@example.com",
                "environment_found": np.random.choice(["Production", "Staging", "QA"]),
                "number_of_customers_affected": np.random.randint(1, 1000) if np.random.random() > 0.5 else 0,
                "root_cause": data_generator.generate_root_cause(),
                "fix_version": f"{proj_id.lower()}-v1.{np.random.randint(0, 9)}.{np.random.randint(0, 9)}",
                "regression_test_status": "Passed" if status == "Fixed" else "In Progress",
                "customer_communication_needed": np.random.choice([True, False]),
                "postmortem_link": f"https://wiki.example.com/postmortem/{proj_id}-BUG-{i + 1}" if status == "Fixed" else None
            })

    return bugs


def generate_sprints(projects: Dict[str, Dict[str, Any]], jira_items: List[Dict[str, Any]]) -> Tuple[
    List[Dict[str, Any]], Dict[str, List[str]]]:
    """Generate sprints for all projects with Jira associations"""
    sprints = []
    sprint_jira_map = {}

    # Group jiras by project
    project_jiras = {}
    for jira in jira_items:
        if jira['event_id'] not in project_jiras:
            project_jiras[jira['event_id']] = []
        project_jiras[jira['event_id']].append(jira)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        sprint_start = details["start_date"] + timedelta(days=14)
        project_completion = details["start_date"] + timedelta(weeks=12)  # Assuming 12 weeks project duration

        available_jiras = project_jiras.get(proj_id, [])
        unassigned_jiras = set(jira['id'] for jira in available_jiras)

        for sprint_num in range(1, 9):
            sprint_id = f"{proj_id}-Sprint-{sprint_num}"
            sprint_start_date = sprint_start + timedelta(days=(sprint_num - 1) * 14)
            sprint_end_date = sprint_start_date + timedelta(days=14)

            # Determine completion based on project state
            is_completed = completion_state in ["design_and_sprint", "pre_release", "all_complete"] or \
                           (completion_state in ["mixed", "mixed_all"] and np.random.random() < 0.7)

            # Filter jiras that can be included in this sprint
            eligible_jiras = [
                jira['id'] for jira in available_jiras
                if jira['id'] in unassigned_jiras and
                jira['created_date'] <= sprint_end_date and
                (not jira.get('completed_date') or jira['completed_date'] >= sprint_start_date)
            ]

            # Assign jiras to sprint based on completion state
            sprint_jiras = []
            if eligible_jiras:
                # Determine number of jiras to assign
                if completion_state == "all_complete" and sprint_num == 8:
                    # Assign all remaining jiras for completed projects in final sprint
                    sprint_jiras = list(unassigned_jiras)
                else:
                    num_jiras = random.randint(
                        min(3, len(eligible_jiras)),
                        min(8, len(eligible_jiras))
                    )
                    sprint_jiras = random.sample(eligible_jiras, num_jiras)

                # Update unassigned jiras set
                unassigned_jiras -= set(sprint_jiras)

            # Calculate metrics based on assigned jiras
            sprint_jiras_data = [j for j in available_jiras if j['id'] in sprint_jiras]
            planned_story_points = sum(j['story_points'] for j in sprint_jiras_data)
            completed_story_points = int(
                planned_story_points * (np.random.uniform(0.9, 1.1) if is_completed else np.random.uniform(0.5, 0.8))
            )

            planned_stories = len(sprint_jiras)
            completed_stories = int(
                planned_stories * (np.random.uniform(0.9, 1.0) if is_completed else np.random.uniform(0.5, 0.8))
            )

            sprint_data = {
                "id": sprint_id,
                "event_id": proj_id,
                "start_date": sprint_start_date,
                "end_date": sprint_end_date,
                "planned_story_points": planned_story_points,
                "completed_story_points": completed_story_points,
                "planned_stories": planned_stories,
                "completed_stories": completed_stories,
                "team_velocity": completed_story_points,
                "burndown_efficiency": np.random.uniform(0.9, 1.1) if is_completed else np.random.uniform(0.6, 0.9),
                "sprint_goals": f"Complete features for {details['title']} phase {sprint_num}",
                "retrospective_summary": np.random.choice([
                    "Improved team collaboration",
                    "Technical debt addressed",
                    "Communication challenges identified",
                    "Process improvements implemented",
                    "Knowledge sharing enhanced"
                ]),
                "blockers_encountered": np.random.randint(0, 2) if is_completed else np.random.randint(2, 5),
                "team_satisfaction_score": np.random.uniform(8, 10) if is_completed else np.random.uniform(6, 8),
                "status": "Completed" if is_completed else "In Progress"
            }
            sprints.append(sprint_data)

            # Update sprint_jira_map if we have associations
            if sprint_jiras:
                sprint_jira_map[sprint_id] = sprint_jiras

        # For completed projects, ensure all Jiras are assigned to a sprint
        if completion_state == "all_complete" and unassigned_jiras:
            # Assign remaining Jiras to the last sprint
            last_sprint_id = f"{proj_id}-Sprint-8"
            if last_sprint_id not in sprint_jira_map:
                sprint_jira_map[last_sprint_id] = []
            sprint_jira_map[last_sprint_id].extend(list(unassigned_jiras))

    return sprints, sprint_jira_map


def update_jiras_with_sprints(jira_items: List[Dict[str, Any]], sprint_jira_map: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Update jira items with their sprint assignments"""
    # Create reverse mapping of jira_id to sprint_id
    jira_to_sprint = {}
    for sprint_id, jira_ids in sprint_jira_map.items():
        for jira_id in jira_ids:
            jira_to_sprint[jira_id] = sprint_id

    # Update jira items with sprint information
    updated_jiras = []
    for jira in jira_items:
        jira_copy = jira.copy()
        jira_copy['sprint_id'] = jira_to_sprint.get(jira['id'])
        updated_jiras.append(jira_copy)

    return updated_jiras

def generate_team_metrics(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate team metrics for all projects"""
    team_metrics = []

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        start_date = details["start_date"]

        for week in range(12):
            week_start = start_date + timedelta(weeks=week)

            # Adjust metrics based on completion state
            is_mature = completion_state in ["pre_release", "all_complete"] or \
                        (completion_state in ["design_and_sprint", "mixed_all"] and week > 6)

            team_metrics.append({
                "id": f"{proj_id}-TM-{week + 1}",
                "event_id": proj_id,
                "week_starting": week_start,
                "team_size": details["team_size"],
                "velocity": np.random.randint(30, 40) if is_mature else np.random.randint(20, 30),
                "code_review_turnaround_hours": np.random.uniform(2, 24) if is_mature else np.random.uniform(24, 48),
                "build_success_rate": np.random.uniform(95, 100) if is_mature else np.random.uniform(85, 95),
                "test_coverage": np.random.uniform(85, 95) if is_mature else np.random.uniform(75, 85),
                "bugs_reported": np.random.randint(1, 5) if is_mature else np.random.randint(5, 10),
                "bugs_fixed": np.random.randint(3, 8) if is_mature else np.random.randint(1, 5),
                "technical_debt_hours": np.random.randint(5, 20) if is_mature else np.random.randint(20, 40),
                "pair_programming_hours": np.random.randint(10, 20) if is_mature else np.random.randint(5, 10),
                "code_review_comments": np.random.randint(20, 50) if is_mature else np.random.randint(50, 100),
                "documentation_updates": np.random.randint(5, 8) if is_mature else np.random.randint(2, 5),
                "knowledge_sharing_sessions": np.random.randint(2, 3) if is_mature else np.random.randint(1, 2),
                "team_satisfaction": np.random.uniform(8, 9.5) if is_mature else np.random.uniform(7, 8),
                "sprint_completion_rate": np.random.uniform(90, 100) if is_mature else np.random.uniform(70, 90)
            })

    return team_metrics


def generate_all_data() -> Dict[str, Any]:
    """Generate all data for the application with new relationships"""
    # Generate base project data
    projects = data_generator.generate_project_base_data()

    # Generate project details
    project_details = data_generator.generate_project_details(projects)

    # Generate design events
    design_events = generate_design_events(projects)

    # Generate Jira items first as they're needed for relationships
    jira_items = generate_jira_items(projects)

    # Generate commits with Jira associations
    commits = generate_commits(projects, jira_items)

    # Generate CICD events with commit associations
    cicd_events, cicd_commit_map = generate_cicd_events(projects, commits)

    # Generate bugs with Jira and CICD associations
    bugs = generate_bugs(projects, jira_items, cicd_events)

    # Generate sprints with Jira associations
    sprints, sprint_jira_map = generate_sprints(projects, jira_items)

    # Generate team metrics
    team_metrics = generate_team_metrics(projects)

    # Combine all data
    all_data = {
        "projects": project_details,
        "design_events": design_events,
        "jira_items": jira_items,
        "commits": commits,
        "cicd_events": cicd_events,
        "bugs": bugs,
        "sprints": sprints,
        "team_metrics": team_metrics,
        "relationships": {
            "sprint_jira_associations": sprint_jira_map,
            "cicd_commit_associations": cicd_commit_map
        }
    }

    return all_data


def validate_relationships(data: Dict[str, Any]) -> List[str]:
    """Validate all relationships in the generated data"""
    validation_errors = []

    # Validate commits have valid Jira IDs
    jira_ids = set(jira["id"] for jira in data["jira_items"])
    for commit in data["commits"]:
        if commit["jira_id"] not in jira_ids:
            validation_errors.append(f"Commit {commit['id']} has invalid jira_id {commit['jira_id']}")

    # Validate bugs have valid Jira IDs and build IDs
    build_ids = set()
    for cicd in data["cicd_events"]:
        if cicd["build_id"]:
            build_ids.add(cicd["build_id"])

    for bug in data["bugs"]:
        if bug["jira_id"] not in jira_ids:
            validation_errors.append(f"Bug {bug['id']} has invalid jira_id {bug['jira_id']}")
        if bug["build_id"] not in build_ids:
            validation_errors.append(f"Bug {bug['id']} has invalid build_id {bug['build_id']}")

    # Validate sprint-jira associations
    sprint_ids = set(sprint["id"] for sprint in data["sprints"])
    for sprint_id, associated_jiras in data["relationships"]["sprint_jira_associations"].items():
        if sprint_id not in sprint_ids:
            validation_errors.append(f"Invalid sprint_id {sprint_id} in sprint-jira associations")
        for jira_id in associated_jiras:
            if jira_id not in jira_ids:
                validation_errors.append(f"Invalid jira_id {jira_id} in sprint-jira associations")

    # Validate CICD-commit associations
    commit_ids = set(commit["id"] for commit in data["commits"])
    cicd_ids = set(cicd["id"] for cicd in data["cicd_events"])
    for cicd_id, associated_commits in data["relationships"]["cicd_commit_associations"].items():
        if cicd_id not in cicd_ids:
            validation_errors.append(f"Invalid cicd_id {cicd_id} in cicd-commit associations")
        for commit_id in associated_commits:
            if commit_id not in commit_ids:
                validation_errors.append(f"Invalid commit_id {commit_id} in cicd-commit associations")

    return validation_errors


def get_sample_data() -> Dict[str, Any]:
    """Helper function to get sample data with validation"""
    # Generate base project data
    projects = data_generator.generate_project_base_data()
    project_details = data_generator.generate_project_details(projects)

    # Generate other data
    design_events = generate_design_events(projects)
    jira_items = generate_jira_items(projects)
    commits = generate_commits(projects, jira_items)
    cicd_events, cicd_commit_map = generate_cicd_events(projects, commits)
    bugs = generate_bugs(projects, jira_items, cicd_events)
    sprints, sprint_jira_map = generate_sprints(projects, jira_items)

    # No need to modify jira items with sprint information since we're using a junction table

    team_metrics = generate_team_metrics(projects)

    all_data = {
        "projects": project_details,
        "design_events": design_events,
        "jira_items": jira_items,
        "commits": commits,
        "cicd_events": cicd_events,
        "bugs": bugs,
        "sprints": sprints,
        "team_metrics": team_metrics,
        "relationships": {
            "sprint_jira_associations": sprint_jira_map,
            "cicd_commit_associations": cicd_commit_map
        }
    }

    validation_errors = validate_relationships(all_data)
    if validation_errors:
        print("Validation errors found:")
        for error in validation_errors:
            print(f"- {error}")

    return all_data


def write_sample_data(filename: str = "sample_data.json") -> None:
    """Write sample data to a JSON file"""
    data = get_sample_data()
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Sample data written to {filename}")


if __name__ == "__main__":
    write_sample_data()

