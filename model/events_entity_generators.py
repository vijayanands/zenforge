# part3b_data_generation_entities.py
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np
from events_data_generation_core import DataGenerator
import json

# Global variables (former class-level variables)
# Add any class-level variables here as globals
data_generator = DataGenerator()


def generate_design_events(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate design events for all projects"""
    design_events = []
    design_phases = data_generator.generate_design_phases()

    for proj_id, details in projects.items():
        start_date = details['start_date']

        for phase in design_phases:
            # Initial start
            design_events.append({
                'id': f"{proj_id}-{phase.upper()}",
                'event_id': proj_id,
                'design_type': phase,
                'stage': 'start',  # Lowercase as per enum
                'timestamp': start_date,
                'author': f"{phase.split('_')[0]}@example.com",
                'jira': f"{proj_id}-{phase.upper()}-1",
                'stakeholders': data_generator.generate_stakeholders(),
                'review_status': 'Pending'
            })

            # Add revisions (as blocked-resume cycles)
            num_revisions = np.random.randint(1, 4)
            revision_dates = data_generator.generate_date_sequence(start_date, num_revisions * 2)

            for rev_idx in range(num_revisions):
                # Blocked state
                design_events.append({
                    'id': f"{proj_id}-{phase.upper()}-BLOCK{rev_idx + 1}",
                    'event_id': proj_id,
                    'design_type': phase,
                    'stage': 'blocked',  # Lowercase as per enum
                    'timestamp': revision_dates[rev_idx * 2],
                    'author': f"{phase.split('_')[0]}@example.com",
                    'jira': f"{proj_id}-{phase.upper()}-1",
                    'stakeholders': data_generator.generate_stakeholders(),
                    'review_status': 'In Review'
                })

                # Resume state
                design_events.append({
                    'id': f"{proj_id}-{phase.upper()}-RESUME{rev_idx + 1}",
                    'event_id': proj_id,
                    'design_type': phase,
                    'stage': 'resume',  # Lowercase as per enum
                    'timestamp': revision_dates[rev_idx * 2 + 1],
                    'author': f"{phase.split('_')[0]}@example.com",
                    'jira': f"{proj_id}-{phase.upper()}-1",
                    'stakeholders': data_generator.generate_stakeholders(),
                    'review_status': 'In Review'
                })

            # Final completion
            design_events.append({
                'id': f"{proj_id}-{phase.upper()}-FINAL",
                'event_id': proj_id,
                'design_type': phase,
                'stage': 'end',  # Lowercase as per enum
                'timestamp': revision_dates[-1] + timedelta(days=2),
                'author': f"{phase.split('_')[0]}@example.com",
                'jira': f"{proj_id}-{phase.upper()}-1",
                'stakeholders': data_generator.generate_stakeholders(),
                'review_status': 'Approved'
            })

            start_date = revision_dates[-1] + timedelta(days=3)

    return design_events


def generate_jira_items(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate Jira items for all projects"""
    jira_items = []

    for proj_id, details in projects.items():
        start_date = details['start_date'] + timedelta(days=13)

        # Generate Epics
        for epic_num in range(1, 6):  # 5 epics per project
            epic_id = f"{proj_id}-E{epic_num}"
            epic_completion = start_date + timedelta(days=epic_num + 25)

            # Add Epic
            jira_items.append({
                'id': epic_id,
                'event_id': proj_id,  # Changed from project_id to event_id
                'type': 'Epic',
                'title': f"Epic {epic_num} for {details['title']}",
                'status': 'Done',
                'created_date': start_date + timedelta(days=epic_num),
                'completed_date': epic_completion,
                'priority': np.random.choice(['High', 'Medium', 'Low']),
                'story_points': np.random.randint(20, 40),
                'assigned_team': f"Team {chr(65 + np.random.randint(0, 3))}"  # Team A, B, or C
            })

            # Generate Stories for Epic
            for story_num in range(1, 6):  # 5 stories per epic
                story_id = f"{epic_id}-S{story_num}"
                story_completion = start_date + timedelta(days=epic_num + story_num + 20)

                # Add Story
                jira_items.append({
                    'id': story_id,
                    'event_id': proj_id,  # Changed from project_id to event_id
                    'parent_id': epic_id,
                    'type': 'Story',
                    'title': f"Story {story_num} for Epic {epic_num}",
                    'status': 'Done',
                    'created_date': start_date + timedelta(days=epic_num + story_num),
                    'completed_date': story_completion,
                    'priority': np.random.choice(['High', 'Medium', 'Low']),
                    'story_points': np.random.randint(5, 13),
                    'assigned_team': f"Team {chr(65 + np.random.randint(0, 3))}"
                })

                # Generate Tasks for Story
                for task_num in range(1, 6):  # 5 tasks per story
                    estimated_hours = np.random.randint(4, 16)
                    actual_hours = int(estimated_hours * np.random.uniform(0.8, 1.3))

                    jira_items.append({
                        'id': f"{story_id}-T{task_num}",
                        'event_id': proj_id,  # Changed from project_id to event_id
                        'parent_id': story_id,
                        'type': 'Task',
                        'title': f"Task {task_num} for Story {story_num}",
                        'status': 'Done',
                        'created_date': start_date + timedelta(days=epic_num + story_num + task_num),
                        'completed_date': start_date + timedelta(days=epic_num + story_num + task_num + 15),
                        'priority': np.random.choice(['High', 'Medium', 'Low']),
                        'story_points': np.random.randint(1, 5),
                        'assigned_developer': f"dev{np.random.randint(1, 6)}@example.com",
                        'estimated_hours': estimated_hours,
                        'actual_hours': actual_hours
                    })

    return jira_items

def generate_commits(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate code commits for all projects"""
    commits = []
    commit_types = ['feature', 'bugfix', 'refactor', 'docs', 'test']

    for proj_id, details in projects.items():
        start_date = details['start_date'] + timedelta(days=20)

        for i in range(200):  # 200 commits per project
            commit_date = start_date + timedelta(days=i // 4)  # 4 commits per day average

            files_changed, lines_added, lines_removed, code_coverage, lint_score = data_generator.generate_commit_metrics()

            commits.append({
                'id': data_generator.generate_unique_id('commit_'),
                'event_id': proj_id,  # Changed from project_id to event_id
                'timestamp': commit_date,
                'repository': f"{proj_id.lower()}-repo",
                'branch': f"feature/sprint-{i // 40 + 1}",
                'author': f"dev{i % 5 + 1}@example.com",
                'commit_hash': uuid.uuid4().hex[:8],
                'files_changed': files_changed,
                'lines_added': lines_added,
                'lines_removed': lines_removed,
                'code_coverage': code_coverage,
                'lint_score': lint_score,
                'commit_type': np.random.choice(commit_types, p=[0.4, 0.3, 0.15, 0.1, 0.05]),
                'review_time_minutes': np.random.randint(10, 120),
                'comments_count': np.random.randint(0, 10),
                'approved_by': f"reviewer{np.random.randint(1, 4)}@example.com"
            })

    return commits

def generate_cicd_events(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate CI/CD events for all projects"""
    cicd_events = []
    environments = ['dev', 'staging', 'qa', 'uat', 'production']

    for proj_id, details in projects.items():
        deploy_start = details['start_date'] + timedelta(days=25)

        for i in range(50):  # 50 deployment cycles per project
            deploy_date = deploy_start + timedelta(days=i)

            for env in environments:
                # Build event
                build_id = data_generator.generate_unique_id('build_')
                build_success = np.random.random() > 0.15  # 85% success rate

                cicd_events.append({
                    'id': build_id,
                    'event_id': proj_id,  # Changed from project_id
                    'timestamp': deploy_date,
                    'environment': env,
                    'event_type': 'build',
                    'status': 'success' if build_success else 'failed',
                    'duration_seconds': np.random.randint(180, 900),
                    'metrics': data_generator.generate_metrics('build')
                })

                if build_success:
                    # Deployment event
                    deploy_success = np.random.random() > 0.1  # 90% success rate
                    deploy_id = data_generator.generate_unique_id('deploy_')

                    cicd_events.append({
                        'id': deploy_id,
                        'event_id': proj_id,  # Changed from project_id
                        'timestamp': deploy_date + timedelta(minutes=15),
                        'environment': env,
                        'event_type': 'deployment',
                        'build_id': build_id,
                        'status': 'success' if deploy_success else 'failed',
                        'duration_seconds': np.random.randint(300, 1200),
                        'metrics': data_generator.generate_metrics('deployment')
                    })

                    # Add rollback if deployment failed
                    if not deploy_success:
                        rollback_reasons = [
                            'Performance degradation',
                            'Critical bug found',
                            'Integration test failure',
                            'Database migration issue',
                            'Memory leak detected',
                            'API compatibility issue',
                            'Security vulnerability',
                            'Data inconsistency'
                        ]

                        cicd_events.append({
                            'id': data_generator.generate_unique_id('rollback_'),
                            'event_id': proj_id,  # Changed from project_id
                            'timestamp': deploy_date + timedelta(minutes=30),
                            'environment': env,
                            'event_type': 'rollback',
                            'build_id': build_id,
                            'status': 'success',
                            'reason': np.random.choice(rollback_reasons),
                            'duration_seconds': np.random.randint(180, 600)
                        })

    return cicd_events

def generate_bugs(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate bugs for all projects"""
    bugs = []
    bug_types = ['Security', 'Performance', 'Functionality', 'Data', 'UI/UX']
    impact_areas = ['Customer', 'Internal', 'Integration', 'Infrastructure']

    for proj_id, details in projects.items():
        bug_start = details['start_date'] + timedelta(days=30)

        for i in range(15):  # 15 P0 bugs per project
            bug_date = bug_start + timedelta(days=i * 2)
            resolution_time = np.random.randint(4, 72)  # 4 to 72 hours

            bugs.append({
                'id': f"{proj_id}-BUG-{i + 1}",
                'event_id': proj_id,  # Changed from project_id
                'bug_type': np.random.choice(bug_types),
                'impact_area': np.random.choice(impact_areas),
                'severity': 'P0',
                'title': f"Critical bug in {details['title']}",
                'status': np.random.choice(['Fixed', 'Fixed', 'Fixed', 'In Progress'], p=[0.7, 0.1, 0.1, 0.1]),
                'created_date': bug_date,
                'resolved_date': bug_date + timedelta(hours=resolution_time),
                'resolution_time_hours': resolution_time,
                'assigned_to': f"dev{np.random.randint(1, 6)}@example.com",
                'environment_found': np.random.choice(['Production', 'Staging', 'QA']),
                'number_of_customers_affected': np.random.randint(1, 1000) if np.random.random() > 0.5 else 0,
                'root_cause': data_generator.generate_root_cause(),
                'fix_version': f"{proj_id.lower()}-v1.{np.random.randint(0, 9)}.{np.random.randint(0, 9)}",
                'regression_test_status': np.random.choice(['Passed', 'In Progress']),
                'customer_communication_needed': np.random.choice([True, False]),
                'postmortem_link': f"https://wiki.example.com/postmortem/{proj_id}-BUG-{i + 1}" if np.random.random() > 0.7 else None
            })

    return bugs

def generate_sprints(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate sprints for all projects"""
    sprints = []

    for proj_id, details in projects.items():
        sprint_start = details['start_date'] + timedelta(days=14)

        for sprint_num in range(1, 9):  # 8 sprints per project
            sprint_start_date = sprint_start + timedelta(days=(sprint_num - 1) * 14)
            sprint_end_date = sprint_start_date + timedelta(days=14)

            planned_story_points = np.random.randint(30, 50)
            completed_story_points = int(planned_story_points * np.random.uniform(0.7, 1.1))

            sprints.append({
                'id': f"{proj_id}-Sprint-{sprint_num}",
                'event_id': proj_id,  # Changed from project_id
                'start_date': sprint_start_date,
                'end_date': sprint_end_date,
                'planned_story_points': planned_story_points,
                'completed_story_points': completed_story_points,
                'planned_stories': np.random.randint(8, 15),
                'completed_stories': np.random.randint(6, 12),
                'team_velocity': completed_story_points,
                'burndown_efficiency': np.random.uniform(0.8, 1.2),
                'sprint_goals': f"Complete features for {details['title']} phase {sprint_num}",
                'retrospective_summary': np.random.choice([
                    'Improved team collaboration',
                    'Technical debt addressed',
                    'Communication challenges identified',
                    'Process improvements implemented',
                    'Knowledge sharing enhanced'
                ]),
                'blockers_encountered': np.random.randint(0, 4),
                'team_satisfaction_score': np.random.randint(7, 10),
                'status': 'Completed'
            })

    return sprints

def generate_team_metrics(projects: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate team metrics for all projects"""
    team_metrics = []

    for proj_id, details in projects.items():
        start_date = details['start_date']

        for week in range(12):  # 12 weeks of metrics
            week_start = start_date + timedelta(weeks=week)

            team_metrics.append({
                'id': f"{proj_id}-TM-{week+1}",  # Added id field
                'event_id': proj_id,  # Changed from project_id
                'week_starting': week_start,
                'team_size': details['team_size'],
                'velocity': np.random.randint(20, 40),
                'code_review_turnaround_hours': np.random.uniform(2, 48),
                'build_success_rate': np.random.uniform(85, 100),
                'test_coverage': np.random.uniform(75, 95),
                'bugs_reported': np.random.randint(2, 10),
                'bugs_fixed': np.random.randint(1, 8),
                'technical_debt_hours': np.random.randint(10, 40),
                'pair_programming_hours': np.random.randint(5, 20),
                'code_review_comments': np.random.randint(20, 100),
                'documentation_updates': np.random.randint(2, 8),
                'knowledge_sharing_sessions': np.random.randint(1, 3),
                'team_satisfaction': np.random.uniform(7, 9.5),
                'sprint_completion_rate': np.random.uniform(80, 100)
            })

    return team_metrics

def generate_all_data() -> Dict[str, List[Dict[str, Any]]]:
    """Generate all data for the application"""
    # Generate base project data
    projects = data_generator.generate_project_base_data()

    # Generate all entities
    data = {
        'projects': data_generator.generate_project_details(projects),
        'design_events': generate_design_events(projects),
        'jira_items': generate_jira_items(projects),
        'commits': generate_commits(projects),
        'cicd_events': generate_cicd_events(projects),
        'bugs': generate_bugs(projects),
        'sprints': generate_sprints(projects),
        'team_metrics': generate_team_metrics(projects)
    }

    return data

def get_sample_data() -> Dict[str, List[Dict[str, Any]]]:
    """Helper function to get sample data"""
    return generate_all_data()

if __name__ == "__main__":
    import json
    all_data = get_sample_data()
    json_data = json.dumps(all_data, indent=2, default=str)
    
    print(json_data)
    
    # Save the JSON data to a file
    output_file = "zenforge_data.json"
    with open(output_file, "w") as f:
        f.write(json_data)
    
    print(f"\nJSON data has been saved to {output_file}")
