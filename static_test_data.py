import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from model.sdlc_events import (
    PRStatus,
    StageType,
    create_bug,
    create_cicd_event,
    create_commit,
    create_design_event,
    create_jira_item,
    create_pr_comment,
    create_project,
    create_pull_request,
    create_sprint,
    create_sprint_jira_associations,
    create_team_metrics,
)


def generate_and_load_static_data():
    """Generate comprehensive static data with proper constraints and unique IDs"""

    base_date = datetime(2024, 1, 1)
    project_id = "PRJ-001"
    created_jira_ids = set()  # Track created IDs

    # Project Data (12-week duration)
    project_data = {
        "id": project_id,
        "title": "Customer Portal Redesign",
        "description": "Modernize customer portal with improved UX and self-service capabilities",
        "start_date": base_date,
        "status": "In Progress",
        "complexity": "High",
        "team_size": 8,
        "estimated_duration_weeks": 12,
        "budget_allocated": 250000,
        "priority": "High",
    }
    create_project(project_data)

    # Design Phase (Weeks 1-2)
    design_phases = [
        ("requirements", "Requirements Gathering and Analysis"),
        ("architecture", "System Architecture Design"),
        ("database", "Database Schema Design"),
        ("api", "API Interface Design"),
        ("security", "Security Architecture Review"),
        ("ux", "User Experience Design"),
    ]

    design_jiras = []
    for phase_idx, (phase_id, phase_title) in enumerate(design_phases, 1):
        jira_id = f"{project_id}-DESIGN-{phase_idx}"
        if jira_id in created_jira_ids:
            continue

        created_jira_ids.add(jira_id)
        design_jira = {
            "id": jira_id,
            "event_id": project_id,
            "parent_id": None,
            "type": "Design",
            "title": phase_title,
            "status": "Done",
            "created_date": base_date,
            "completed_date": base_date + timedelta(days=14),
            "priority": "High",
            "story_points": random.randint(8, 13),
            "assigned_team": "Team A",
            "assigned_developer": f"{phase_id}@example.com",
            "estimated_hours": random.randint(30, 50),
            "actual_hours": random.randint(35, 55),
        }
        create_jira_item(design_jira)
        design_jiras.append(design_jira)

        # Design events (START -> BLOCKED -> RESUME -> END pattern)
        event_sequence = [
            (StageType.START, "In Review", 0),
            (StageType.BLOCKED, "Needs Changes", 2),
            (StageType.RESUME, "In Review", 3),
            (StageType.END, "Approved", 4),
        ]

        for stage, status, day_offset in event_sequence:
            create_design_event(
                {
                    "id": f"{jira_id}-{stage.value}",
                    "event_id": project_id,
                    "timestamp": base_date + timedelta(days=day_offset),
                    "design_type": phase_id,
                    "stage": stage,
                    "author": f"{phase_id}@example.com",
                    "jira": jira_id,
                    "stakeholders": "Product,Dev,Arch,Security",
                    "review_status": status,
                }
            )

    # Create Epics, Stories and Tasks
    epics = [
        ("Authentication", "Implement secure user authentication system"),
        ("Dashboard", "Create customizable user dashboard"),
        ("Reporting", "Generate detailed activity reports"),
        ("Integration", "Third-party system integration"),
        ("Admin", "Administrative control panel"),
    ]

    all_jiras = []
    story_points_per_sprint = []  # Track points for burndown

    for epic_idx, (epic_name, epic_desc) in enumerate(epics, 1):
        epic_id = f"{project_id}-EPIC-{epic_idx}"
        if epic_id in created_jira_ids:
            continue

        created_jira_ids.add(epic_id)
        epic = {
            "id": epic_id,
            "event_id": project_id,
            "parent_id": None,
            "type": "Epic",
            "title": f"Epic: {epic_name} - {epic_desc}",
            "status": "In Progress",
            "created_date": base_date + timedelta(days=15),
            "completed_date": None,
            "priority": "High",
            "story_points": 0,
            "assigned_team": "Team A",
            "assigned_developer": None,
            "estimated_hours": None,
            "actual_hours": None,
        }
        create_jira_item(epic)
        all_jiras.append(epic)

        # Create 3-5 stories per epic
        num_stories = random.randint(3, 5)
        sprint_story_points = 0

        for story_idx in range(1, num_stories + 1):
            story_id = f"{epic_id}-STORY-{story_idx}"
            if story_id in created_jira_ids:
                continue

            created_jira_ids.add(story_id)
            story = {
                "id": story_id,
                "event_id": project_id,
                "parent_id": epic_id,
                "type": "Story",
                "title": f"Story: {epic_name} - Feature {story_idx}",
                "status": "To Do",
                "created_date": base_date + timedelta(days=15),
                "completed_date": None,
                "priority": random.choice(["High", "Medium"]),
                "story_points": random.randint(3, 8),
                "assigned_team": "Team A",
                "assigned_developer": None,
                "estimated_hours": None,
                "actual_hours": None,
            }
            create_jira_item(story)
            all_jiras.append(story)
            sprint_story_points += story["story_points"]

            # Create 2-4 tasks per story
            num_tasks = random.randint(2, 4)
            for task_idx in range(1, num_tasks + 1):
                task_id = f"{story_id}-TASK-{task_idx}"
                if task_id in created_jira_ids:
                    continue

                created_jira_ids.add(task_id)
                task = {
                    "id": task_id,
                    "event_id": project_id,
                    "parent_id": story_id,
                    "type": "Task",
                    "title": f"Task: {epic_name} - Feature {story_idx} - Task {task_idx}",
                    "status": "To Do",
                    "created_date": base_date + timedelta(days=15),
                    "completed_date": None,
                    "priority": story["priority"],
                    "story_points": random.randint(1, 3),
                    "assigned_team": "Team A",
                    "assigned_developer": f"dev{random.randint(1, 5)}@example.com",
                    "estimated_hours": random.randint(4, 16),
                    "actual_hours": None,
                }
                create_jira_item(task)
                all_jiras.append(task)

        story_points_per_sprint.append(sprint_story_points)

    # Create Sprints (2-week sprints for 12 weeks)
    sprints = []
    for sprint_num in range(1, 7):  # 6 sprints
        sprint_start = base_date + timedelta(days=14 + (sprint_num - 1) * 14)
        sprint_end = sprint_start + timedelta(days=14)

        # Select stories for this sprint
        available_stories = [
            j for j in all_jiras if j["type"] == "Story" and j["status"] == "To Do"
        ]
        sprint_stories = random.sample(
            available_stories, min(len(available_stories), random.randint(4, 6))
        )

        # Calculate sprint metrics
        total_points = (
            story_points_per_sprint[sprint_num - 1]
            if sprint_num <= len(story_points_per_sprint)
            else 0
        )
        completion_rate = random.uniform(0.7, 0.95)
        completed_points = int(total_points * completion_rate)

        sprint_data = {
            "id": f"{project_id}-SPRINT-{sprint_num}",
            "event_id": project_id,
            "start_date": sprint_start,
            "end_date": sprint_end,
            "planned_story_points": total_points,
            "completed_story_points": completed_points,
            "planned_stories": len(sprint_stories),
            "completed_stories": int(len(sprint_stories) * completion_rate),
            "team_velocity": completed_points,
            "burndown_efficiency": random.uniform(0.8, 1.0),
            "sprint_goals": f"Sprint {sprint_num} Goals",
            "retrospective_summary": f"Sprint {sprint_num} Retrospective",
            "blockers_encountered": random.randint(0, 3),
            "team_satisfaction_score": random.uniform(7.0, 9.0),
            "status": "Completed" if sprint_num < 6 else "In Progress",
        }
        create_sprint(sprint_data)
        sprints.append(sprint_data)

        # Associate stories with sprint and update their status
        story_ids = [story["id"] for story in sprint_stories]
        create_sprint_jira_associations(sprint_data["id"], story_ids)

        # Update story and task status based on completion rate
        for story in sprint_stories:
            completion_chance = random.random()
            if completion_chance < completion_rate:
                story_completion = sprint_end - timedelta(days=random.randint(0, 3))
                story["status"] = "Done"
                story["completed_date"] = story_completion

                # Create development artifacts
                commit_time = story_completion + timedelta(hours=2)
                pr_time = commit_time + timedelta(hours=1)

                # Create commit
                commit_data = {
                    "id": f"commit-{story['id']}",
                    "timestamp": commit_time,
                    "event_id": project_id,
                    "repository": "customer-portal",
                    "branch": f"feature/{story['id']}",
                    "author": f"dev{random.randint(1, 5)}@example.com",
                    "commit_hash": f"{random.getrandbits(32):08x}",
                    "files_changed": random.randint(3, 15),
                    "lines_added": random.randint(50, 500),
                    "lines_removed": random.randint(10, 200),
                    "code_coverage": random.uniform(80, 95),
                    "lint_score": random.uniform(85, 98),
                    "commit_type": "feature",
                    "review_time_minutes": random.randint(30, 120),
                    "comments_count": random.randint(2, 8),
                    "approved_by": "reviewer1@example.com",
                    "jira_id": story["id"],
                }
                create_commit(commit_data)

                # Create Pull Request
                pr_data = {
                    "id": f"PR-{story['id']}",
                    "created_at": pr_time,
                    "project_id": project_id,
                    "title": f"Feature: {story['title']}",
                    "description": f"Implementing {story['title']}",
                    "branch_from": f"feature/{story['id']}",
                    "branch_to": "main",
                    "author": commit_data["author"],
                    "status": PRStatus.MERGED,
                    "merged_at": pr_time + timedelta(hours=24),
                    "commit_id": commit_data["id"],
                    "commit_timestamp": commit_time,
                }
                create_pull_request(pr_data)

                # Create PR comments
                for comment_idx in range(1, random.randint(3, 6) + 1):
                    comment_data = {
                        "id": f"COM-{story['id']}-{comment_idx}",
                        "created_at": pr_time + timedelta(hours=comment_idx),
                        "pr_id": pr_data["id"],
                        "author": f"reviewer{random.randint(1, 3)}@example.com",
                        "content": f"Review comment {comment_idx}",
                    }
                    create_pr_comment(comment_data)

                # Create CICD event
                cicd_data = {
                    "id": f"CICD-{story['id']}",
                    "event_id": project_id,
                    "timestamp": pr_data["merged_at"] + timedelta(hours=1),
                    "environment": "staging",
                    "event_type": "build",
                    "build_id": f"build-{story['id']}",
                    "status": "success",
                    "duration_seconds": random.randint(300, 900),
                    "metrics": {
                        "test_coverage": random.uniform(80, 95),
                        "failed_tests": random.randint(0, 2),
                        "security_issues": random.randint(0, 1),
                    },
                }
                create_cicd_event(cicd_data)

                # Create P0 bug (10% chance)
                if random.random() < 0.1:
                    bug_data = {
                        "id": f"BUG-{story['id']}",
                        "event_id": project_id,
                        "jira_id": story["id"],
                        "build_id": cicd_data["build_id"],
                        "bug_type": random.choice(
                            ["Security", "Performance", "Functionality"]
                        ),
                        "impact_area": story["title"],
                        "severity": "P0",
                        "title": f"Critical issue in {story['title']}",
                        "status": "Fixed",
                        "created_date": cicd_data["timestamp"] + timedelta(hours=2),
                        "resolved_date": cicd_data["timestamp"]
                        + timedelta(hours=random.randint(24, 72)),
                        "resolution_time_hours": random.randint(24, 72),
                        "assigned_to": commit_data["author"],
                        "environment_found": "Staging",
                        "number_of_customers_affected": random.randint(0, 100),
                        "root_cause": "Implementation error",
                        "fix_version": "1.0.1",
                        "regression_test_status": "Passed",
                        "customer_communication_needed": random.choice([True, False]),
                        "postmortem_link": f"https://wiki.example.com/postmortem/BUG-{story['id']}",
                    }
                    create_bug(bug_data)

                    # Create team metrics for each week of the sprint
                week_start = sprint_start
                for week in range(2):  # 2 weeks per sprint
                    metrics_data = {
                        "id": f"{project_id}-TM-{sprint_num}-{week + 1}",
                        "event_id": project_id,
                        "week_starting": week_start,
                        "team_size": project_data["team_size"],
                        "velocity": completed_points
                        / 2,  # Split sprint velocity across weeks
                        "code_review_turnaround_hours": random.uniform(4, 24),
                        "build_success_rate": random.uniform(90, 100),
                        "test_coverage": random.uniform(80, 95),
                        "bugs_reported": random.randint(2, 8),
                        "bugs_fixed": random.randint(1, 6),
                        "technical_debt_hours": random.randint(4, 16),
                        "pair_programming_hours": random.randint(8, 24),
                        "code_review_comments": random.randint(20, 50),
                        "documentation_updates": random.randint(2, 8),
                        "knowledge_sharing_sessions": random.randint(1, 3),
                        "team_satisfaction": random.uniform(7.0, 9.0),
                        "sprint_completion_rate": completion_rate * 100,
                    }
                    create_team_metrics(metrics_data)
                    week_start += timedelta(days=7)

                # Calculate and store additional statistics
            statistics = {
                "total_story_points": sum(story_points_per_sprint),
                "sprint_breakdown": story_points_per_sprint,
                "average_velocity": sum(story_points_per_sprint)
                / len(story_points_per_sprint),
                "total_epics": len(epics),
                "total_stories": len([j for j in all_jiras if j["type"] == "Story"]),
                "total_tasks": len([j for j in all_jiras if j["type"] == "Task"]),
                "design_phases": len(design_phases),
                "sprints": len(sprints),
            }

            # Generate Sprint Burndown Data
            burndown_data = []
            for sprint_idx, sprint in enumerate(sprints):
                total_points = (
                    story_points_per_sprint[sprint_idx]
                    if sprint_idx < len(story_points_per_sprint)
                    else 0
                )
                days_in_sprint = 10  # 2 work weeks
                ideal_burn_rate = total_points / days_in_sprint

                # Generate daily burndown with some randomness
                remaining_points = total_points
                sprint_days = []

                for day in range(days_in_sprint):
                    date = sprint["start_date"] + timedelta(days=day)

                    # Add some randomness to actual burndown
                    if day > 0:  # No points burned on first day
                        # More points tend to be completed in middle of sprint
                        mid_sprint_factor = 1 - abs(day - days_in_sprint / 2) / (
                            days_in_sprint / 2
                        )
                        points_burned = (
                            ideal_burn_rate
                            * random.uniform(0.5, 1.5)
                            * mid_sprint_factor
                        )
                        remaining_points = max(0, remaining_points - points_burned)

                    sprint_days.append(
                        {
                            "date": date,
                            "remaining_points": remaining_points,
                            "ideal_points": max(
                                0, total_points - (ideal_burn_rate * day)
                            ),
                        }
                    )

                burndown_data.append(
                    {
                        "sprint_number": sprint_idx + 1,
                        "start_date": sprint["start_date"],
                        "end_date": sprint["end_date"],
                        "daily_data": sprint_days,
                    }
                )

            print(f"Created {len(created_jira_ids)} unique Jira items")
            print(f"Generated data for {len(sprints)} sprints")
            print(f"Generated {len(all_jiras)} total work items")
            print(f"Static test data loaded successfully")

            return {
                "project": project_data,
                "statistics": statistics,
                "design_jiras": design_jiras,
                "sprints": sprints,
                "burndown_data": burndown_data,
                "all_jiras": all_jiras,
                "created_ids": list(created_jira_ids),
            }
