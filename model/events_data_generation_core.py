# part3a_data_generation_core.py

from datetime import datetime, timedelta
import numpy as np
import uuid
from typing import Dict, List, Any, Tuple

class DataGenerator:
    def __init__(self):
        # Set seed for reproducibility
        np.random.seed(42)
        self.base_start_date = datetime(2024, 1, 1)

    def generate_project_base_data(self) -> Dict[str, Dict[str, Any]]:
        """Generate base project information"""
        return {
            'PRJ-001': {
                'title': 'Customer Portal Redesign',
                'description': 'Modernize the customer portal with improved UX and additional self-service features',
                'start_date': self.base_start_date,
                'complexity': 'High',
                'team_size': 12
            },
            'PRJ-002': {
                'title': 'Payment Gateway Integration',
                'description': 'Implement new payment gateway with support for multiple currencies and payment methods',
                'start_date': self.base_start_date + timedelta(days=15),
                'complexity': 'Medium',
                'team_size': 8
            },
            'PRJ-003': {
                'title': 'Mobile App Analytics',
                'description': 'Add comprehensive analytics and tracking to mobile applications',
                'start_date': self.base_start_date + timedelta(days=30),
                'complexity': 'Medium',
                'team_size': 6
            },
            'PRJ-004': {
                'title': 'API Gateway Migration',
                'description': 'Migrate existing APIs to new gateway with improved security and monitoring',
                'start_date': self.base_start_date + timedelta(days=45),
                'complexity': 'High',
                'team_size': 10
            }
        }

    def generate_project_details(self, projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate detailed project information"""
        project_details = []
        for proj_id, details in projects.items():
            project_details.append({
                'id': proj_id,
                'title': details['title'],
                'description': details['description'],
                'start_date': details['start_date'],
                'status': 'In Progress',
                'complexity': details['complexity'],
                'team_size': details['team_size'],
                'estimated_duration_weeks': np.random.randint(12, 24),
                'budget_allocated': np.random.randint(100000, 500000),
                'priority': np.random.choice(['High', 'Medium', 'Low'], p=[0.5, 0.3, 0.2])
            })
        return project_details

    def generate_design_phases(self) -> List[str]:
        """Generate list of design phases"""
        return [
            'requirements',
            'ux_design',
            'architecture',
            'database_design',
            'api_design',
            'security_review'
        ]

    def generate_stakeholders(self) -> str:
        """Generate random stakeholder combination"""
        stakeholder_groups = [
            'Product,Dev,QA',
            'Dev,Arch',
            'UX,Dev,Product',
            'Dev,Security',
            'Product,QA,Security',
            'Arch,Security,Dev'
        ]
        return np.random.choice(stakeholder_groups)

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

    def generate_unique_id(self, prefix: str = '') -> str:
        """Generate a unique identifier"""
        return f"{prefix}{uuid.uuid4().hex[:8]}"

    def generate_metrics(self, metric_type: str) -> Dict[str, Any]:
        """Generate metrics based on type"""
        if metric_type == 'build':
            return {
                'test_coverage': np.random.uniform(80, 95),
                'failed_tests': np.random.randint(0, 10),
                'warnings': np.random.randint(0, 20),
                'security_issues': np.random.randint(0, 5)
            }
        elif metric_type == 'deployment':
            return {
                'startup_time': np.random.uniform(5, 30),
                'memory_usage': np.random.randint(512, 2048),
                'cpu_usage': np.random.uniform(20, 80),
                'response_time': np.random.uniform(100, 500)
            }
        return {}

    def generate_root_cause(self) -> str:
        """Generate random root cause for bugs"""
        causes = [
            'Code logic error',
            'Database deadlock',
            'Memory leak',
            'Race condition',
            'Configuration error',
            'Third-party API failure',
            'Network timeout',
            'Input validation',
            'Cache inconsistency',
            'Resource exhaustion',
            'Concurrency issue',
            'Environmental mismatch'
        ]
        return np.random.choice(causes)

    def generate_commit_metrics(self) -> Tuple[int, int, int, float, float]:
        """Generate metrics for a code commit"""
        files_changed = np.random.randint(1, 20)
        lines_added = np.random.randint(10, 500)
        lines_removed = np.random.randint(5, 300)
        code_coverage = np.random.uniform(75, 98)
        lint_score = np.random.uniform(80, 99)
        return files_changed, lines_added, lines_removed, code_coverage, lint_score
