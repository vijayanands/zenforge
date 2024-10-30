# events_data_generator.py
import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
import random

import numpy as np

from model.sdlc_events import StageType


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

    def generate_project_details(
        self, projects: Dict[str, Dict[str, Any]]
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

    def get_completion_probability(
        self, completion_state: str, event_type: str
    ) -> float:
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

    def get_design_event_status(
        self, completion_state: str, phase: str
    ) -> Dict[str, Any]:
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

    def generate_date_sequence(
        self,
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

    def generate_unique_id(self, prefix: str = "") -> str:
        """Generate a unique identifier"""
        return f"{prefix}{uuid.uuid4().hex[:8]}"

    def get_random_jira_ids(
        self,
        project_id: str,
        available_jiras: List[str],
        min_count: int = 1,
        max_count: int = 5,
    ) -> List[str]:
        """Get random jira IDs for a project"""
        project_jiras = [j for j in available_jiras if j.startswith(project_id)]
        count = min(random.randint(min_count, max_count), len(project_jiras))
        return random.sample(project_jiras, count) if project_jiras else []

    def get_random_commit_ids(
        self, available_commits: List[str], min_count: int = 1, max_count: int = 3
    ) -> List[str]:
        """Get random commit IDs"""
        count = min(random.randint(min_count, max_count), len(available_commits))
        return random.sample(available_commits, count) if available_commits else []

    def generate_commit_metrics(self) -> Tuple[int, int, int, float, float]:
        """Generate metrics for a code commit"""
        files_changed = np.random.randint(1, 20)
        lines_added = np.random.randint(10, 500)
        lines_removed = np.random.randint(5, 300)
        code_coverage = np.random.uniform(75, 98)
        lint_score = np.random.uniform(80, 99)
        return files_changed, lines_added, lines_removed, code_coverage, lint_score

    def get_jira_status(self, completion_state: str) -> str:
        """Get Jira item status based on completion state"""
        if completion_state in ["design_and_sprint", "pre_release", "all_complete"]:
            return "Done"
        elif completion_state == "design_only":
            return np.random.choice(["In Progress", "To Do", "Done"], p=[0.4, 0.4, 0.2])
        else:  # mixed or mixed_all
            return np.random.choice(
                ["To Do", "In Progress", "Done", "Blocked"], p=[0.3, 0.3, 0.2, 0.2]
            )

    def get_commit_status(self, completion_state: str) -> Dict[str, Any]:
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

    def get_build_ids_by_project(
        self, cicd_events: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Get build IDs grouped by project"""
        build_ids = {}
        for cicd in cicd_events:
            if cicd["event_id"] not in build_ids:
                build_ids[cicd["event_id"]] = []
            if cicd.get("build_id"):  # Using get() to safely handle missing build_id
                build_ids[cicd["event_id"]].append(cicd["build_id"])
        return build_ids

    def generate_root_cause(self) -> str:
        """Generate random root cause for bugs"""
        causes = [
            "Code logic error",
            "Database deadlock",
            "Memory leak",
            "Race condition",
            "Configuration error",
            "Third-party API failure",
            "Network timeout",
            "Input validation",
            "Cache inconsistency",
            "Resource exhaustion",
            "Concurrency issue",
            "Environmental mismatch",
        ]
        return np.random.choice(causes)

    def get_cicd_status(self, completion_state: str) -> Dict[str, Any]:
        """Get CI/CD event status based on completion state"""
        if completion_state in ["pre_release", "all_complete"]:
            return {
                "status": "success",
                "metrics": {
                    "test_coverage": np.random.uniform(90, 98),
                    "failed_tests": 0,
                    "security_issues": 0,
                },
            }
        elif completion_state == "design_and_sprint":
            return {
                "status": np.random.choice(["success", "failed"], p=[0.8, 0.2]),
                "metrics": {
                    "test_coverage": np.random.uniform(80, 95),
                    "failed_tests": np.random.randint(0, 5),
                    "security_issues": np.random.randint(0, 3),
                },
            }
        else:
            return {
                "status": np.random.choice(["success", "failed"], p=[0.6, 0.4]),
                "metrics": {
                    "test_coverage": np.random.uniform(70, 90),
                    "failed_tests": np.random.randint(0, 10),
                    "security_issues": np.random.randint(0, 5),
                },
            }

    def associate_jiras_with_sprints(
        self, sprint_data: List[Dict[str, Any]], jira_data: List[Dict[str, Any]]
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

    def associate_commits_with_cicd(
        self, cicd_data: List[Dict[str, Any]], commit_data: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Create associations between CICD events and commits"""
        cicd_commit_map = {}
        project_commits = {}

        # Group commits by project
        for commit in commit_data:
            if commit["event_id"] not in project_commits:
                project_commits[commit["event_id"]] = []
            project_commits[commit["event_id"]].append(commit["id"])

        # Associate commits with CICD events based on timestamp
        for cicd in cicd_data:
            project_id = cicd["event_id"]
            if project_id in project_commits:
                # Get commits that happened before this CICD event
                available_commits = [
                    commit["id"]
                    for commit in commit_data
                    if commit["event_id"] == project_id
                    and commit["timestamp"] <= cicd["timestamp"]
                ]

                if available_commits:
                    # Select 1-5 commits for this CICD event
                    commit_count = random.randint(1, min(5, len(available_commits)))
                    cicd_commit_map[cicd["id"]] = random.sample(
                        available_commits, commit_count
                    )

        return cicd_commit_map

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

    def get_sequential_story_points(
        self, num_items: int, total_points: int
    ) -> List[int]:
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

    def calculate_project_progress(
        self, completion_state: str, elapsed_days: int, total_days: int
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
    """Generate design events for all projects with proper Jira linking and status transitions"""
    design_events = []
    design_phases = data_generator.generate_design_phases()

    for proj_id, details in projects.items():
        start_date = details["start_date"]
        completion_state = details["completion_state"]

        for phase in design_phases:
            phase_status = data_generator.get_design_event_status(
                completion_state, phase
            )
            jira_id = f"{proj_id}-{phase.upper()}-1"  # Matches the ID format from generate_design_related_jiras

            # Initial event (START)
            design_events.append(
                {
                    "id": f"{proj_id}-{phase.upper()}",
                    "event_id": proj_id,
                    "design_type": phase,
                    "stage": StageType.START,
                    "timestamp": start_date,
                    "author": f"{phase.split('_')[0]}@example.com",
                    "jira": jira_id,
                    "stakeholders": data_generator.generate_stakeholders(),
                    "review_status": "Pending",
                }
            )

            current_date = start_date + timedelta(
                days=2
            )  # Base date for subsequent events

            if phase_status["stage"] != "start":
                if phase_status["stage"] in ["blocked", "resume"]:
                    # Generate blocked-resume cycles
                    num_revisions = np.random.randint(1, 3)
                    days_between_events = np.random.randint(
                        2, 4
                    )  # 2-4 days between status changes

                    for rev_idx in range(num_revisions):
                        # Blocked state
                        design_events.append(
                            {
                                "id": f"{proj_id}-{phase.upper()}-BLOCK{rev_idx + 1}",
                                "event_id": proj_id,
                                "design_type": phase,
                                "stage": StageType.BLOCKED,
                                "timestamp": current_date,
                                "author": f"{phase.split('_')[0]}@example.com",
                                "jira": jira_id,
                                "stakeholders": data_generator.generate_stakeholders(),
                                "review_status": "In Review",
                            }
                        )
                        current_date += timedelta(days=days_between_events)

                        # Resume state
                        design_events.append(
                            {
                                "id": f"{proj_id}-{phase.upper()}-RESUME{rev_idx + 1}",
                                "event_id": proj_id,
                                "design_type": phase,
                                "stage": StageType.RESUME,
                                "timestamp": current_date,
                                "author": f"{phase.split('_')[0]}@example.com",
                                "jira": jira_id,
                                "stakeholders": data_generator.generate_stakeholders(),
                                "review_status": "In Review",
                            }
                        )
                        current_date += timedelta(days=days_between_events)

                # Final completion event (END)
                if phase_status["stage"] == "end" or completion_state in [
                    "design_only",
                    "design_and_sprint",
                    "pre_release",
                    "all_complete",
                ]:
                    final_date = max(
                        current_date, start_date + timedelta(days=7)
                    )  # Ensure minimum 7 days for completion
                    design_events.append(
                        {
                            "id": f"{proj_id}-{phase.upper()}-FINAL",
                            "event_id": proj_id,
                            "design_type": phase,
                            "stage": StageType.END,
                            "timestamp": final_date,
                            "author": f"{phase.split('_')[0]}@example.com",
                            "jira": jira_id,
                            "stakeholders": data_generator.generate_stakeholders(),
                            "review_status": phase_status["review_status"],
                        }
                    )

            # Move start date for next phase
            start_date += timedelta(
                days=15
            )  # Each phase starts 15 days after the previous one

    # Sort all events by timestamp to ensure chronological order
    design_events.sort(key=lambda x: (x["event_id"], x["design_type"], x["timestamp"]))

    return design_events


def get_design_event_status(completion_state: str, phase: str) -> Dict[str, Any]:
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
    """Generate Jira items for all projects, including design, epics, stories and tasks"""
    # First generate design-related Jiras
    all_jiras = generate_design_related_jiras(projects)

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        start_date = details["start_date"] + timedelta(days=13)

        # Generate Epics
        for epic_num in range(1, 6):
            status = data_generator.get_jira_status(completion_state)
            epic_completion = (
                start_date + timedelta(days=epic_num + 25) if status == "Done" else None
            )

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
                "actual_hours": None,
            }
            all_jiras.append(epic_data)

            # Generate Stories for Epic
            for story_num in range(1, 6):
                story_status = data_generator.get_jira_status(completion_state)
                story_completion = (
                    start_date + timedelta(days=epic_num + story_num + 20)
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
                    "created_date": start_date + timedelta(days=epic_num + story_num),
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
                    actual_hours = (
                        int(estimated_hours * np.random.uniform(0.8, 1.3))
                        if task_status == "Done"
                        else None
                    )
                    task_completion = (
                        start_date
                        + timedelta(days=epic_num + story_num + task_num + 15)
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
                        "created_date": start_date
                        + timedelta(days=epic_num + story_num + task_num),
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
                jira["completed_date"] = jira["created_date"] + timedelta(
                    days=np.random.randint(5, 15)
                )
                if jira["type"] == "Task":
                    jira["actual_hours"] = int(
                        jira["estimated_hours"] * np.random.uniform(0.8, 1.3)
                    )

    return all_jiras


def generate_commits(
    projects: Dict[str, Dict[str, Any]], jira_items: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Generate code commits with proper timestamps and Jira associations"""
    commits = []

    # Create a map of available Jira IDs per project
    project_jiras = {}
    for jira in jira_items:
        if jira["event_id"] not in project_jiras:
            project_jiras[jira["event_id"]] = []
        project_jiras[jira["event_id"]].append(jira["id"])

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        available_jiras = project_jiras.get(proj_id, [])

        if not available_jiras:
            continue

        num_commits = (
            200
            if completion_state in ["pre_release", "all_complete"]
            else np.random.randint(50, 150)
        )
        start_date = details["start_date"] + timedelta(
            days=20
        )  # Start commits after design phase

        for i in range(num_commits):
            # Calculate commit date - ensure proper chronological order
            commit_date = start_date + timedelta(days=i // 4)  # Up to 4 commits per day

            # Assign a random Jira ID from the project
            associated_jira = random.choice(available_jiras)

            commit_metrics = data_generator.get_commit_status(completion_state)
            files_changed, lines_added, lines_removed, _, _ = (
                data_generator.generate_commit_metrics()
            )

            commit = {
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
                "jira_id": associated_jira,
            }

            commits.append(commit)

    # Sort all commits by timestamp
    commits.sort(key=lambda x: x["timestamp"])
    return commits


# Update generate_cicd_events function
def generate_cicd_events(
    projects: Dict[str, Dict[str, Any]], commits: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    """Generate CI/CD events ensuring proper temporal relationships with commits"""
    cicd_events = []
    cicd_commit_map = {}
    environments = ["dev", "staging", "qa", "uat", "production"]

    # Create a map of project to available commits with timestamps
    project_commits = {}
    for commit in commits:
        if commit["event_id"] not in project_commits:
            project_commits[commit["event_id"]] = []
        project_commits[commit["event_id"]].append(
            {"id": commit["id"], "timestamp": commit["timestamp"]}
        )

    # Track used build IDs
    used_build_ids = set()

    for proj_id, details in projects.items():
        if proj_id not in project_commits or not project_commits[proj_id]:
            continue

        completion_state = details["completion_state"]

        # Sort project commits by timestamp
        proj_commits = sorted(project_commits[proj_id], key=lambda x: x["timestamp"])

        # Start CICD events one day after first commit
        current_date = proj_commits[0]["timestamp"] + timedelta(days=1)
        build_counter = 0

        while build_counter < 50:
            # Find commits that happened before this build
            valid_commits = [
                commit for commit in proj_commits if commit["timestamp"] < current_date
            ]

            if not valid_commits:
                current_date += timedelta(days=1)
                continue

            for env in environments:
                cicd_status = data_generator.get_cicd_status(completion_state)

                # Generate unique build ID
                build_id = None
                while True:
                    build_id = f"build_{uuid.uuid4().hex[:8]}"
                    if build_id not in used_build_ids:
                        used_build_ids.add(build_id)
                        break

                # Select recent commits for this build
                recent_commits = sorted(
                    valid_commits, key=lambda x: x["timestamp"], reverse=True
                )[:5]
                num_commits = random.randint(1, len(recent_commits))
                selected_commits = recent_commits[:num_commits]

                # Create build event
                build_event_id = f"cicd_{uuid.uuid4().hex[:8]}"
                build_event = {
                    "id": build_event_id,
                    "event_id": proj_id,
                    "timestamp": current_date,
                    "environment": env,
                    "event_type": "build",
                    "build_id": build_id,
                    "status": cicd_status["status"],
                    "duration_seconds": np.random.randint(180, 900),
                    "metrics": cicd_status["metrics"],
                    "reason": None,
                }
                cicd_events.append(build_event)
                cicd_commit_map[build_event_id] = [
                    commit["id"] for commit in selected_commits
                ]

                # Handle successful builds
                if cicd_status["status"] == "success":
                    deploy_success = completion_state in ["pre_release", "all_complete"]

                    # Create deployment event
                    deploy_event_id = f"cicd_{uuid.uuid4().hex[:8]}"
                    deploy_event = {
                        "id": deploy_event_id,
                        "event_id": proj_id,
                        "timestamp": current_date + timedelta(minutes=15),
                        "environment": env,
                        "event_type": "deployment",
                        "build_id": f"build_{uuid.uuid4().hex[:8]}",
                        "status": "success" if deploy_success else "failed",
                        "duration_seconds": np.random.randint(300, 1200),
                        "metrics": cicd_status["metrics"],
                        "reason": None,
                    }
                    cicd_events.append(deploy_event)
                    cicd_commit_map[deploy_event_id] = [
                        commit["id"] for commit in selected_commits
                    ]

                    # Handle failed deployments
                    if not deploy_success:
                        rollback_event_id = f"cicd_{uuid.uuid4().hex[:8]}"
                        rollback_event = {
                            "id": rollback_event_id,
                            "event_id": proj_id,
                            "timestamp": current_date + timedelta(minutes=30),
                            "environment": env,
                            "event_type": "rollback",
                            "build_id": f"build_{uuid.uuid4().hex[:8]}",
                            "status": "success",
                            "duration_seconds": np.random.randint(180, 600),
                            "metrics": cicd_status["metrics"],
                            "reason": data_generator.generate_root_cause(),
                        }
                        cicd_events.append(rollback_event)
                        cicd_commit_map[rollback_event_id] = [
                            commit["id"] for commit in selected_commits
                        ]

            build_counter += 1
            current_date += timedelta(days=1)

    return cicd_events, cicd_commit_map


def generate_bugs(
    projects: Dict[str, Dict[str, Any]],
    jira_items: List[Dict[str, Any]],
    cicd_events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Generate bugs for all projects with Jira and CICD associations"""
    bugs = []
    bug_types = ["Security", "Performance", "Functionality", "Data", "UI/UX"]
    impact_areas = ["Customer", "Internal", "Integration", "Infrastructure"]

    # Create maps for available Jiras and build IDs by project
    project_jiras = {}
    for jira in jira_items:
        if jira["event_id"] not in project_jiras:
            project_jiras[jira["event_id"]] = []
        project_jiras[jira["event_id"]].append(jira["id"])

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

            status = (
                "Fixed"
                if completion_state in ["pre_release", "all_complete"]
                else np.random.choice(
                    ["Fixed", "In Progress", "Open"], p=[0.6, 0.3, 0.1]
                )
            )

            # Associate with a random Jira and build ID
            associated_jira = random.choice(available_jiras)
            associated_build = random.choice(available_builds)

            bugs.append(
                {
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
                    "resolved_date": (
                        bug_date + timedelta(hours=resolution_time)
                        if status == "Fixed"
                        else None
                    ),
                    "resolution_time_hours": (
                        resolution_time if status == "Fixed" else None
                    ),
                    "assigned_to": f"dev{np.random.randint(1, 6)}@example.com",
                    "environment_found": np.random.choice(
                        ["Production", "Staging", "QA"]
                    ),
                    "number_of_customers_affected": (
                        np.random.randint(1, 1000) if np.random.random() > 0.5 else 0
                    ),
                    "root_cause": data_generator.generate_root_cause(),
                    "fix_version": f"{proj_id.lower()}-v1.{np.random.randint(0, 9)}.{np.random.randint(0, 9)}",
                    "regression_test_status": (
                        "Passed" if status == "Fixed" else "In Progress"
                    ),
                    "customer_communication_needed": np.random.choice([True, False]),
                    "postmortem_link": (
                        f"https://wiki.example.com/postmortem/{proj_id}-BUG-{i + 1}"
                        if status == "Fixed"
                        else None
                    ),
                }
            )

    return bugs


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
        project_completion = details["start_date"] + timedelta(
            weeks=12
        )  # Assuming 12 weeks project duration

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


def generate_team_metrics(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate team metrics for all projects"""
    team_metrics = []

    for proj_id, details in projects.items():
        completion_state = details["completion_state"]
        start_date = details["start_date"]

        for week in range(12):
            week_start = start_date + timedelta(weeks=week)

            # Adjust metrics based on completion state
            is_mature = completion_state in ["pre_release", "all_complete"] or (
                completion_state in ["design_and_sprint", "mixed_all"] and week > 6
            )

            team_metrics.append(
                {
                    "id": f"{proj_id}-TM-{week + 1}",
                    "event_id": proj_id,
                    "week_starting": week_start,
                    "team_size": details["team_size"],
                    "velocity": (
                        np.random.randint(30, 40)
                        if is_mature
                        else np.random.randint(20, 30)
                    ),
                    "code_review_turnaround_hours": (
                        np.random.uniform(2, 24)
                        if is_mature
                        else np.random.uniform(24, 48)
                    ),
                    "build_success_rate": (
                        np.random.uniform(95, 100)
                        if is_mature
                        else np.random.uniform(85, 95)
                    ),
                    "test_coverage": (
                        np.random.uniform(85, 95)
                        if is_mature
                        else np.random.uniform(75, 85)
                    ),
                    "bugs_reported": (
                        np.random.randint(1, 5)
                        if is_mature
                        else np.random.randint(5, 10)
                    ),
                    "bugs_fixed": (
                        np.random.randint(3, 8)
                        if is_mature
                        else np.random.randint(1, 5)
                    ),
                    "technical_debt_hours": (
                        np.random.randint(5, 20)
                        if is_mature
                        else np.random.randint(20, 40)
                    ),
                    "pair_programming_hours": (
                        np.random.randint(10, 20)
                        if is_mature
                        else np.random.randint(5, 10)
                    ),
                    "code_review_comments": (
                        np.random.randint(20, 50)
                        if is_mature
                        else np.random.randint(50, 100)
                    ),
                    "documentation_updates": (
                        np.random.randint(5, 8)
                        if is_mature
                        else np.random.randint(2, 5)
                    ),
                    "knowledge_sharing_sessions": (
                        np.random.randint(2, 3)
                        if is_mature
                        else np.random.randint(1, 2)
                    ),
                    "team_satisfaction": (
                        np.random.uniform(8, 9.5)
                        if is_mature
                        else np.random.uniform(7, 8)
                    ),
                    "sprint_completion_rate": (
                        np.random.uniform(90, 100)
                        if is_mature
                        else np.random.uniform(70, 90)
                    ),
                }
            )

    return team_metrics


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


def generate_all_data() -> Dict[str, Any]:
    """Generate all data for the application with comprehensive validation"""
    try:
        print("Generating project data...")
        projects = data_generator.generate_project_base_data()
        project_details = data_generator.generate_project_details(projects)

        print("Generating Jira items...")
        jira_items = generate_jira_items(projects)

        print("Generating design events...")
        design_events = generate_design_events(projects)

        print("Generating commits...")
        commits = generate_commits(projects, jira_items)

        print("Generating CICD events...")
        cicd_events, cicd_commit_map = generate_cicd_events(projects, commits)

        print("Generating sprints...")
        sprints, sprint_jira_map = generate_sprints(projects, jira_items)

        print("Generating bugs...")
        bugs = generate_bugs(projects, jira_items, cicd_events)

        print("Generating team metrics...")
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
                "cicd_commit_associations": cicd_commit_map,
            },
        }

        print("Verifying data consistency...")

        # Verify temporal consistency
        temporal_errors = verify_temporal_consistency(
            commits, cicd_events, cicd_commit_map
        )
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

        # Verify data completeness
        for key in [
            "projects",
            "design_events",
            "jira_items",
            "commits",
            "cicd_events",
            "bugs",
            "sprints",
            "team_metrics",
        ]:
            if not all_data[key]:
                print(f"Warning: {key} data is empty")

        all_errors = temporal_errors + project_errors + jira_errors
        if all_errors:
            raise ValueError(f"Found {len(all_errors)} data consistency errors")

        print("Data generation completed successfully")
        return all_data

    except Exception as e:
        print(f"Error generating data: {str(e)}")
        raise


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
            "cicd_events",
            "bugs",
            "sprints",
            "team_metrics",
            "relationships",
        }
        missing_keys = required_keys - set(all_data.keys())
        if missing_keys:
            raise ValueError(f"Missing required data sections: {missing_keys}")

        # Verify relationships structure
        required_relationships = {
            "sprint_jira_associations",
            "cicd_commit_associations",
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
            "cicd_events": list,
            "relationships": dict,
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


def write_sample_data(filename: str = "sample_data.json") -> None:
    """Write sample data to a JSON file"""
    data = get_sample_data()
    with open(filename, "w") as f:
        json.dump(data, f, indent=2, default=str)
    print(f"Sample data written to {filename}")


if __name__ == "__main__":
    write_sample_data()
