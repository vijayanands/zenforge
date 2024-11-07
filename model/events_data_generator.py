# events_data_generator.py
import random
import uuid
from datetime import datetime, timedelta
from random import randint
from typing import Any, Dict, List, Tuple

import numpy as np
from sqlalchemy import text

from model.sdlc_events import (
    BugStatus,
    BugType,
    BuildMode,
    BuildStatus,
    Environment,
    ImpactArea,
    PRStatus,
    StageType,
    db_manager,
    verify_jira_references,
    verify_project_references,
    verify_temporal_consistency,
)
from model.validators import (
    validate_all_timelines,
    validate_bug_build_association,
    validate_bug_data,
    validate_bug_timelines,
    validate_cicd_relationships,
    validate_commit_jira_completion_dates,
)


class DataGenerator:
    def __init__(self):
        np.random.seed(42)
        random.seed(42)
        self.base_start_date = datetime(2024, 1, 1)

    def generate_project_base_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate base project information with specific completion states"""
        return {
            "PRJ-001": {  # All design complete, rest mixed
                "title": "Customer Portal Redesign",
                "description": "Modernize the customer portal with improved UX and additional self-service features",
                "start_date": self.base_start_date,
                "complexity": "High",
                "team_size": 12,
                "completion_state": "design_only",
            },
            "PRJ-002": {  # Design and sprint/jira complete
                "title": "Payment Gateway Integration",
                "description": "Implement new payment gateway with support for multiple currencies",
                "start_date": self.base_start_date + timedelta(days=15),
                "complexity": "Medium",
                "team_size": 8,
                "completion_state": "design_and_sprint",
            },
            "PRJ-003": {  # Design, sprint, commit, CICD complete
                "title": "Mobile App Analytics",
                "description": "Add comprehensive analytics and tracking to mobile applications",
                "start_date": self.base_start_date + timedelta(days=30),
                "complexity": "Medium",
                "team_size": 6,
                "completion_state": "pre_release",
            },
            "PRJ-004": {  # Mixed completion states
                "title": "API Gateway Migration",
                "description": "Migrate existing APIs to new gateway with improved security",
                "start_date": self.base_start_date + timedelta(days=45),
                "complexity": "High",
                "team_size": 10,
                "completion_state": "mixed",
            },
            "PRJ-005": {  # All complete, no P0s
                "title": "Data Pipeline Optimization",
                "description": "Optimize existing data pipelines for better performance",
                "start_date": self.base_start_date + timedelta(days=60),
                "complexity": "Medium",
                "team_size": 7,
                "completion_state": "all_complete",
            },
            "PRJ-006": {  # Mixed completion with all types of states
                "title": "Search Service Upgrade",
                "description": "Upgrade search infrastructure with advanced capabilities",
                "start_date": self.base_start_date + timedelta(days=75),
                "complexity": "High",
                "team_size": 9,
                "completion_state": "mixed_all",
            },
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
                    "status": (
                        "Completed"
                        if details["completion_state"] == "all_complete"
                        else "In Progress"
                    ),
                    "complexity": details["complexity"],
                    "team_size": details["team_size"],
                    "estimated_duration_weeks": np.random.randint(12, 24),
                    "budget_allocated": np.random.randint(100000, 500000),
                    "priority": np.random.choice(
                        ["High", "Medium", "Low"], p=[0.5, 0.3, 0.2]
                    ),
                }
            )
        return project_details

    def generate_design_phases(self) -> List[str]:
        """Generate list of design phases"""
        return [
            "requirements",
            "ux_design",
            "architecture",
            "database_design",
            "api_design",
            "security_review",
        ]

    def generate_stakeholders(self) -> str:
        """Generate random stakeholder combination"""
        stakeholder_groups = [
            "Product,Dev,QA",
            "Dev,Arch",
            "UX,Dev,Product",
            "Dev,Security",
            "Product,QA,Security",
            "Arch,Security,Dev",
        ]
        return np.random.choice(stakeholder_groups)

    @staticmethod
    def get_completion_probability(completion_state: str, event_type: str) -> float:
        """Get probability of completion based on project state and event type"""
        probabilities = {
            "design_only": {
                "design": 1.0,
                "sprint": 0.7,
                "jira": 0.6,
                "commit": 0.5,
                "cicd": 0.4,
                "bug": 0.3,
            },
            "design_and_sprint": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 0.7,
                "cicd": 0.6,
                "bug": 0.5,
            },
            "pre_release": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 1.0,
                "cicd": 1.0,
                "bug": 0.7,
            },
            "mixed": {
                "design": 0.7,
                "sprint": 0.6,
                "jira": 0.5,
                "commit": 0.4,
                "cicd": 0.3,
                "bug": 0.4,
            },
            "all_complete": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 1.0,
                "cicd": 1.0,
                "bug": 0.0,
            },
            "mixed_all": {
                "design": 0.8,
                "sprint": 0.7,
                "jira": 0.6,
                "commit": 0.5,
                "cicd": 0.4,
                "bug": 0.5,
            },
        }
        return probabilities.get(completion_state, {}).get(event_type, 0.5)

    def should_generate_record(
        self, project_details: Dict[str, Any], event_type: str
    ) -> bool:
        """Determine if a record should be generated based on completion state"""
        completion_prob = self.get_completion_probability(
            project_details["completion_state"], event_type
        )
        return np.random.random() < completion_prob

    @staticmethod
    def get_design_event_status(completion_state: str) -> Dict[str, Any]:
        """Get design event status based on completion state"""
        if completion_state in [
            "design_only",
            "design_and_sprint",
            "pre_release",
            "all_complete",
        ]:
            return {"stage": "end", "review_status": "Approved"}
        elif completion_state == "mixed":
            if np.random.random() < 0.7:
                return {
                    "stage": np.random.choice(["end", "blocked", "resume"]),
                    "review_status": np.random.choice(
                        ["Approved", "In Review", "Pending"]
                    ),
                }
            else:
                return {"stage": "start", "review_status": "Pending"}
        else:  # mixed_all
            return {
                "stage": np.random.choice(["start", "end", "blocked", "resume"]),
                "review_status": np.random.choice(["Approved", "In Review", "Pending"]),
            }

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
    def get_jira_status(completion_state: str) -> str:
        """Get Jira item status based on completion state"""
        if completion_state in ["design_and_sprint", "pre_release", "all_complete"]:
            return "Done"
        elif completion_state == "design_only":
            return np.random.choice(["In Progress", "To Do", "Done"], p=[0.4, 0.4, 0.2])
        else:  # mixed or mixed_all
            return np.random.choice(
                ["To Do", "In Progress", "Done", "Blocked"], p=[0.3, 0.3, 0.2, 0.2]
            )

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

    def generate_metrics(self, metric_type: str) -> Dict[str, Any]:
        """Generate metrics based on type"""
        if metric_type == "build":
            return {
                "test_coverage": np.random.uniform(80, 95),
                "failed_tests": np.random.randint(0, 10),
                "warnings": np.random.randint(0, 20),
                "security_issues": np.random.randint(0, 5),
            }
        elif metric_type == "deployment":
            return {
                "startup_time": np.random.uniform(5, 30),
                "memory_usage": np.random.randint(512, 2048),
                "cpu_usage": np.random.uniform(20, 80),
                "response_time": np.random.uniform(100, 500),
            }
        return {}

    @staticmethod
    def get_sequential_story_points(num_items: int, total_points: int) -> List[int]:
        """Generate a sequence of story points that sum to total_points"""
        points = []
        remaining_points = total_points
        remaining_items = num_items

        for i in range(num_items - 1):
            max_points = remaining_points - remaining_items + 1
            min_points = 1
            points_for_item = np.random.randint(
                min_points, max(min_points + 1, max_points)
            )
            points.append(points_for_item)
            remaining_points -= points_for_item
            remaining_items -= 1

        points.append(remaining_points)
        return points

    @staticmethod
    def calculate_project_progress(
        completion_state: str, elapsed_days: int, total_days: int
    ) -> float:
        """Calculate project progress percentage based on state and time"""
        time_progress = min(1.0, elapsed_days / total_days)

        if completion_state == "all_complete":
            return 1.0
        elif completion_state == "pre_release":
            return min(1.0, time_progress * 1.1)
        elif completion_state == "design_and_sprint":
            return min(0.9, time_progress * 1.05)
        elif completion_state == "design_only":
            return min(0.7, time_progress * 0.9)
        else:  # mixed or mixed_all
            return min(0.8, time_progress)


data_generator = DataGenerator()


def generate_design_related_jiras(
    projects: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate Jira items specifically for design phases"""
    design_jiras = []
    design_phases = data_generator.generate_design_phases()

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        completion_state = details["completion_state"]

        for phase in design_phases:
            jira_id = f"{proj_id}-{phase.upper()}-1"

            # Determine status based on completion state
            if completion_state in [
                "design_only",
                "design_and_sprint",
                "pre_release",
                "all_complete",
            ]:
                status = "Done"
                completed_date = start_date + timedelta(days=14)
                actual_hours = np.random.randint(16, 32)
            elif completion_state == "mixed":
                status = np.random.choice(["Done", "In Progress"], p=[0.7, 0.3])
                completed_date = (
                    start_date + timedelta(days=14) if status == "Done" else None
                )
                actual_hours = np.random.randint(16, 32) if status == "Done" else None
            else:  # mixed_all
                status = np.random.choice(
                    ["Done", "In Progress", "To Do"], p=[0.5, 0.3, 0.2]
                )
                completed_date = (
                    start_date + timedelta(days=14) if status == "Done" else None
                )
                actual_hours = np.random.randint(16, 32) if status == "Done" else None

            design_jiras.append(
                {
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
                    "actual_hours": actual_hours,
                }
            )

    return design_jiras


