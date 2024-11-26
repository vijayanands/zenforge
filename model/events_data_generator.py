import random
import uuid
from datetime import datetime, timedelta
from random import randint
from typing import Any, Dict, List, Tuple
from collections import defaultdict

import numpy as np
from soupsieve.css_match import DAYS_IN_WEEK
from sqlalchemy import text

from model.sdlc_events import (
    BugStatus,
    BugType,
    BuildMode,
    BuildStatus,
    Environment,
    ImpactArea,
    JiraStatus,
    JiraType,
    ProjectComplexity,
    ProjectDesignPhase,
    ProjectPriority,
    ProjectStatus,
    PRStatus,
    StageType,
)

BASE_START_DATE = datetime(2024, 1, 1)


class DataGenerator:
    def __init__(self):
        np.random.seed(42)
        random.seed(42)
        self.DAYS_IN_WEEK = 5

    def generate_project_base_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate base project information with specific completion states"""
        return {
            "PRJ-001": {  # All design complete, rest mixed
                "title": "Customer Portal Redesign",
                "description": "Modernize the customer portal with improved UX and additional self-service features",
                "start_date": BASE_START_DATE,
                "complexity": ProjectComplexity.HIGH,
                "status": ProjectStatus.CODE_COMPLETE,
                "priority": ProjectPriority.MEDIUM,
            },
            "PRJ-002": {  # Design and sprint/jira complete
                "title": "Payment Gateway Integration",
                "description": "Implement new payment gateway with support for multiple currencies",
                "start_date": BASE_START_DATE + timedelta(days=15),
                "complexity": ProjectComplexity.MEDIUM,
                "status": ProjectStatus.IN_PROGRESS,
                "priority": ProjectPriority.MEDIUM,
            },
            "PRJ-003": {  # Design, sprint, commit, CICD complete
                "title": "Mobile App Analytics",
                "description": "Add comprehensive analytics and tracking to mobile applications",
                "start_date": BASE_START_DATE + timedelta(days=30),
                "complexity": ProjectComplexity.MEDIUM,
                "status": ProjectStatus.RELEASED,
                "priority": ProjectPriority.HIGH,
            },
            "PRJ-004": {  # Mixed completion states
                "title": "API Gateway Migration",
                "description": "Migrate existing APIs to new gateway with improved security",
                "start_date": BASE_START_DATE + timedelta(days=45),
                "complexity": ProjectComplexity.HIGH,
                "status": ProjectStatus.CODE_COMPLETE,
                "priority": ProjectPriority.MEDIUM,
            },
            "PRJ-005": {  # All complete, no P0s
                "title": "Data Pipeline Optimization",
                "description": "Optimize existing data pipelines for better performance",
                "start_date": BASE_START_DATE + timedelta(days=60),
                "complexity": ProjectComplexity.MEDIUM,
                "status": ProjectStatus.RELEASED,
                "priority": ProjectPriority.HIGH,
            },
            "PRJ-006": {  # Mixed completion with all types of states
                "title": "Search Service Upgrade",
                "description": "Upgrade search infrastructure with advanced capabilities",
                "start_date": BASE_START_DATE + timedelta(days=75),
                "complexity": ProjectComplexity.HIGH,
                "status": ProjectStatus.RELEASED,
                "priority": ProjectPriority.LOW,
            },
        }

    @staticmethod
    def get_estimated_duration(complexity) -> int:
        if complexity == ProjectComplexity.VERY_HIGH:
            return 48 * DAYS_IN_WEEK
        elif complexity == ProjectComplexity.HIGH:
            return 24 * DAYS_IN_WEEK
        elif complexity == ProjectComplexity.MEDIUM:
            return 12 * DAYS_IN_WEEK
        elif complexity == ProjectComplexity.LOW:
            return 4 * DAYS_IN_WEEK
        else:
            raise ValueError(f"Invalid Value: {complexity} for complexity")

    @staticmethod
    def get_total_design_time(complexity):
        design_duration = DataGenerator.get_estimated_design_duration(complexity)
        requirement_duration = design_duration.get(ProjectDesignPhase.REQUIREMENT.value)
        ux_duration = design_duration.get(ProjectDesignPhase.UX_DESIGN.value)
        architecture_duration = design_duration.get(
            ProjectDesignPhase.ARCHITECTURE.value
        )
        database_design_duration = design_duration.get(
            ProjectDesignPhase.DATABASE_DESIGN.value
        )
        api_design_duration = design_duration.get(ProjectDesignPhase.API_DESIGN.value)
        security_review_duration = design_duration.get(
            ProjectDesignPhase.SECURITY_REVIEW.value
        )
        design_duration = (
            requirement_duration
            + max(ux_duration, architecture_duration)
            + max(database_design_duration, api_design_duration)
            + security_review_duration
        )
        return timedelta(days=design_duration * DAYS_IN_WEEK)

    @staticmethod
    def get_estimated_design_duration(complexity):
        if complexity == ProjectComplexity.VERY_HIGH:
            requirements = 8
            ux_design = 6
            architecture = 6
            database_design = 4
            api_design = 4
            security_review = 2
        elif complexity == ProjectComplexity.HIGH:
            requirements = 4
            ux_design = 2
            architecture = 2
            database_design = 2
            api_design = 2
            security_review = 2
        elif complexity == ProjectComplexity.MEDIUM:
            requirements = 2
            ux_design = 2
            architecture = 1
            database_design = 1
            api_design = 1
            security_review = 1
        elif complexity == ProjectComplexity.LOW:
            requirements = 1
            ux_design = 0
            architecture = 1
            database_design = 0
            api_design = 0
            security_review = 1
        else:
            raise ValueError(f"Invalid Value: {complexity} for complexity")
        return {
            f"{ProjectDesignPhase.REQUIREMENT.value}": requirements * DAYS_IN_WEEK,
            f"{ProjectDesignPhase.UX_DESIGN.value}": ux_design * DAYS_IN_WEEK,
            f"{ProjectDesignPhase.ARCHITECTURE.value}": architecture * DAYS_IN_WEEK,
            f"{ProjectDesignPhase.DATABASE_DESIGN.value}": database_design
            * DAYS_IN_WEEK,
            f"{ProjectDesignPhase.API_DESIGN.value}": api_design * DAYS_IN_WEEK,
            f"{ProjectDesignPhase.SECURITY_REVIEW.value}": security_review
            * DAYS_IN_WEEK,
        }

    @staticmethod
    def generate_project_details(
        projects: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate detailed project information"""
        project_details = []
        for proj_id, details in projects.items():
            project_details.append(
                {
                    "id": proj_id,
                    "title": details["title"],
                    "description": details["description"],
                    "start_date": details["start_date"],
                    "status": details["status"],
                    "complexity": details["complexity"],
                    "estimated_duration_weeks": DataGenerator.get_estimated_duration(
                        details["complexity"]
                    ),
                    "priority": details["priority"],
                }
            )
        return project_details

    @staticmethod
    def generate_date_sequence(
        start_date: datetime,
        num_events: int,
        min_days: int = 1,
        max_days: int = 5,
    ) -> List[datetime]:
        """Generate a sequence of dates"""
        dates = [start_date]
        current_date = start_date
        for _ in range(num_events - 1):
            days_to_add = np.random.randint(min_days, max_days)
            current_date += timedelta(days=days_to_add)
            dates.append(current_date)
        return dates

    @staticmethod
    def generate_unique_id(prefix: str = "") -> str:
        """Generate a unique identifier"""
        return f"{prefix}{uuid.uuid4().hex[:8]}"

    @staticmethod
    def get_random_jira_ids(
        project_id: str,
        available_jiras: List[str],
        min_count: int = 1,
        max_count: int = 5,
    ) -> List[str]:
        """Get random jira IDs for a project"""
        project_jiras = [j for j in available_jiras if j.startswith(project_id)]
        count = min(randint(min_count, max_count), len(project_jiras))
        return random.sample(project_jiras, count) if project_jiras else []

    @staticmethod
    def get_random_commit_ids(
        available_commits: List[str], min_count: int = 1, max_count: int = 3
    ) -> List[str]:
        """Get random commit IDs"""
        count = min(randint(min_count, max_count), len(available_commits))
        return random.sample(available_commits, count) if available_commits else []

    @staticmethod
    def generate_commit_metrics() -> Tuple[int, int, int, float, float]:
        """Generate metrics for a code commit"""
        files_changed = np.random.randint(1, 20)
        lines_added = np.random.randint(10, 500)
        lines_removed = np.random.randint(5, 300)
        code_coverage = np.random.uniform(75, 98)
        lint_score = np.random.uniform(80, 99)
        return files_changed, lines_added, lines_removed, code_coverage, lint_score

    @staticmethod
    def get_jira_status(completion_state: str, design_jira: bool = False) -> JiraStatus:
        """Get Jira item status based on completion state"""
        if completion_state in [
            ProjectStatus.CODE_COMPLETE,
            ProjectStatus.RELEASED,
            ProjectStatus.END_OF_LIFE,
        ]:
            return JiraStatus.CLOSED
        elif completion_state == ProjectStatus.NOT_STARTED:
            return JiraStatus.OPEN
        elif completion_state == ProjectStatus.IN_PROGRESS:
            return JiraStatus.IN_PROGRESS
        elif completion_state == ProjectStatus.DESIGN_PHASE_COMPLETE:
            if design_jira:
                return JiraStatus.CLOSED
            else:
                return JiraStatus.IN_PROGRESS
        else:
            raise ValueError(f"Invalid Project Status {completion_state} Found")

    @staticmethod
    def get_commit_status(completion_state: str) -> Dict[str, Any]:
        """Get commit related statuses based on completion state"""
        if completion_state in ["pre_release", "all_complete"]:
            return {
                "code_coverage": np.random.uniform(90, 98),
                "lint_score": np.random.uniform(95, 99),
                "review_time_minutes": np.random.randint(10, 60),
            }
        elif completion_state == "design_and_sprint":
            return {
                "code_coverage": np.random.uniform(85, 95),
                "lint_score": np.random.uniform(90, 98),
                "review_time_minutes": np.random.randint(20, 90),
            }
        else:
            return {
                "code_coverage": np.random.uniform(75, 90),
                "lint_score": np.random.uniform(80, 95),
                "review_time_minutes": np.random.randint(30, 120),
            }

    @staticmethod
    def associate_jiras_with_sprints(
        sprint_data: List[Dict[str, Any]], jira_data: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Create associations between sprints and jiras"""
        sprint_jira_map = {}
        project_jiras = {}

        # Group jiras by project
        for jira in jira_data:
            if jira["event_id"] not in project_jiras:
                project_jiras[jira["event_id"]] = []
            project_jiras[jira["event_id"]].append(jira)

        # Associate jiras with sprints based on dates and state
        for sprint in sprint_data:
            project_id = sprint["event_id"]
            if project_id in project_jiras:
                available_jiras = project_jiras[project_id]
                sprint_start = sprint["start_date"]
                sprint_end = sprint["end_date"]

                # Filter jiras that might be relevant to this sprint's timeframe
                relevant_jiras = []
                for jira in available_jiras:
                    jira_created = jira["created_date"]
                    jira_completed = jira.get(
                        "completed_date"
                    )  # Use get() to handle missing completed_date

                    # Include jira if:
                    # 1. It was created before sprint end AND
                    # 2. Either it's not completed, or it was completed after sprint start
                    if jira_created <= sprint_end:
                        if not jira_completed or jira_completed >= sprint_start:
                            relevant_jiras.append(jira["id"])

                # Assign jiras to sprint
                if relevant_jiras:
                    num_jiras = random.randint(
                        min(3, len(relevant_jiras)), min(8, len(relevant_jiras))
                    )
                    sprint_jira_map[sprint["id"]] = random.sample(
                        relevant_jiras, num_jiras
                    )

        return sprint_jira_map


data_generator = DataGenerator()


def generate_design_related_jira(
    design_jiras,
    jira_id,
    proj_id,
    design_phase,
    status,
    start_date,
    completed_date,
    estimated_hours,
    actual_hours,
):
    """Generate Jira items specifically for design phases"""
    design_jiras.append(
        {
            "id": jira_id,
            "event_id": proj_id,
            "type": JiraType.TASK,
            "title": f"{design_phase} Design for Project: {proj_id}",
            "status": status,
            "parent_id": None,
            "created_date": start_date,
            "completed_date": completed_date,
            "priority": "High",
            "story_points": np.random.randint(5, 13),
            "estimated_hours": estimated_hours,
            "actual_hours": actual_hours,
        }
    )


def add_design_phase_event(
    design_events,
    design_jiras,
    proj_id,
    jira_id,
    proj_status,
    phase,
    start_time,
    end_time,
    author,
    estimated_hours,
) -> []:
    design_events.extend(
        [
            {
                "id": f"{proj_id}-{phase.value}-START",
                "event_id": proj_id,
                "design_type": phase,
                "stage": StageType.START,
                "timestamp": start_time,
                "author": author,
                "jira": jira_id,
            }
        ]
    )
    completion_time = None
    status = JiraStatus.IN_PROGRESS

    if proj_status != ProjectStatus.NOT_STARTED:
        design_events.append(
            {
                "id": f"{proj_id}-{phase.value}-END",
                "event_id": proj_id,
                "design_type": phase,
                "stage": StageType.END,
                "timestamp": end_time,
                "author": author,
                "jira": jira_id,
                "stakeholders": "Product,Dev,Arch",
            }
        )
        completion_time = end_time
        status = JiraStatus.CLOSED

    actual_hours = end_time - start_time
    generate_design_related_jira(
        design_jiras,
        jira_id,
        proj_id,
        phase.value,
        status,
        start_time,
        completion_time,
        estimated_hours,
        actual_hours,
    )


def generate_design_events(projects: Dict[str, Dict[str, Any]]):
    design_events = []
    design_jiras = []

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        design_phase_durations = DataGenerator.get_estimated_design_duration(
            details["complexity"]
        )

        # Phase 1: Requirements (First phase)
        max_duration = design_phase_durations.get(ProjectDesignPhase.REQUIREMENT.value)
        if max_duration:
            requirements_duration = timedelta(
                days=np.random.randint(1, max_duration + 1)
            )
        else:
            requirements_duration = 0
        requirements_completion = start_date + requirements_duration

        # Generate Requirements events
        jira_id = f"{proj_id}-REQUIREMENTS-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.REQUIREMENT,
            start_date,
            requirements_completion,
            "requirements_lead@example.com",
            max_duration,
        )

        phase2_start_time = requirements_completion + timedelta(days=1)
        # Phase 2: UX Design (Follows Requirements)
        max_duration = design_phase_durations.get(ProjectDesignPhase.UX_DESIGN.value)
        if max_duration:
            ux_duration = timedelta(days=np.random.randint(1, max_duration + 1))
        else:
            ux_duration = 0
        ux_completion = phase2_start_time + ux_duration

        jira_id = f"{proj_id}-UX_DESIGN-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.UX_DESIGN,
            phase2_start_time,
            ux_completion,
            "ux_lead@example.com",
            max_duration,
        )

        # Phase 2: Architecture
        max_duration = design_phase_durations.get(ProjectDesignPhase.ARCHITECTURE.value)
        if max_duration:
            architecture_duration = timedelta(
                days=np.random.randint(1, max_duration + 1)
            )
        else:
            architecture_duration = 0
        architecture_completion = phase2_start_time + architecture_duration

        jira_id = f"{proj_id}-ARCHITECTURE-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.ARCHITECTURE,
            phase2_start_time,
            architecture_completion,
            "arch_lead@example.com",
            max_duration,
        )

        phase3_start_time = max(ux_completion, architecture_completion) + timedelta(
            days=1
        )
        # Phase 3: Database Design
        max_duration = design_phase_durations.get(
            ProjectDesignPhase.DATABASE_DESIGN.value
        )
        if max_duration:
            db_design_duration = timedelta(days=np.random.randint(1, max_duration + 1))
        else:
            db_design_duration = 0
        db_design_completion = phase3_start_time + db_design_duration

        jira_id = f"{proj_id}-DATABASE_DESIGN-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.DATABASE_DESIGN,
            phase3_start_time,
            db_design_completion,
            "db_lead@example.com",
            max_duration,
        )

        # Phase 3: API Design
        max_duration = design_phase_durations.get(ProjectDesignPhase.API_DESIGN.value)
        if max_duration:
            api_design_duration = timedelta(days=np.random.randint(1, max_duration + 1))
        else:
            api_design_duration = 0
        api_design_completion = phase3_start_time + api_design_duration

        jira_id = f"{proj_id}-API_DESIGN-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.API_DESIGN,
            phase3_start_time,
            api_design_completion,
            "api_lead@example.com",
            max_duration,
        )

        # Phase 4: Security Review
        max_duration = design_phase_durations.get(
            ProjectDesignPhase.SECURITY_REVIEW.value
        )
        security_review_start = max(
            db_design_completion, api_design_completion
        ) + timedelta(days=1)
        if max_duration:
            security_review_duration = timedelta(
                days=np.random.randint(1, max_duration + 1)
            )
        else:
            security_review_duration = 0
        security_review_completion = security_review_start + security_review_duration

        jira_id = f"{proj_id}-SECURITY_REVIEW-1"
        add_design_phase_event(
            design_events,
            design_jiras,
            proj_id,
            jira_id,
            details["status"],
            ProjectDesignPhase.SECURITY_REVIEW,
            security_review_start,
            security_review_completion,
            "security_lead@example.com",
            max_duration,
        )

        # add the security review completion date as the design phase completion date if the project status is not NOT_STARTED
        if details["status"] != ProjectStatus.NOT_STARTED:
            details["design_phase_completed_time"] = security_review_completion

    # Sort all events by timestamp to ensure chronological order
    design_events.sort(key=lambda x: (x["event_id"], x["timestamp"]))

    return design_events, design_jiras


def get_design_event_status(completion_state: str) -> Dict[str, Any]:
    """Helper function to get design event status based on completion state"""
    if completion_state in [
        "design_only",
        "design_and_sprint",
        "pre_release",
        "all_complete",
    ]:
        return {"stage": "end", "review_status": "Approved"}
    elif completion_state == "mixed":
        if np.random.random() < 0.7:
            status = np.random.choice(["end", "blocked"], p=[0.7, 0.3])
            return {
                "stage": status,
                "review_status": "Approved" if status == "end" else "In Review",
            }
        else:
            return {"stage": "start", "review_status": "Pending"}
    else:  # mixed_all
        status = np.random.choice(["start", "end", "blocked"], p=[0.2, 0.5, 0.3])
        return {
            "stage": status,
            "review_status": {
                "start": "Pending",
                "end": "Approved",
                "blocked": "In Review",
            }[status],
        }


def _get_number_of_epics_stories_and_tasks(complexity: ProjectComplexity) -> tuple:
    if complexity == ProjectComplexity.VERY_HIGH:
        return 10, 8, 6
    elif complexity == ProjectComplexity.HIGH:
        return 6, 6, 6
    elif complexity == ProjectComplexity.MEDIUM:
        return 2, 4, 4
    elif complexity == ProjectComplexity.LOW:
        return 1, 2, 2
    else:
        raise ValueError("Invalid Complexity on Project")


def generate_jira_items(
    projects: Dict[str, Dict[str, Any]], design_jiras
) -> List[Dict[str, Any]]:
    """Generate Jira items for all projects with proper date hierarchies"""
    # First generate design-related Jiras
    all_jiras = design_jiras

    for proj_id, details in projects.items():
        project_status = details["status"]
        design_phase_completion_time = details["design_phase_completed_time"]
        first_epic_start = design_phase_completion_time + timedelta(days=1)
        # if project complexity is very high, there are 10 epics, 8 stories per epic, 6 tasks per story and epics are assumed to take about 4 sprints
        # if project complexity is high, there are 6 epics, 6 stories per epic, 6 tasks per story and epics are assumed to take about 2 sprints
        # if project complexity is medium there are 2 epics, 4 stories per epic, 4 tasks per story and epics are assumed to take 1 sprint
        # if project complexity is low there is 1 epic, 2 stories per epic, 2 tasks per story and it starts after design
        no_of_epics, no_of_stories, no_of_tasks = (
            _get_number_of_epics_stories_and_tasks(details["complexity"])
        )
        # Generate Epics
        for epic_num in range(1, no_of_epics):
            status = data_generator.get_jira_status(project_status)
            # Epic starts after sprint start date
            epic_start = first_epic_start + timedelta(days=(epic_num - 1) * 14)

            epic_id = f"{proj_id}-E{epic_num}"
            epic_data = {
                "id": epic_id,
                "event_id": proj_id,
                "parent_id": None,
                "type": JiraType.EPIC,
                "title": f"Epic {epic_num} for {details['title']}",
                "status": status,
                "created_date": epic_start,
                "completed_date": None,
                "priority": np.random.choice(["High", "Medium", "Low"]),
                "story_points": np.random.randint(20, 40),
                "estimated_hours": None,
                "actual_hours": None,
            }
            all_jiras.append(epic_data)

            # Generate Stories for Epic
            for story_num in range(1, no_of_stories):
                story_status = data_generator.get_jira_status(project_status)
                # Story starts after epic starts
                story_start = epic_start + timedelta(days=randint(1, 3))
                story_id = f"{epic_id}-S{story_num}"

                story_data = {
                    "id": story_id,
                    "event_id": proj_id,
                    "parent_id": epic_id,
                    "type": JiraType.STORY,
                    "title": f"Story {story_num} for Epic {epic_num}",
                    "status": story_status,
                    "created_date": story_start,
                    "completed_date": None,
                    "priority": np.random.choice(["High", "Medium", "Low"]),
                    "story_points": np.random.randint(5, 13),
                    "estimated_hours": None,
                    "actual_hours": None,
                }
                all_jiras.append(story_data)

                # Generate Tasks for Story
                for task_num in range(1, no_of_tasks):
                    task_status = data_generator.get_jira_status(project_status)
                    estimated_hours = np.random.randint(4, 16)
                    # Task starts after story starts
                    task_start = story_start + timedelta(days=randint(0, 2))
                    actual_hours = (
                        int(estimated_hours * np.random.uniform(0.8, 1.3))
                        if task_status == JiraStatus.CLOSED
                        else None
                    )
                    task_completion = (
                        task_start + timedelta(days=randint(2, 5))
                        if task_status == JiraStatus.CLOSED
                        else None
                    )

                    task_data = {
                        "id": f"{story_id}-T{task_num}",
                        "event_id": proj_id,
                        "parent_id": story_id,
                        "type": JiraType.TASK,
                        "title": f"Task {task_num} for Story {story_num}",
                        "status": task_status,
                        "created_date": task_start,
                        "completed_date": task_completion,
                        "priority": np.random.choice(["High", "Medium", "Low"]),
                        "story_points": np.random.randint(1, 5),
                        "actual_hours": actual_hours,
                    }
                    all_jiras.append(task_data)
    return all_jiras


def generate_commits(
    projects: Dict[str, Dict[str, Any]], jira_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate code commits with proper timestamps and Jira associations"""
    commits = []

    # Create a map of available completed Jira IDs per project
    project_jiras = {}
    for jira in jira_items:
        if jira["event_id"] not in project_jiras:
            project_jiras[jira["event_id"]] = []
        # Only include completed Jiras
        if jira.get("completed_date"):
            project_jiras[jira["event_id"]].append(jira)

    for proj_id, details in projects.items():
        completion_state = details["status"]
        available_jiras = project_jiras.get(proj_id, [])

        if not available_jiras:
            continue

        # Adjust number of commits based on project state
        num_commits = (
            200
            if completion_state
            in [
                ProjectStatus.NOT_STARTED,
                ProjectStatus.CODE_COMPLETE,
                ProjectStatus.RELEASED,
                ProjectStatus.END_OF_LIFE,
            ]
            else np.random.randint(50, 150)
        )

        for i in range(num_commits):
            # Randomly select a completed Jira
            selected_jira = random.choice(available_jiras)
            jira_completion_date = selected_jira["completed_date"]

            # Calculate commit date - ensure it's after Jira completion
            commit_date = jira_completion_date + timedelta(minutes=randint(5, 60))

            commit_metrics = data_generator.get_commit_status(completion_state)
            files_changed, lines_added, lines_removed, _, _ = (
                data_generator.generate_commit_metrics()
            )

            commits.append(
                {
                    "id": f"commit_{uuid.uuid4().hex[:8]}",
                    "event_id": proj_id,
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
                    "commit_type": np.random.choice(
                        ["feature", "bugfix", "refactor", "docs", "test"],
                        p=[0.4, 0.3, 0.15, 0.1, 0.05],
                    ),
                    "review_time_minutes": commit_metrics["review_time_minutes"],
                    "comments_count": np.random.randint(0, 10),
                    "approved_by": f"reviewer{np.random.randint(1, 4)}@example.com",
                    "jira_id": selected_jira["id"],
                }
            )

    # Sort all commits by timestamp
    return sorted(commits, key=lambda x: x["timestamp"])


def generate_sprints():
    sprints = []
    # let us assume that sprints are 2 week sprints and we generate sprints for the year from the BASE_START_DATE
    # assuming 52 weeks in a year, we have 26 sprints
    for sprint_num in range(1, 26):
        sprint_id = f"Sprint-{sprint_num}"
        sprint_data = {
            "id": sprint_id,
            "start_date": BASE_START_DATE + timedelta(days=(sprint_num - 1) * 14),
            "end_date": BASE_START_DATE + timedelta(days=13),
        }
        sprints.append(sprint_data)
    return sprints


def _determine_sprint(date: datetime) -> int:
    """
    Determine the sprint number for a given date.
    Sprint 1: Jan 1-14, Sprint 2: Jan 15-28, etc.

    Args:
        date (datetime): The date to check

    Returns:
        int: The sprint number

    Example: _determine_sprint(datetime(2024, 1, 14)) => 1
             _determine_sprint(datetime(2024, 1, 15)) => 2
    """
    if date < BASE_START_DATE:
        raise ValueError("Date cannot be before the base start time")

    # Calculate the number of days between the given date and base start time
    # Add 1 because we want Jan 1 to be day 1, not day 0
    days_difference = (date - BASE_START_DATE).days + 1

    # Calculate sprint number using ceiling division
    # This ensures that day 1-14 is sprint 1, day 15-28 is sprint 2, etc.
    sprint_number = (days_difference + 13) // 14

    return sprint_number


def assign_jiras_to_sprints(jira_items):
    sprint_jira_map = {}
    for jira in jira_items:
        jira_id = jira["id"]
        jira_start = jira["created_date"]
        jira_completion_date = jira["completed_date"]
        starting_sprint = _determine_sprint(jira_start)
        if jira_completion_date is not None:
            ending_sprint = _determine_sprint(jira_completion_date)
        else:
            ending_sprint = None

        if ending_sprint is None:
            # add the jira to the starting sprint only
            sprint_id = f"Sprint-{starting_sprint}"
            # Initialize the list if sprint_id doesn't exist in map, then add jira_id
            if sprint_id not in sprint_jira_map:
                sprint_jira_map[sprint_id] = []
            sprint_jira_map[sprint_id].append(jira_id)
        else:
            # add the jira to all sprints between starting sprint and ending sprint
            for idx in range(starting_sprint, ending_sprint + 1):
                sprint_id = f"Sprint-{idx}"
                # Initialize the list if sprint_id doesn't exist in map, then add jira_id
                if sprint_id not in sprint_jira_map:
                    sprint_jira_map[sprint_id] = []
                sprint_jira_map[sprint_id].append(jira_id)

    return sprint_jira_map


def generate_pull_requests(
    projects: List[Dict[str, Any]], commits: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate pull requests and comments with higher percentage of merged PRs"""
    pull_requests = []

    # Define target branches with weights
    target_branches = {
        "main": 0.6,  # Increased to 60% to main
        "develop": 0.2,  # 20% to develop
        "staging": 0.1,  # 10% to staging
        "test": 0.1,  # 10% to test
    }

    # Create a map of projects for easier lookup
    projects_map = {project["id"]: project for project in projects}

    # Group commits by project and branch
    project_branch_commits = {}
    for commit in commits:
        if not commit["branch"].lower().startswith(("main", "master", "release")):
            proj_id = commit["event_id"]
            branch = commit["branch"]
            if proj_id not in project_branch_commits:
                project_branch_commits[proj_id] = {}
            if branch not in project_branch_commits[proj_id]:
                project_branch_commits[proj_id][branch] = []
            project_branch_commits[proj_id][branch].append(commit)

    # Generate PRs for each project and branch
    for proj_id, branch_commits in project_branch_commits.items():
        project = projects_map.get(proj_id)
        if not project:
            continue

        project_status = project.get("status", ProjectStatus.IN_PROGRESS)
        merge_probability = {
            ProjectStatus.END_OF_LIFE: 1.0,
            ProjectStatus.RELEASED: 0.9,
            ProjectStatus.CODE_COMPLETE: 0.8,
            ProjectStatus.DESIGN_PHASE_COMPLETE: 0.6,
            ProjectStatus.IN_PROGRESS: 0.4,
            ProjectStatus.NOT_STARTED: 0.2,
        }.get(project_status, 0.5)

        # Create PRs for each feature branch
        for branch, branch_commits in branch_commits.items():
            if randint(1, 100) > 40:  # 60% of feature branches get PRs
                # Sort commits by timestamp
                branch_commits.sort(key=lambda x: x["timestamp"])
                first_commit = branch_commits[0]
                last_commit = branch_commits[-1]

                pr_created = last_commit["timestamp"] + timedelta(minutes=randint(5, 30))
                
                # Select target branch based on weights
                branch_to = np.random.choice(
                    list(target_branches.keys()), p=list(target_branches.values())
                )

                # Determine PR status with higher merge rate
                if branch_to == "main":
                    status = np.random.choice(
                        [PRStatus.MERGED, PRStatus.BLOCKED, PRStatus.OPEN],
                        p=[
                            merge_probability,
                            (1 - merge_probability) / 2,
                            (1 - merge_probability) / 2,
                        ],
                    )
                else:
                    status = np.random.choice(
                        [PRStatus.MERGED, PRStatus.BLOCKED, PRStatus.OPEN],
                        p=[
                            merge_probability * 0.8,
                            (1 - merge_probability * 0.8) / 2,
                            (1 - merge_probability * 0.8) / 2,
                        ],
                    )

                # Generate review data
                review_started = pr_created + timedelta(hours=randint(1, 24))
                merged_at = review_started + timedelta(hours=randint(2, 48)) if status == PRStatus.MERGED else None

                # Calculate additions and deletions
                additions = sum(commit.get("lines_added", 0) for commit in branch_commits)
                deletions = sum(commit.get("lines_removed", 0) for commit in branch_commits)

                pr_data = {
                    "id": f"PR-{uuid.uuid4().hex[:8]}",
                    "created_at": pr_created.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "project_id": proj_id,
                    "title": f"Feature: {first_commit['commit_type']} - {first_commit['repository']}",
                    "description": f"Implementing changes for {project['title']}",
                    "branch_from": branch,
                    "branch_to": branch_to,
                    "author": first_commit["author"],
                    "status": status,
                    "merged_at": merged_at.strftime("%Y-%m-%dT%H:%M:%SZ") if merged_at else None,
                    "commits": [commit["id"] for commit in branch_commits],
                    "additions": additions,
                    "deletions": deletions,
                    "review_started_at": review_started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "first_commit_date": first_commit["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "last_commit_date": last_commit["timestamp"].strftime("%Y-%m-%dT%H:%M:%SZ"),
                }

                pull_requests.append(pr_data)

                # Generate review comments
                num_comments = randint(2, 8)
                comment_time = review_started
                for _ in range(num_comments):
                    comment_time += timedelta(hours=randint(1, 8))
                    if merged_at and comment_time > merged_at:
                        break
                    
                    pr_data.setdefault("review_comments", []).append({
                        "id": f"comment-{uuid.uuid4().hex[:8]}",
                        "created_at": comment_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "author": random.choice([dev for dev in DEVELOPER_NAMES if dev != pr_data["author"]]),
                        "body": f"Review comment {_ + 1}",
                    })

    print(
        f"Generated {len(pull_requests)} pull requests, {sum(1 for pr in pull_requests if pr['status'] == PRStatus.MERGED)} merged"
    )
    return pull_requests


def update_epic_and_store_completion_dates(jira_items):
    story_completion_dates = {}
    epic_completion_dates = {}
    stories = []
    epics = []
    tasks = []
    incomplete_stories = {}
    incomplete_epics = {}
    for jira in jira_items:
        if jira["type"] == JiraType.STORY:
            stories.append(jira)
        elif jira["type"] == JiraType.EPIC:
            epics.append(jira)
        elif jira["type"] == JiraType.TASK:
            tasks.append(jira)
        else:
            id = jira["id"]
            raise ValueError(f"Invalid Jira Type for jira: {id}")
    for jira in tasks:
        parent = jira["parent_id"]
        if parent is None:
            continue
        if jira["status"] not in (JiraStatus.CLOSED, JiraStatus.FIXED):
            incomplete_stories[parent] = None
            continue
        if parent not in story_completion_dates.keys():
            story_completion_dates[parent] = jira["completed_date"] + timedelta(
                seconds=60
            )
        else:
            story_completion_dates[parent] = max(
                story_completion_dates[parent], jira["completed_date"]
            )
    for jira in stories:
        id = jira["id"]
        parent = jira["parent_id"]
        assert parent is not None
        if id in incomplete_stories.keys():
            incomplete_epics[parent] = None
            incomplete_stories[id] = jira
        if id not in story_completion_dates.keys():
            continue
        story_completion_date = story_completion_dates[id]
        jira["completed_date"] = story_completion_date
        if parent not in epic_completion_dates.keys():
            epic_completion_dates[parent] = story_completion_date + timedelta(
                seconds=60
            )
        else:
            epic_completion_dates[parent] = max(
                epic_completion_dates[parent], story_completion_date
            )
    for jira in epics:
        id = jira["id"]
        if id in incomplete_epics.keys():
            incomplete_epics[id] = jira
            continue
        if id in epic_completion_dates.keys():
            jira["completed_date"] = epic_completion_dates[id]

    for key, value in incomplete_stories.items():
        value["completed_date"] = None
    for key, value in incomplete_epics.items():
        value["completed_date"] = None

    for jira in jira_items:
        if jira["type"] == JiraType.TASK:
            continue
        if (
            jira["id"] not in incomplete_stories.keys()
            and jira["id"] not in incomplete_epics.keys()
        ):
            if jira["completed_date"] == None:
                id = jira["id"]
                status = jira["status"]
                message = f"{id} with status: {status} has completed date None"
                print(message)
                assert False
    return jira_items


def generate_projects():
    print("Generating project data...")
    projects = data_generator.generate_project_base_data()
    project_details = data_generator.generate_project_details(projects)
    print("Generating design events...")
    design_events, design_jiras = generate_design_events(projects)
    print("Generating Design Jira items...")
    jira_items = generate_jira_items(projects, design_jiras)
    jira_items = update_epic_and_store_completion_dates(jira_items)
    return design_events, jira_items, project_details, projects


def generate_cicd_events(
    pull_requests: List[Dict[str, Any]], project_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate CICD events based on pull requests and manual triggers.
    Ensures completed projects have at least one successful build chain on main branch.
    """
    cicd_events = []

    # Helper function to generate release version
    def generate_release_version() -> str:
        major = random.randint(1, 3)
        minor = random.randint(0, 9)
        patch = random.randint(0, 99)
        return f"{major}.{minor}.{patch}"

    # Helper function to generate build duration
    def generate_build_duration() -> int:
        return random.randint(300, 1800)  # 5-30 minutes in seconds

    # Environment sequence for promotion
    env_sequence = [
        Environment.DEV,
        Environment.QA,
        Environment.STAGING,
        Environment.PRODUCTION,
    ]

    # Create events for pull requests
    for pr in pull_requests:
        if pr["status"] == PRStatus.MERGED and pr["merged_at"]:
            # For each merged PR, create builds for different environments
            prev_timestamp = pr["merged_at"]
            build_success = True
            build_version = generate_release_version()

            # Create sequential builds through environments
            for env in env_sequence:
                if not build_success:
                    break

                # Add some time after the previous event
                timestamp = prev_timestamp + timedelta(minutes=random.randint(5, 15))

                # Higher success rate for builds
                success_rate = {
                    Environment.DEV: 0.95,
                    Environment.QA: 0.90,
                    Environment.STAGING: 0.85,
                    Environment.PRODUCTION: 0.80,
                }[env]

                status = (
                    BuildStatus.SUCCESS
                    if random.random() < success_rate
                    else BuildStatus.FAILURE
                )

                build_id = f"build-{uuid.uuid4().hex[:8]}"

                cicd_event = {
                    "event_id": pr["id"],
                    "timestamp": timestamp,
                    "project_id": pr["project_id"],
                    "environment": env.value,
                    "event_type": "build",
                    "build_id": build_id,
                    "status": status.value,
                    "duration_seconds": generate_build_duration(),
                    "branch": pr["branch_to"],
                    "tag": None,
                    "mode": BuildMode.AUTOMATIC.value,
                    "release_version": build_version,
                }

                cicd_events.append(cicd_event)

                # Update success flag for next environment
                build_success = status == BuildStatus.SUCCESS
                prev_timestamp = timestamp

    # Get list of completed projects
    completed_projects = [
        proj_id
        for proj_id in project_ids
        if any(
            pr["project_id"] == proj_id and pr["status"] == PRStatus.MERGED
            for pr in pull_requests
        )
    ]

    # Ensure each completed project has at least one successful build chain
    for project_id in completed_projects:
        # Check if project already has a successful build chain
        has_successful_chain = False
        for env in env_sequence:
            env_success = any(
                event["project_id"] == project_id
                and event["environment"] == env.value
                and event["status"] == BuildStatus.SUCCESS.value
                and event["branch"] == "main"
                and event["mode"] == BuildMode.AUTOMATIC.value
                for event in cicd_events
            )
            if not env_success:
                has_successful_chain = False
                break
            has_successful_chain = True

        # If no successful chain exists, create one
        if not has_successful_chain:
            timestamp = datetime(2024, 1, 1) + timedelta(days=random.randint(1, 90))
            build_version = generate_release_version()

            for env in env_sequence:
                build_id = f"build-{uuid.uuid4().hex[:8]}"

                cicd_event = {
                    "event_id": f"auto-{uuid.uuid4().hex[:8]}",
                    "timestamp": timestamp,
                    "project_id": project_id,
                    "environment": env.value,
                    "event_type": "build",
                    "build_id": build_id,
                    "status": BuildStatus.SUCCESS.value,
                    "duration_seconds": generate_build_duration(),
                    "branch": "main",
                    "tag": None,
                    "mode": BuildMode.AUTOMATIC.value,
                    "release_version": build_version,
                }

                cicd_events.append(cicd_event)
                timestamp += timedelta(minutes=random.randint(5, 15))

    # Generate some manual builds (not associated with PRs)
    num_manual_builds = len(pull_requests) // 4  # Reduce number of manual builds
    base_timestamp = datetime(2024, 1, 1)
    branches = ["main", "develop", "staging", "feature/xyz", "hotfix/abc"]

    for _ in range(num_manual_builds):
        branch = random.choice(branches)
        env = random.choice(env_sequence)
        timestamp = base_timestamp + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        build_id = f"manual-build-{uuid.uuid4().hex[:8]}"

        cicd_events.append(
            {
                "event_id": f"manual-{uuid.uuid4().hex[:8]}",
                "project_id": random.choice(project_ids),
                "timestamp": timestamp,
                "environment": env.value,
                "event_type": "build",
                "build_id": build_id,
                "status": random.choice([status for status in BuildStatus]).value,
                "duration_seconds": generate_build_duration(),
                "branch": branch,
                "tag": None,
                "mode": BuildMode.MANUAL.value,
                "release_version": generate_release_version(),
            }
        )

    # Sort all events by timestamp
    cicd_events.sort(key=lambda x: x["timestamp"])

    # Print statistics
    automatic_builds = sum(
        1 for e in cicd_events if e["mode"] == BuildMode.AUTOMATIC.value
    )
    manual_builds = sum(1 for e in cicd_events if e["mode"] == BuildMode.MANUAL.value)
    successful_builds = sum(
        1 for e in cicd_events if e["status"] == BuildStatus.SUCCESS.value
    )
    failed_builds = sum(
        1 for e in cicd_events if e["status"] == BuildStatus.FAILURE.value
    )

    print(f"Generated {len(cicd_events)} CICD events")
    print(f"- Automatic builds: {automatic_builds}")
    print(f"- Manual builds: {manual_builds}")
    print(f"- Successful builds: {successful_builds}")
    print(f"- Failed builds: {failed_builds}")

    return cicd_events


# Bug Data Generator
class BugDataGenerator:
    def __init__(self):
        self.bug_titles = [
            "Critical data corruption in {area}",
            "System crash during {area} operation",
            "Memory leak in {area} component",
            "Security vulnerability in {area}",
            "Performance degradation in {area}",
            "Deadlock in {area} process",
            "Data inconsistency in {area}",
            "Authentication bypass in {area}",
            "Resource exhaustion in {area}",
            "Race condition in {area} workflow",
        ]

        self.areas = [
            "user authentication",
            "payment processing",
            "data sync",
            "API gateway",
            "cache layer",
            "database operations",
            "file upload",
            "search indexing",
            "notification service",
            "reporting module",
        ]

    def generate_bug_data(
        self, cicd_event: Dict[str, Any], bug_count: int
    ) -> List[Dict[str, Any]]:
        """Generate bug data for a successful CICD event"""
        bugs = []
        for i in range(bug_count):
            created_date = cicd_event["timestamp"] + timedelta(
                hours=random.randint(1, 24)
            )

            # Determine if bug will be resolved/closed
            will_resolve = random.random() < 0.7  # 70% chance of resolution
            resolved_date = None
            close_date = None
            resolution_time_hours = None

            if will_resolve:
                # First calculate the resolved_date
                min_resolution_hours = 24  # Minimum time to resolution
                max_resolution_hours = 96  # Maximum time to resolution
                actual_resolution_hours = random.randint(
                    min_resolution_hours, max_resolution_hours
                )
                resolved_date = created_date + timedelta(hours=actual_resolution_hours)

                # Now calculate resolution_time_hours as a portion of the actual time difference
                # This represents the actual time spent working on the bug, which must be
                # less than the total elapsed time between creation and resolution
                max_possible_hours = (
                    resolved_date - created_date
                ).total_seconds() / 3600
                # Resolution time should be between 20% and 80% of the total time difference
                resolution_time_hours = round(
                    random.uniform(0.2 * max_possible_hours, 0.8 * max_possible_hours),
                    1,
                )

                will_close = random.random() < 0.8  # 80% chance of closure if resolved
                if will_close:
                    close_date = resolved_date + timedelta(hours=random.randint(4, 24))
                    status = BugStatus.CLOSED
                else:
                    status = BugStatus.FIXED
            else:
                status = random.choice(
                    [BugStatus.OPEN, BugStatus.IN_PROGRESS, BugStatus.BLOCKED]
                )

            bug_data = {
                "id": f"BUG-{cicd_event['build_id']}-{i + 1}",
                "project_id": cicd_event["project_id"],
                "bug_type": random.choice(list(BugType)),
                "impact_area": random.choice(list(ImpactArea)),
                "severity": "P0",
                "title": random.choice(self.bug_titles).format(
                    area=random.choice(self.areas)
                ),
                "status": status,
                "created_date": created_date,
                "resolved_date": resolved_date,
                "close_date": close_date,
                "resolution_time_hours": resolution_time_hours,
                "assigned_to": f"dev{random.randint(1, 5)}@example.com",
                "environment_found": cicd_event["environment"],
                "build_id": cicd_event["build_id"],
                "release_id": cicd_event["release_version"],
            }
            bugs.append(bug_data)

        return bugs


def generate_bugs_for_builds(cicd_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate bugs for successful CICD builds"""
    generator = BugDataGenerator()
    all_bugs = []

    for event in cicd_events:
        if event["status"] != BuildStatus.SUCCESS.value:
            continue

        # Determine number of bugs based on branch
        if event["branch"] == "main":
            # Fewer bugs for main branch
            bug_count = random.randint(0, 2)
        else:
            # More bugs for other branches
            bug_count = random.randint(1, 4)

        if bug_count > 0:
            bugs = generator.generate_bug_data(event, bug_count)
            all_bugs.extend(bugs)

    return all_bugs


def generate_all_data() -> Dict[str, Any]:
    """Generate all data for the application with comprehensive validation and timeline constraints"""
    try:
        design_events, jira_items, project_details, projects = generate_projects()

        print("Generating sprints...")
        sprints = generate_sprints()

        print("Associating Jiras with sprints...")
        sprint_jira_map = assign_jiras_to_sprints(jira_items)

        print("Generating commits...")
        commits = generate_commits(projects, jira_items)

        print("Generating pull requests...")
        pull_requests = generate_pull_requests(project_details, commits)

        print("Generating CICD events...")
        project_ids = list(projects.keys())
        cicd_events = generate_cicd_events(pull_requests, project_ids)

        print("Generating P0 bugs...")
        bugs = generate_bugs_for_builds(cicd_events)

        # Combine all data
        all_data = {
            "projects": project_details,
            "design_events": design_events,
            "jira_items": jira_items,
            "commits": commits,
            "sprints": sprints,
            "pull_requests": pull_requests,
            "cicd_events": cicd_events,
            "bugs": bugs,
            "relationships": {
                "sprint_jira_associations": sprint_jira_map,
            },
        }

        print("Data generation completed successfully")
        return all_data

    except Exception as e:
        print(f"Error generating data: {str(e)}")
        raise
