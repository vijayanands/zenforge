# events_data_generation_core.py
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Set
import random

import numpy as np

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
                "completion_state": "design_only"
            },
            "PRJ-002": {  # Design and sprint/jira complete
                "title": "Payment Gateway Integration",
                "description": "Implement new payment gateway with support for multiple currencies",
                "start_date": self.base_start_date + timedelta(days=15),
                "complexity": "Medium",
                "team_size": 8,
                "completion_state": "design_and_sprint"
            },
            "PRJ-003": {  # Design, sprint, commit, CICD complete
                "title": "Mobile App Analytics",
                "description": "Add comprehensive analytics and tracking to mobile applications",
                "start_date": self.base_start_date + timedelta(days=30),
                "complexity": "Medium",
                "team_size": 6,
                "completion_state": "pre_release"
            },
            "PRJ-004": {  # Mixed completion states
                "title": "API Gateway Migration",
                "description": "Migrate existing APIs to new gateway with improved security",
                "start_date": self.base_start_date + timedelta(days=45),
                "complexity": "High",
                "team_size": 10,
                "completion_state": "mixed"
            },
            "PRJ-005": {  # All complete, no P0s
                "title": "Data Pipeline Optimization",
                "description": "Optimize existing data pipelines for better performance",
                "start_date": self.base_start_date + timedelta(days=60),
                "complexity": "Medium",
                "team_size": 7,
                "completion_state": "all_complete"
            },
            "PRJ-006": {  # Mixed completion with all types of states
                "title": "Search Service Upgrade",
                "description": "Upgrade search infrastructure with advanced capabilities",
                "start_date": self.base_start_date + timedelta(days=75),
                "complexity": "High",
                "team_size": 9,
                "completion_state": "mixed_all"
            }
        }

    def generate_project_details(self, projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate detailed project information"""
        project_details = []
        for proj_id, details in projects.items():
            project_details.append({
                "id": proj_id,
                "title": details["title"],
                "description": details["description"],
                "start_date": details["start_date"],
                "status": "Completed" if details["completion_state"] == "all_complete" else "In Progress",
                "complexity": details["complexity"],
                "team_size": details["team_size"],
                "estimated_duration_weeks": np.random.randint(12, 24),
                "budget_allocated": np.random.randint(100000, 500000),
                "priority": np.random.choice(["High", "Medium", "Low"], p=[0.5, 0.3, 0.2])
            })
        return project_details

    def generate_design_phases(self) -> List[str]:
        """Generate list of design phases"""
        return [
            "requirements",
            "ux_design",
            "architecture",
            "database_design",
            "api_design",
            "security_review"
        ]

    def generate_stakeholders(self) -> str:
        """Generate random stakeholder combination"""
        stakeholder_groups = [
            "Product,Dev,QA",
            "Dev,Arch",
            "UX,Dev,Product",
            "Dev,Security",
            "Product,QA,Security",
            "Arch,Security,Dev"
        ]
        return np.random.choice(stakeholder_groups)

    def get_completion_probability(self, completion_state: str, event_type: str) -> float:
        """Get probability of completion based on project state and event type"""
        probabilities = {
            "design_only": {
                "design": 1.0,
                "sprint": 0.7,
                "jira": 0.6,
                "commit": 0.5,
                "cicd": 0.4,
                "bug": 0.3
            },
            "design_and_sprint": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 0.7,
                "cicd": 0.6,
                "bug": 0.5
            },
            "pre_release": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 1.0,
                "cicd": 1.0,
                "bug": 0.7
            },
            "mixed": {
                "design": 0.7,
                "sprint": 0.6,
                "jira": 0.5,
                "commit": 0.4,
                "cicd": 0.3,
                "bug": 0.4
            },
            "all_complete": {
                "design": 1.0,
                "sprint": 1.0,
                "jira": 1.0,
                "commit": 1.0,
                "cicd": 1.0,
                "bug": 0.0
            },
            "mixed_all": {
                "design": 0.8,
                "sprint": 0.7,
                "jira": 0.6,
                "commit": 0.5,
                "cicd": 0.4,
                "bug": 0.5
            }
        }
        return probabilities.get(completion_state, {}).get(event_type, 0.5)

    def should_generate_record(self, project_details: Dict[str, Any], event_type: str) -> bool:
        """Determine if a record should be generated based on completion state"""
        completion_prob = self.get_completion_probability(
            project_details["completion_state"],
            event_type
        )
        return np.random.random() < completion_prob

    def get_design_event_status(self, completion_state: str, phase: str) -> Dict[str, Any]:
        """Get design event status based on completion state"""
        if completion_state in ["design_only", "design_and_sprint", "pre_release", "all_complete"]:
            return {
                "stage": "end",
                "review_status": "Approved"
            }
        elif completion_state == "mixed":
            if np.random.random() < 0.7:
                return {
                    "stage": np.random.choice(["end", "blocked", "resume"]),
                    "review_status": np.random.choice(["Approved", "In Review", "Pending"])
                }
            else:
                return {
                    "stage": "start",
                    "review_status": "Pending"
                }
        else:  # mixed_all
            return {
                "stage": np.random.choice(["start", "end", "blocked", "resume"]),
                "review_status": np.random.choice(["Approved", "In Review", "Pending"])
            }

    def generate_date_sequence(self, start_date: datetime, num_events: int,
                               min_days: int = 1, max_days: int = 5) -> List[datetime]:
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

    def get_random_jira_ids(self, project_id: str, available_jiras: List[str],
                            min_count: int = 1, max_count: int = 5) -> List[str]:
        """Get random jira IDs for a project"""
        project_jiras = [j for j in available_jiras if j.startswith(project_id)]
        count = min(random.randint(min_count, max_count), len(project_jiras))
        return random.sample(project_jiras, count) if project_jiras else []

    def get_random_commit_ids(self, available_commits: List[str],
                              min_count: int = 1, max_count: int = 3) -> List[str]:
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
            return np.random.choice(["To Do", "In Progress", "Done", "Blocked"],
                                    p=[0.3, 0.3, 0.2, 0.2])

    def get_commit_status(self, completion_state: str) -> Dict[str, Any]:
        """Get commit related statuses based on completion state"""
        if completion_state in ["pre_release", "all_complete"]:
            return {
                "code_coverage": np.random.uniform(90, 98),
                "lint_score": np.random.uniform(95, 99),
                "review_time_minutes": np.random.randint(10, 60)
            }
        elif completion_state == "design_and_sprint":
            return {
                "code_coverage": np.random.uniform(85, 95),
                "lint_score": np.random.uniform(90, 98),
                "review_time_minutes": np.random.randint(20, 90)
            }
        else:
            return {
                "code_coverage": np.random.uniform(75, 90),
                "lint_score": np.random.uniform(80, 95),
                "review_time_minutes": np.random.randint(30, 120)
            }

    def get_build_ids_by_project(self, cicd_events: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Get build IDs grouped by project"""
        build_ids = {}
        for cicd in cicd_events:
            if cicd['event_id'] not in build_ids:
                build_ids[cicd['event_id']] = []
            if cicd.get('build_id'):  # Using get() to safely handle missing build_id
                build_ids[cicd['event_id']].append(cicd['build_id'])
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
            "Environmental mismatch"
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
                    "security_issues": 0
                }
            }
        elif completion_state == "design_and_sprint":
            return {
                "status": np.random.choice(["success", "failed"], p=[0.8, 0.2]),
                "metrics": {
                    "test_coverage": np.random.uniform(80, 95),
                    "failed_tests": np.random.randint(0, 5),
                    "security_issues": np.random.randint(0, 3)
                }
            }
        else:
            return {
                "status": np.random.choice(["success", "failed"], p=[0.6, 0.4]),
                "metrics": {
                    "test_coverage": np.random.uniform(70, 90),
                    "failed_tests": np.random.randint(0, 10),
                    "security_issues": np.random.randint(0, 5)
                }
            }

    def associate_jiras_with_sprints(self, sprint_data: List[Dict[str, Any]],
                                     jira_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create associations between sprints and jiras"""
        sprint_jira_map = {}
        project_jiras = {}

        # Group jiras by project
        for jira in jira_data:
            if jira['event_id'] not in project_jiras:
                project_jiras[jira['event_id']] = []
            project_jiras[jira['event_id']].append(jira)

        # Associate jiras with sprints based on dates and state
        for sprint in sprint_data:
            project_id = sprint['event_id']
            if project_id in project_jiras:
                available_jiras = project_jiras[project_id]
                sprint_start = sprint['start_date']
                sprint_end = sprint['end_date']

                # Filter jiras that might be relevant to this sprint's timeframe
                relevant_jiras = []
                for jira in available_jiras:
                    jira_created = jira['created_date']
                    jira_completed = jira.get('completed_date')  # Use get() to handle missing completed_date

                    # Include jira if:
                    # 1. It was created before sprint end AND
                    # 2. Either it's not completed, or it was completed after sprint start
                    if jira_created <= sprint_end:
                        if not jira_completed or jira_completed >= sprint_start:
                            relevant_jiras.append(jira['id'])

                # Assign jiras to sprint
                if relevant_jiras:
                    num_jiras = random.randint(
                        min(3, len(relevant_jiras)),
                        min(8, len(relevant_jiras))
                    )
                    sprint_jira_map[sprint['id']] = random.sample(relevant_jiras, num_jiras)

        return sprint_jira_map

    def associate_commits_with_cicd(self, cicd_data: List[Dict[str, Any]],
                                    commit_data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Create associations between CICD events and commits"""
        cicd_commit_map = {}
        project_commits = {}

        # Group commits by project
        for commit in commit_data:
            if commit['event_id'] not in project_commits:
                project_commits[commit['event_id']] = []
            project_commits[commit['event_id']].append(commit['id'])

        # Associate commits with CICD events based on timestamp
        for cicd in cicd_data:
            project_id = cicd['event_id']
            if project_id in project_commits:
                # Get commits that happened before this CICD event
                available_commits = [
                    commit['id'] for commit in commit_data
                    if commit['event_id'] == project_id and commit['timestamp'] <= cicd['timestamp']
                ]

                if available_commits:
                    # Select 1-5 commits for this CICD event
                    commit_count = random.randint(1, min(5, len(available_commits)))
                    cicd_commit_map[cicd['id']] = random.sample(available_commits, commit_count)

        return cicd_commit_map

    def generate_metrics(self, metric_type: str) -> Dict[str, Any]:
        """Generate metrics based on type"""
        if metric_type == "build":
            return {
                "test_coverage": np.random.uniform(80, 95),
                "failed_tests": np.random.randint(0, 10),
                "warnings": np.random.randint(0, 20),
                "security_issues": np.random.randint(0, 5)
            }
        elif metric_type == "deployment":
            return {
                "startup_time": np.random.uniform(5, 30),
                "memory_usage": np.random.randint(512, 2048),
                "cpu_usage": np.random.uniform(20, 80),
                "response_time": np.random.uniform(100, 500)
            }
        return {}

    def get_sequential_story_points(self, num_items: int, total_points: int) -> List[int]:
        """Generate a sequence of story points that sum to total_points"""
        points = []
        remaining_points = total_points
        remaining_items = num_items

        for i in range(num_items - 1):
            max_points = remaining_points - remaining_items + 1
            min_points = 1
            points_for_item = np.random.randint(min_points, max(min_points + 1, max_points))
            points.append(points_for_item)
            remaining_points -= points_for_item
            remaining_items -= 1

        points.append(remaining_points)
        return points

    def calculate_project_progress(self, completion_state: str, elapsed_days: int, total_days: int) -> float:
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