def generate_design_events(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generate design events for all projects with sequential and parallel dependencies:
    - Requirements and UX are sequential
    - Architecture, API Design, and Database Design start in parallel after Requirements
    - Security Review starts after Architecture, API Design, and Database Design complete

    Args:
        projects: Dictionary of project details
    Returns:
        List of design events with proper timeline dependencies
    """
    design_events = []

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        completion_state = details["completion_state"]

        # Initialize tracking for phase completion
        phase_completion_times = {}

        # Phase 1: Requirements (First phase)
        requirements_duration = timedelta(days=np.random.randint(5, 10))
        requirements_completion = start_date + requirements_duration
        phase_completion_times["requirements"] = requirements_completion

        # Generate Requirements events
        design_events.extend(
            [
                {
                    "id": f"{proj_id}-REQUIREMENTS-START",
                    "event_id": proj_id,
                    "design_type": "requirements",
                    "stage": StageType.START,
                    "timestamp": start_date,
                    "author": "requirements_lead@example.com",
                    "jira": f"{proj_id}-REQUIREMENTS-1",
                    "stakeholders": "Product,Dev,Arch",
                    "review_status": "Pending",
                }
            ]
        )

        if completion_state in [
            "design_only",
            "design_and_sprint",
            "pre_release",
            "all_complete",
        ]:
            design_events.append(
                {
                    "id": f"{proj_id}-REQUIREMENTS-END",
                    "event_id": proj_id,
                    "design_type": "requirements",
                    "stage": StageType.END,
                    "timestamp": requirements_completion,
                    "author": "requirements_lead@example.com",
                    "jira": f"{proj_id}-REQUIREMENTS-1",
                    "stakeholders": "Product,Dev,Arch",
                    "review_status": "Approved",
                }
            )

        # Phase 2: UX Design (Follows Requirements)
        ux_duration = timedelta(days=np.random.randint(7, 12))
        ux_start = requirements_completion + timedelta(days=1)
        ux_completion = ux_start + ux_duration
        phase_completion_times["ux_design"] = ux_completion

        design_events.extend(
            [
                {
                    "id": f"{proj_id}-UX_DESIGN-START",
                    "event_id": proj_id,
                    "design_type": "ux_design",
                    "stage": StageType.START,
                    "timestamp": ux_start,
                    "author": "ux_lead@example.com",
                    "jira": f"{proj_id}-UX_DESIGN-1",
                    "stakeholders": "UX,Dev,Product",
                    "review_status": "Pending",
                }
            ]
        )

        if completion_state in [
            "design_only",
            "design_and_sprint",
            "pre_release",
            "all_complete",
        ]:
            design_events.append(
                {
                    "id": f"{proj_id}-UX_DESIGN-END",
                    "event_id": proj_id,
                    "design_type": "ux_design",
                    "stage": StageType.END,
                    "timestamp": ux_completion,
                    "author": "ux_lead@example.com",
                    "jira": f"{proj_id}-UX_DESIGN-1",
                    "stakeholders": "UX,Dev,Product",
                    "review_status": "Approved",
                }
            )

        # Phase 3: Parallel phases (Architecture, API Design, Database Design)
        parallel_start = requirements_completion + timedelta(days=1)

        # Generate events for parallel phases
        parallel_phases = {
            "architecture": {
                "duration": np.random.randint(8, 15),
                "author": "arch_lead@example.com",
            },
            "api_design": {
                "duration": np.random.randint(6, 12),
                "author": "api_lead@example.com",
            },
            "database_design": {
                "duration": np.random.randint(7, 13),
                "author": "db_lead@example.com",
            },
        }

        # Create start events and calculate completion times for parallel phases
        for phase, details in parallel_phases.items():
            phase_duration = timedelta(days=details["duration"])
            phase_completion = parallel_start + phase_duration
            phase_completion_times[phase] = phase_completion

            design_events.append(
                {
                    "id": f"{proj_id}-{phase.upper()}-START",
                    "event_id": proj_id,
                    "design_type": phase,
                    "stage": StageType.START,
                    "timestamp": parallel_start,
                    "author": details["author"],
                    "jira": f"{proj_id}-{phase.upper()}-1",
                    "stakeholders": "Dev,Arch",
                    "review_status": "Pending",
                }
            )

            if completion_state in [
                "design_only",
                "design_and_sprint",
                "pre_release",
                "all_complete",
            ]:
                design_events.append(
                    {
                        "id": f"{proj_id}-{phase.upper()}-END",
                        "event_id": proj_id,
                        "design_type": phase,
                        "stage": StageType.END,
                        "timestamp": phase_completion,
                        "author": details["author"],
                        "jira": f"{proj_id}-{phase.upper()}-1",
                        "stakeholders": "Dev,Arch",
                        "review_status": "Approved",
                    }
                )

        # Phase 4: Security Review (after all parallel phases complete)
        security_start = max(
            phase_completion_times["architecture"],
            phase_completion_times["api_design"],
            phase_completion_times["database_design"],
        ) + timedelta(days=1)

        security_duration = timedelta(days=np.random.randint(5, 10))
        security_completion = security_start + security_duration
        phase_completion_times["security_review"] = security_completion

        design_events.extend(
            [
                {
                    "id": f"{proj_id}-SECURITY_REVIEW-START",
                    "event_id": proj_id,
                    "design_type": "security_review",
                    "stage": StageType.START,
                    "timestamp": security_start,
                    "author": "security_lead@example.com",
                    "jira": f"{proj_id}-SECURITY_REVIEW-1",
                    "stakeholders": "Security,Dev,Arch",
                    "review_status": "Pending",
                }
            ]
        )

        if completion_state in [
            "design_only",
            "design_and_sprint",
            "pre_release",
            "all_complete",
        ]:
            design_events.append(
                {
                    "id": f"{proj_id}-SECURITY_REVIEW-END",
                    "event_id": proj_id,
                    "design_type": "security_review",
                    "stage": StageType.END,
                    "timestamp": security_completion,
                    "author": "security_lead@example.com",
                    "jira": f"{proj_id}-SECURITY_REVIEW-1",
                    "stakeholders": "Security,Dev,Arch",
                    "review_status": "Approved",
                }
            )

        # For mixed states, add blocked/resume events randomly
        if completion_state in ["mixed", "mixed_all"]:
            for phase in phase_completion_times.keys():
                if np.random.random() < 0.3:  # 30% chance of having blocks
                    phase_start = next(
                        event["timestamp"]
                        for event in design_events
                        if event["design_type"] == phase
                        and event["stage"] == StageType.START
                    )
                    block_time = phase_start + timedelta(days=np.random.randint(2, 4))
                    resume_time = block_time + timedelta(days=np.random.randint(2, 4))

                    design_events.extend(
                        [
                            {
                                "id": f"{proj_id}-{phase.upper()}-BLOCK1",
                                "event_id": proj_id,
                                "design_type": phase,
                                "stage": StageType.BLOCKED,
                                "timestamp": block_time,
                                "author": f"{phase.split('_')[0]}_lead@example.com",
                                "jira": f"{proj_id}-{phase.upper()}-1",
                                "stakeholders": "Dev,Arch",
                                "review_status": "In Review",
                            },
                            {
                                "id": f"{proj_id}-{phase.upper()}-RESUME1",
                                "event_id": proj_id,
                                "design_type": phase,
                                "stage": StageType.RESUME,
                                "timestamp": resume_time,
                                "author": f"{phase.split('_')[0]}_lead@example.com",
                                "jira": f"{proj_id}-{phase.upper()}-1",
                                "stakeholders": "Dev,Arch",
                                "review_status": "In Review",
                            },
                        ]
                    )

    # Sort all events by timestamp to ensure chronological order
    design_events.sort(key=lambda x: (x["event_id"], x["timestamp"]))

    return design_events


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


def generate_jira_items(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Jira items for all projects with proper date hierarchies"""
    # First generate design-related Jiras
    all_jiras = generate_design_related_jiras(projects)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        sprint_start = details["start_date"] + timedelta(days=13)

        # Generate Epics
        for epic_num in range(1, 6):
            # Associate epic with a sprint
            sprint_num = (epic_num - 1) // 2 + 1  # Distribute epics across sprints
            sprint_start_date = sprint_start + timedelta(days=sprint_num * 14)

            status = data_generator.get_jira_status(completion_state)
            # Epic starts after sprint start date
            epic_start = sprint_start_date + timedelta(days=randint(1, 3))
            epic_completion = (
                epic_start + timedelta(days=epic_num + 25) if status == "Done" else None
            )

            epic_id = f"{proj_id}-E{epic_num}"
            epic_data = {
                "id": epic_id,
                "event_id": proj_id,
                "parent_id": None,
                "type": "Epic",
                "title": f"Epic {epic_num} for {details['title']}",
                "status": status,
                "created_date": epic_start,
                "completed_date": epic_completion,
                "priority": np.random.choice(["High", "Medium", "Low"]),
                "story_points": np.random.randint(20, 40),
                "assigned_team": f"Team {chr(65 + np.random.randint(0, 3))}",
                "assigned_developer": None,
                "estimated_hours": None,
                "actual_hours": None,
            }
            all_jiras.append(epic_data)

            # Generate Stories for Epic
            for story_num in range(1, 6):
                story_status = data_generator.get_jira_status(completion_state)
                # Story starts after epic starts
                story_start = epic_start + timedelta(days=randint(2, 4))
                story_completion = (
                    story_start + timedelta(days=randint(5, 10))
                    if story_status == "Done"
                    else None
                )
                story_id = f"{epic_id}-S{story_num}"

                story_data = {
                    "id": story_id,
                    "event_id": proj_id,
                    "parent_id": epic_id,
                    "type": "Story",
                    "title": f"Story {story_num} for Epic {epic_num}",
                    "status": story_status,
                    "created_date": story_start,
                    "completed_date": story_completion,
                    "priority": np.random.choice(["High", "Medium", "Low"]),
                    "story_points": np.random.randint(5, 13),
                    "assigned_team": f"Team {chr(65 + np.random.randint(0, 3))}",
                    "assigned_developer": None,
                    "estimated_hours": None,
                    "actual_hours": None,
                }
                all_jiras.append(story_data)

                # Generate Tasks for Story
                for task_num in range(1, 6):
                    task_status = data_generator.get_jira_status(completion_state)
                    estimated_hours = np.random.randint(4, 16)
                    # Task starts after story starts
                    task_start = story_start + timedelta(days=randint(1, 3))
                    actual_hours = (
                        int(estimated_hours * np.random.uniform(0.8, 1.3))
                        if task_status == "Done"
                        else None
                    )
                    task_completion = (
                        task_start + timedelta(days=randint(2, 5))
                        if task_status == "Done"
                        else None
                    )

                    task_data = {
                        "id": f"{story_id}-T{task_num}",
                        "event_id": proj_id,
                        "parent_id": story_id,
                        "type": "Task",
                        "title": f"Task {task_num} for Story {story_num}",
                        "status": task_status,
                        "created_date": task_start,
                        "completed_date": task_completion,
                        "priority": np.random.choice(["High", "Medium", "Low"]),
                        "story_points": np.random.randint(1, 5),
                        "assigned_developer": f"dev{np.random.randint(1, 6)}@example.com",
                        "estimated_hours": estimated_hours,
                        "actual_hours": actual_hours,
                    }
                    all_jiras.append(task_data)

                    # Update story and epic completion based on task status
                    if task_completion and story_data["status"] == "Done":
                        story_data["completed_date"] = max(
                            story_data["completed_date"] or task_completion,
                            task_completion,
                        )
                    if task_completion and epic_data["status"] == "Done":
                        epic_data["completed_date"] = max(
                            epic_data["completed_date"] or task_completion,
                            task_completion,
                        )

    # For completed projects, ensure all non-design Jiras are marked as Done
    for jira in all_jiras:
        project_details = projects.get(jira["event_id"])
        if project_details and project_details["completion_state"] == "all_complete":
            if jira["type"] != "Design":
                jira["status"] = "Done"
                if jira.get("completed_date") is None:
                    if jira["type"] == "Epic":
                        jira["completed_date"] = jira["created_date"] + timedelta(
                            days=randint(15, 25)
                        )
                    elif jira["type"] == "Story":
                        jira["completed_date"] = jira["created_date"] + timedelta(
                            days=randint(7, 14)
                        )
                    else:  # Task
                        jira["completed_date"] = jira["created_date"] + timedelta(
                            days=randint(3, 7)
                        )
                        jira["actual_hours"] = int(
                            jira["estimated_hours"] * np.random.uniform(0.8, 1.3)
                        )

    return all_jiras


def adjust_commit_dates(
    commits: List[Dict[str, Any]], jira_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Adjust commit dates to ensure they happen after their associated Jira item's completion date.
    If a Jira isn't completed, the commit won't be generated.

    Args:
        commits (List[Dict[str, Any]]): List of commit dictionaries
        jira_items (List[Dict[str, Any]]): List of Jira item dictionaries

    Returns:
        List[Dict[str, Any]]: List of adjusted commits with proper timestamps
    """
    # Create a map of Jira completion times
    jira_completion_times = {
        j["id"]: j.get("completed_date")
        for j in jira_items
        if j.get("completed_date") is not None
    }

    # Filter and adjust commits
    adjusted_commits = []
    for commit in commits:
        jira_completion = jira_completion_times.get(commit["jira_id"])

        if jira_completion:
            # Set commit timestamp to jira completion time plus random minutes (5-60)
            adjusted_commit = commit.copy()
            adjusted_commit["timestamp"] = jira_completion + timedelta(
                minutes=randint(5, 60)
            )
            adjusted_commits.append(adjusted_commit)

    # Sort adjusted commits by timestamp
    return sorted(adjusted_commits, key=lambda x: x["timestamp"])


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
        completion_state = details["completion_state"]
        available_jiras = project_jiras.get(proj_id, [])

        if not available_jiras:
            continue

        # Adjust number of commits based on project state
        num_commits = (
            200
            if completion_state in ["pre_release", "all_complete"]
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


def fetch_valid_prs(session):
    """Fetch all valid PRs from the database with their creation and merge times"""
    result = session.execute(
        text(
            """
        SELECT id, created_at, merged_at, project_id, branch_to, status
        FROM sdlc_timeseries.pull_requests
        WHERE status = 'MERGED' AND merged_at IS NOT NULL
        ORDER BY merged_at
    """
        )
    )

    valid_prs = {}
    for row in result:
        valid_prs[row.id] = {
            "created_at": row.created_at,
            "merged_at": row.merged_at,
            "project_id": row.project_id,
            "branch_to": row.branch_to,
        }
    return valid_prs


def generate_sprints(
    projects: Dict[str, Dict[str, Any]], jira_items: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    """Generate sprints for all projects with Jira associations"""
    sprints = []
    sprint_jira_map = {}

    # Group jiras by project
    project_jiras = {}
    for jira in jira_items:
        if jira["event_id"] not in project_jiras:
            project_jiras[jira["event_id"]] = []
        project_jiras[jira["event_id"]].append(jira)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        sprint_start = details["start_date"] + timedelta(days=14)
        available_jiras = project_jiras.get(proj_id, [])
        unassigned_jiras = set(jira["id"] for jira in available_jiras)

        for sprint_num in range(1, 9):
            sprint_id = f"{proj_id}-Sprint-{sprint_num}"
            sprint_start_date = sprint_start + timedelta(days=(sprint_num - 1) * 14)
            sprint_end_date = sprint_start_date + timedelta(days=14)

            # Determine completion based on project state
            is_completed = completion_state in [
                "design_and_sprint",
                "pre_release",
                "all_complete",
            ] or (
                completion_state in ["mixed", "mixed_all"] and np.random.random() < 0.7
            )

            # Filter jiras that can be included in this sprint
            eligible_jiras = [
                jira["id"]
                for jira in available_jiras
                if jira["id"] in unassigned_jiras
                and jira["created_date"] <= sprint_end_date
                and (
                    not jira.get("completed_date")
                    or jira["completed_date"] >= sprint_start_date
                )
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
                        min(3, len(eligible_jiras)), min(8, len(eligible_jiras))
                    )
                    sprint_jiras = random.sample(eligible_jiras, num_jiras)

                # Update unassigned jiras set
                unassigned_jiras -= set(sprint_jiras)

            # Calculate metrics based on assigned jiras
            sprint_jiras_data = [j for j in available_jiras if j["id"] in sprint_jiras]
            planned_story_points = sum(j["story_points"] for j in sprint_jiras_data)
            completed_story_points = int(
                planned_story_points
                * (
                    np.random.uniform(0.9, 1.1)
                    if is_completed
                    else np.random.uniform(0.5, 0.8)
                )
            )

            planned_stories = len(sprint_jiras)
            completed_stories = int(
                planned_stories
                * (
                    np.random.uniform(0.9, 1.0)
                    if is_completed
                    else np.random.uniform(0.5, 0.8)
                )
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
                "burndown_efficiency": (
                    np.random.uniform(0.9, 1.1)
                    if is_completed
                    else np.random.uniform(0.6, 0.9)
                ),
                "sprint_goals": f"Complete features for {details['title']} phase {sprint_num}",
                "retrospective_summary": np.random.choice(
                    [
                        "Improved team collaboration",
                        "Technical debt addressed",
                        "Communication challenges identified",
                        "Process improvements implemented",
                        "Knowledge sharing enhanced",
                    ]
                ),
                "blockers_encountered": (
                    np.random.randint(0, 2) if is_completed else np.random.randint(2, 5)
                ),
                "team_satisfaction_score": (
                    np.random.uniform(8, 10)
                    if is_completed
                    else np.random.uniform(6, 8)
                ),
                "status": "Completed" if is_completed else "In Progress",
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


def update_jiras_with_sprints(
    jira_items: List[Dict[str, Any]], sprint_jira_map: Dict[str, List[str]]
) -> List[Dict[str, Any]]:
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
        jira_copy["sprint_id"] = jira_to_sprint.get(jira["id"])
        updated_jiras.append(jira_copy)

    return updated_jiras


def generate_pull_requests(
    projects: List[Dict[str, Any]], commits: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Generate pull requests and comments with higher percentage of merged PRs"""
    pull_requests = []
    pr_comments = []

    # Define target branches with weights
    target_branches = {
        "main": 0.6,  # Increased to 60% to main
        "develop": 0.2,  # 20% to develop
        "staging": 0.1,  # 10% to staging
        "test": 0.1,  # 10% to test
    }

    # Create a map of projects for easier lookup
    projects_map = {project["id"]: project for project in projects}

    # Group commits by project
    project_commits = {}
    for commit in commits:
        if not commit["branch"].lower().startswith(("main", "master", "release")):
            proj_id = commit["event_id"]
            if proj_id not in project_commits:
                project_commits[proj_id] = []
            project_commits[proj_id].append(commit)

    # Sort commits in each project by timestamp
    for proj_commits in project_commits.values():
        proj_commits.sort(key=lambda x: x["timestamp"])

    # Generate PRs for each project
    for proj_id, feature_commits in project_commits.items():
        project = projects_map.get(proj_id)
        if not project:
            continue

        completion_state = project.get("completion_state", "mixed")

        # Determine merge probability based on project state
        merge_probability = {
            "all_complete": 0.9,
            "pre_release": 0.8,
            "design_and_sprint": 0.7,
            "mixed_all": 0.6,
            "mixed": 0.5,
            "design_only": 0.4,
        }.get(completion_state, 0.5)

        # Create PRs for eligible commits
        for commit in feature_commits:
            # Higher percentage of commits get PRs
            if randint(1, 100) > 40:  # 60% of feature commits get PRs
                pr_id = f"PR-{commit['id']}"
                created_at = commit["timestamp"] + timedelta(minutes=randint(5, 30))

                # Select target branch based on weights
                branch_to = np.random.choice(
                    list(target_branches.keys()), p=list(target_branches.values())
                )

                # Determine PR status with higher merge rate
                if branch_to == "main":
                    status = np.random.choice(
                        ["MERGED", "BLOCKED", "OPEN"],
                        p=[
                            merge_probability,
                            (1 - merge_probability) / 2,
                            (1 - merge_probability) / 2,
                        ],
                    )
                else:
                    status = np.random.choice(
                        ["MERGED", "BLOCKED", "OPEN"],
                        p=[
                            merge_probability * 0.8,
                            (1 - merge_probability * 0.8) / 2,
                            (1 - merge_probability * 0.8) / 2,
                        ],
                    )

                merged_at = None
                if status == "MERGED":
                    merged_at = created_at + timedelta(days=randint(1, 3))

                # Create PR
                pull_requests.append(
                    {
                        "id": pr_id,
                        "created_at": created_at,
                        "project_id": proj_id,
                        "title": f"Feature: {commit['commit_type']} - {commit['repository']}",
                        "description": f"Implementing changes for {project['title']}",
                        "branch_from": commit["branch"],
                        "branch_to": branch_to,
                        "author": commit["author"],
                        "status": status,
                        "merged_at": merged_at,
                        "commit_id": commit["id"],
                        "commit_timestamp": commit["timestamp"],
                    }
                )

                # Generate comments for the PR
                num_comments = randint(2, 8)
                comment_time = created_at

                # Generate comments...
                for _ in range(num_comments):
                    comment_time += timedelta(hours=randint(1, 8))
                    if merged_at and comment_time > merged_at:
                        break

                    template = np.random.choice(
                        [
                            "Please review the changes in file_{num}",
                            "I've addressed the previous comments",
                            "LGTM 👍",
                            "Can you add more tests?",
                            "Consider refactoring this part",
                            "The changes look good, but needs documentation",
                            "This might impact performance",
                            "Approved after addressing comments",
                            "Need to fix the failing tests",
                            "Should we add logging here?",
                        ]
                    )

                    content = (
                        template.format(num=randint(1, commit["files_changed"]))
                        if "{num}" in template
                        else template
                    )

                    pr_comments.append(
                        {
                            "id": f"COM-{uuid.uuid4().hex[:8]}",
                            "pr_id": pr_id,
                            "created_at": comment_time,
                            "author": f"reviewer{randint(1, 4)}@example.com",
                            "content": content,
                        }
                    )

    print(
        f"Generated {len(pull_requests)} pull requests, {sum(1 for pr in pull_requests if pr['status'] == 'MERGED')} merged"
    )
    return pull_requests, pr_comments


def generate_all_data() -> Dict[str, Any]:
    """Generate all data for the application with comprehensive validation and timeline constraints"""
    try:
        print("Generating project data...")
        projects = data_generator.generate_project_base_data()
        project_details = data_generator.generate_project_details(projects)

        print("Calculating design phase completion times...")
        design_completion_times = enforce_design_sprint_timeline(projects)

        print("Generating design events...")
        design_events = generate_design_events(projects)

        print("Generating Jira items...")
        jira_items = generate_jira_items(projects)

        print("Generating and adjusting sprints...")
        sprints, sprint_jira_map = generate_sprints(projects, jira_items)
        sprints = adjust_sprint_dates(sprints, jira_items, design_completion_times)

        print("Adjusting sprint and Jira timelines...")
        adjusted_sprints, adjusted_jiras = adjust_sprint_and_jira_timelines(
            design_events, sprints, jira_items, sprint_jira_map
        )

        print("Generating and adjusting commits...")
        commits = generate_commits(projects, adjusted_jiras)
        commits = adjust_commit_dates(commits, adjusted_jiras)

        print("Generating and adjusting pull requests...")
        pull_requests, pr_comments = generate_pull_requests(project_details, commits)
        pull_requests = adjust_pr_dates(pull_requests, commits)

        print("Generating CICD events...")
        project_ids = list(projects.keys())
        cicd_events = generate_cicd_events(pull_requests, project_ids)

        print("Generating P0 bugs...")
        bugs = generate_bugs_for_builds(cicd_events)

        # Combine all data
        all_data = {
            "projects": project_details,
            "design_events": design_events,
            "jira_items": adjusted_jiras,
            "commits": commits,
            "sprints": adjusted_sprints,
            "pull_requests": pull_requests,
            "pr_comments": pr_comments,
            "cicd_events": cicd_events,
            "bugs": bugs,
            "relationships": {
                "sprint_jira_associations": sprint_jira_map,
            },
        }

        print("Verifying data consistency...")

        # Verify temporal consistency with enhanced Jira validation
        temporal_errors = verify_temporal_consistency(commits, adjusted_jiras)
        if temporal_errors:
            print("Temporal consistency errors:")
            for error in temporal_errors:
                print(f"  - {error}")

        # Verify project references
        project_errors = verify_project_references(all_data)
        if project_errors:
            print("Project reference errors:")
            for error in project_errors:
                print(f"  - {error}")

        # Verify Jira references
        jira_errors = verify_jira_references(all_data)
        if jira_errors:
            print("Jira reference errors:")
            for error in jira_errors:
                print(f"  - {error}")

        # Verify timeline constraints with new commit-Jira validation
        with db_manager.get_session() as session:
            timeline_validation = validate_all_timelines(session)
            timeline_errors = []
            for category, errors in timeline_validation.items():
                if errors:
                    timeline_errors.extend(errors)

            if timeline_errors:
                print("Timeline constraint errors:")
                for error in timeline_errors:
                    print(f"  - {error}")

        # Special validation for commit-Jira completion dates
        commit_jira_errors = validate_commit_jira_completion_dates(
            {"commits": commits, "jira_items": adjusted_jiras}
        )
        if commit_jira_errors:
            print("Commit-Jira completion date errors:")
            for error in commit_jira_errors:
                print(f"  - {error}")

        # Add CICD relationship validation
        cicd_relationship_errors = validate_cicd_relationships(all_data)
        if cicd_relationship_errors:
            print("CICD relationship errors:")
            for error in cicd_relationship_errors:
                print(f"  - {error}")

        # New bug validations
        bug_validation_errors = []
        for bug in bugs:
            errors = validate_bug_data(bug)
            bug_validation_errors.extend(errors)

        build_association_errors = validate_bug_build_association(bugs, cicd_events)
        bug_validation_errors.extend(build_association_errors)

        # Add bug timeline validation
        bug_timeline_errors = validate_bug_timelines(bugs, cicd_events)

        with db_manager.get_session() as session:
            timeline_validation = validate_all_timelines(session)
            timeline_errors = []
            for category, errors in timeline_validation.items():
                if errors:
                    timeline_errors.extend(errors)

        # Verify bug data consistency
        bug_counts = {
            "total": len(all_data["bugs"]),
            "main_branch": sum(
                1
                for b in all_data["bugs"]
                if any(
                    e["branch"] == "main" and e["build_id"] == b["build_id"]
                    for e in all_data["cicd_events"]
                )
            ),
            "other_branches": sum(
                1
                for b in all_data["bugs"]
                if any(
                    e["branch"] != "main" and e["build_id"] == b["build_id"]
                    for e in all_data["cicd_events"]
                )
            ),
        }

        print("\nBug generation statistics:")
        print(f"Total bugs: {bug_counts['total']}")
        print(f"Bugs on main branch: {bug_counts['main_branch']}")
        print(f"Bugs on other branches: {bug_counts['other_branches']}")

        print(
            f"Data generation completed successfully with {len(bugs)} P0 bugs generated"
        )
        print(
            f"- Bugs on main branch: {sum(1 for b in bugs if any(e['branch'] == 'main' and e['build_id'] == b['build_id'] for e in cicd_events))}"
        )
        print(
            f"- Bugs on other branches: {sum(1 for b in bugs if any(e['branch'] != 'main' and e['build_id'] == b['build_id'] for e in cicd_events))}"
        )

        # Combine all errors
        all_errors = (
            temporal_errors
            + project_errors
            + jira_errors
            + timeline_errors
            + commit_jira_errors
            + cicd_relationship_errors
            + bug_validation_errors
            + bug_timeline_errors
        )

        if all_errors:
            raise ValueError(f"Found {len(all_errors)} data consistency errors")

        print("Data generation completed successfully")
        return all_data

    except Exception as e:
        print(f"Error generating data: {str(e)}")
        raise


def get_sample_data() -> Dict[str, Any]:
    """Get sample data with validation"""
    try:
        print("Starting sample data generation...")

        # Generate data using the enhanced generate_all_data function
        all_data = generate_all_data()

        print("Performing final validation checks...")

        # Verify required keys exist
        required_keys = {
            "projects",
            "design_events",
            "jira_items",
            "commits",
            "sprints",
            "relationships",
            "cicd_events",
            "bugs",
        }
        missing_keys = required_keys - set(all_data.keys())
        if missing_keys:
            raise ValueError(f"Missing required data sections: {missing_keys}")

        # Verify relationships structure
        required_relationships = {
            "sprint_jira_associations",  # Removed cicd_commit_associations
        }
        missing_relationships = required_relationships - set(
            all_data["relationships"].keys()
        )
        if missing_relationships:
            raise ValueError(
                f"Missing required relationship maps: {missing_relationships}"
            )

        # Verify data types
        type_checks = {
            "projects": list,
            "commits": list,
            "relationships": dict,
            "bugs": list,
        }
        for key, expected_type in type_checks.items():
            if not isinstance(all_data[key], expected_type):
                raise TypeError(
                    f"Invalid type for {key}: expected {expected_type}, got {type(all_data[key])}"
                )

        print("Sample data generation and validation completed successfully")
        return all_data

    except Exception as e:
        print(f"Error in get_sample_data: {str(e)}")
        raise


def enforce_design_sprint_timeline(
    projects: Dict[str, Dict[str, Any]]
) -> Dict[str, datetime]:
    """Calculate and enforce design phase completion times for each project"""
    design_completion_times = {}

    for proj_id, details in projects.items():
        # Set design phase to complete in first 2-3 weeks
        design_duration = timedelta(days=randint(14, 21))
        design_completion_times[proj_id] = details["start_date"] + design_duration

    return design_completion_times


def adjust_sprint_dates(
    sprints: List[Dict[str, Any]],
    jira_items: List[Dict[str, Any]],
    design_completion_times: Dict[str, datetime],
) -> List[Dict[str, Any]]:
    """Adjust sprint dates based on Jira timelines and design completion"""
    project_jiras = {}
    for jira in jira_items:
        if jira["event_id"] not in project_jiras:
            project_jiras[jira["event_id"]] = []
        project_jiras[jira["event_id"]].append(jira)

    adjusted_sprints = []
    for sprint in sprints:
        proj_id = sprint["event_id"]
        design_completion = design_completion_times.get(proj_id)

        if design_completion:
            # Ensure sprint starts after design completion
            sprint_start = max(
                design_completion + timedelta(days=1), sprint["start_date"]
            )
            sprint["start_date"] = sprint_start

            # Adjust sprint end date based on Jira completions
            sprint_jiras = [
                j
                for j in project_jiras.get(proj_id, [])
                if j.get("sprint_id") == sprint["id"]
            ]
            if sprint_jiras:
                latest_completion = max(
                    j["completed_date"] for j in sprint_jiras if j.get("completed_date")
                )
                sprint["end_date"] = latest_completion

        adjusted_sprints.append(sprint)

    return adjusted_sprints


def adjust_pr_dates(
    pull_requests: List[Dict[str, Any]], commits: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Adjust PR dates to ensure they start after commits"""
    commit_times = {(c["id"], c["timestamp"]): c["timestamp"] for c in commits}

    adjusted_prs = []
    for pr in pull_requests:
        commit_time = commit_times.get((pr["commit_id"], pr["commit_timestamp"]))
        if commit_time:
            # Set PR creation time to commit time plus random minutes
            pr["created_at"] = commit_time + timedelta(minutes=randint(5, 30))
            if pr["status"] == PRStatus.MERGED:
                pr["merged_at"] = pr["created_at"] + timedelta(hours=randint(1, 24))
        adjusted_prs.append(pr)

    return adjusted_prs


def enforce_timeline_constraints(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce all timeline constraints on the data"""
    # Get design completion times
    design_completion_times = enforce_design_sprint_timeline(all_data["projects"])

    # Adjust dates for all entities
    all_data["sprints"] = adjust_sprint_dates(
        all_data["sprints"], all_data["jira_items"], design_completion_times
    )

    all_data["commits"] = adjust_commit_dates(
        all_data["commits"], all_data["jira_items"]
    )

    all_data["pull_requests"] = adjust_pr_dates(
        all_data["pull_requests"], all_data["commits"]
    )

    return all_data


def adjust_sprint_and_jira_timelines(
    design_events: List[Dict[str, Any]],
    sprints: List[Dict[str, Any]],
    jira_items: List[Dict[str, Any]],
    sprint_jira_associations: Dict[str, List[str]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Adjust sprint start dates and JIRA dates to maintain proper temporal consistency:
    1. Sprints cannot start until all design items for their project are complete
    2. JIRA items must start after their associated sprint's start date

    Args:
        design_events (list): List of design event dictionaries
        sprints (list): List of sprint dictionaries
        jira_items (list): List of JIRA item dictionaries
        sprint_jira_associations (dict): Dictionary mapping sprint IDs to lists of JIRA IDs

    Returns:
        tuple: (adjusted_sprints, adjusted_jiras)
    """
    from datetime import timedelta

    # Get the latest design completion time for each project
    project_design_completion = {}
    for event in design_events:
        project_id = event["event_id"]  # Using event_id for design events
        event_timestamp = event["timestamp"]

        if project_id not in project_design_completion:
            project_design_completion[project_id] = event_timestamp
        else:
            project_design_completion[project_id] = max(
                project_design_completion[project_id], event_timestamp
            )

    # Create a reverse mapping of JIRA ID to sprint IDs
    jira_to_sprints = {}
    for sprint_id, jira_ids in sprint_jira_associations.items():
        for jira_id in jira_ids:
            if jira_id not in jira_to_sprints:
                jira_to_sprints[jira_id] = []
            jira_to_sprints[jira_id].append(sprint_id)

    # Step 1: Adjust sprint start dates based on design completion
    adjusted_sprints = []
    sprint_start_dates = {}  # Keep track of sprint start dates for JIRA adjustment

    for sprint in sorted(sprints, key=lambda x: x["start_date"]):
        project_id = sprint["event_id"]
        design_completion = project_design_completion.get(project_id)

        if design_completion:
            # Ensure sprint starts after design completion
            new_start_date = max(
                sprint["start_date"], design_completion + timedelta(days=1)
            )

            # Adjust end date to maintain same duration
            duration = sprint["end_date"] - sprint["start_date"]
            new_end_date = new_start_date + duration

            adjusted_sprint = sprint.copy()
            adjusted_sprint["start_date"] = new_start_date
            adjusted_sprint["end_date"] = new_end_date

            sprint_start_dates[sprint["id"]] = new_start_date
        else:
            # If no design events found, keep original dates
            adjusted_sprint = sprint.copy()
            sprint_start_dates[sprint["id"]] = sprint["start_date"]

        adjusted_sprints.append(adjusted_sprint)

    # Step 2: Adjust JIRA dates based on sprint associations
    adjusted_jiras = []

    for jira in jira_items:
        jira_id = jira["id"]
        associated_sprints = jira_to_sprints.get(jira_id, [])

        if associated_sprints:
            # Find the earliest associated sprint start date
            earliest_sprint_start = min(
                sprint_start_dates[sprint_id] for sprint_id in associated_sprints
            )

            adjusted_jira = jira.copy()

            # Ensure JIRA created date is not before sprint start
            if jira["created_date"] < earliest_sprint_start:
                adjusted_jira["created_date"] = earliest_sprint_start

                # If completion date exists, maintain the same duration
                if jira.get("completed_date"):
                    original_duration = jira["completed_date"] - jira["created_date"]
                    adjusted_jira["completed_date"] = (
                        earliest_sprint_start + original_duration
                    )

            adjusted_jiras.append(adjusted_jira)
        else:
            # If no sprint associations, keep original dates
            adjusted_jiras.append(jira.copy())

    # Perform final validation
    validation_errors = []

    # Validate sprint dates against design completion
    for sprint in adjusted_sprints:
        design_completion = project_design_completion.get(sprint["event_id"])
        if design_completion and sprint["start_date"] < design_completion:
            validation_errors.append(
                f"Sprint {sprint['id']} still starts before design completion for project {sprint['event_id']}"
            )

    # Validate JIRA dates against sprint dates
    for jira in adjusted_jiras:
        associated_sprints = jira_to_sprints.get(jira["id"], [])
        for sprint_id in associated_sprints:
            sprint_start = sprint_start_dates[sprint_id]
            if jira["created_date"] < sprint_start:
                validation_errors.append(
                    f"JIRA {jira['id']} still starts before its associated sprint {sprint_id}"
                )

    if validation_errors:
        raise ValueError(
            f"Timeline adjustment failed validation:\n" + "\n".join(validation_errors)
        )

    return adjusted_sprints, adjusted_jiras


def generate_cicd_events(
    pull_requests: List[Dict[str, Any]], project_ids: List[str]
) -> List[Dict[str, Any]]:
    """
    Generate CICD events based on pull requests and manual triggers

    Args:
        pull_requests: List of pull request dictionaries
        project_ids: List of valid project IDs for manual builds
    """
    cicd_events = []

    # Helper function to generate release version
    def generate_release_version(env: str) -> str:
        major = random.randint(1, 3)
        minor = random.randint(0, 9)
        patch = random.randint(0, 99)
        return f"{env}:{major}.{minor}.{patch}"

    # Helper function to generate build duration
    def generate_build_duration() -> int:
        return random.randint(300, 1800)  # 5-30 minutes in seconds

    # Generate automatic builds for merged PRs
    for pr in pull_requests:
        if pr["status"] == PRStatus.MERGED and pr["merged_at"]:
            # For each merged PR, create builds for different environments
            prev_timestamp = pr["merged_at"]

            for env in Environment:
                # Skip some environments randomly
                if (
                    env in [Environment.UAT, Environment.PRODUCTION]
                    and random.random() < 0.3
                ):
                    continue

                build_id = f"build-{uuid.uuid4().hex[:8]}"
                # Add some time after the previous event
                timestamp = prev_timestamp + timedelta(minutes=random.randint(5, 15))

                # Determine build status (higher success rate for lower environments)
                success_rate = {
                    Environment.DEV: 0.9,
                    Environment.QA: 0.85,
                    Environment.STAGING: 0.8,
                    Environment.UAT: 0.75,
                    Environment.PRODUCTION: 0.7,
                }

                status = (
                    BuildStatus.SUCCESS
                    if random.random() < success_rate[env]
                    else BuildStatus.FAILURE
                )

                cicd_events.append(
                    {
                        "event_id": pr["id"],
                        "timestamp": timestamp,
                        "project_id": pr["project_id"],  # Add project_id from PR
                        "environment": env.value,
                        "event_type": "build",
                        "build_id": build_id,
                        "status": status.value,
                        "duration_seconds": generate_build_duration(),
                        "branch": pr["branch_to"],
                        "tag": None,
                        "mode": BuildMode.AUTOMATIC.value,
                        "release_version": generate_release_version(env.value),
                    }
                )

                prev_timestamp = timestamp

    # Generate manual builds (not associated with PRs)
    num_manual_builds = (
        len(pull_requests) // 2
    )  # Create manual builds for about half the number of PRs

    branches = ["main", "develop", "staging", "feature/xyz", "hotfix/abc"]
    tags = [None, "v1.0.0", "v1.1.0", "v2.0.0"]

    base_timestamp = datetime(2024, 1, 1)

    for _ in range(num_manual_builds):
        branch = random.choice(branches)
        env = random.choice(list(Environment))
        tag = random.choice(tags)

        timestamp = base_timestamp + timedelta(
            days=random.randint(0, 90),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )

        cicd_events.append(
            {
                "event_id": f"manual-{uuid.uuid4().hex[:8]}",
                "project_id": random.choice(
                    project_ids
                ),  # Randomly select a project_id
                "timestamp": timestamp,
                "environment": env.value,
                "event_type": "build",
                "build_id": f"build-{uuid.uuid4().hex[:8]}",
                "status": random.choice(list(BuildStatus)).value,
                "duration_seconds": generate_build_duration(),
                "branch": branch,
                "tag": tag,
                "mode": BuildMode.MANUAL.value,
                "release_version": generate_release_version(env.value),
            }
        )

    # Sort all events by timestamp
    cicd_events.sort(key=lambda x: x["timestamp"])
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
            status = BugStatus.OPEN

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
