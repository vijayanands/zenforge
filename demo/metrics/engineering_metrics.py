from datetime import datetime, timedelta
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from tools.github.github import pull_github_data

def calculate_coding_time(prs: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate time from first commit to PR creation"""
    coding_times = []
    for pr in prs:
        pr_commits = [c for c in commits if c['sha'] in pr.get('commits', [])]
        if pr_commits:
            first_commit = min(datetime.strptime(c['date'], '%Y-%m-%dT%H:%M:%SZ') for c in pr_commits)
            pr_created = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            coding_time = (pr_created - first_commit).total_seconds() / 3600  # in hours
            coding_times.append(coding_time)
    
    if not coding_times:
        return {"value": "N/A", "trend": [], "target": "48 hours"}
    
    avg_coding_time = np.mean(coding_times)
    return {
        "value": f"{avg_coding_time/24:.1f} days",
        "trend": coding_times[-4:],
        "target": "2 days"
    }

def calculate_pr_metrics(prs: List[Dict[str, Any]], pr_comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate PR-related metrics"""
    pr_metrics = {}
    
    # PR Pickup Time
    pickup_times = []
    for pr in prs:
        created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
        first_review = None
        pr_comments_filtered = [c for c in pr_comments if c.get('pull_request_url', '').endswith(str(pr['number']))]
        if pr_comments_filtered:
            first_review = min(datetime.strptime(c['created_at'], '%Y-%m-%dT%H:%M:%SZ') for c in pr_comments_filtered)
            pickup_time = (first_review - created_at).total_seconds() / 3600  # in hours
            pickup_times.append(pickup_time)
    
    # PR Review Time
    review_times = []
    for pr in prs:
        if pr.get('merged_at'):
            created_at = datetime.strptime(pr['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            merged_at = datetime.strptime(pr['merged_at'], '%Y-%m-%dT%H:%M:%SZ')
            review_time = (merged_at - created_at).total_seconds() / 3600  # in hours
            review_times.append(review_time)
    
    # PR Size
    pr_sizes = [len(pr.get('additions', '').split('\n')) + len(pr.get('deletions', '').split('\n')) for pr in prs]
    
    return {
        "pr_pickup_time": {
            "value": f"{np.mean(pickup_times):.1f} hours" if pickup_times else "N/A",
            "trend": pickup_times[-4:] if pickup_times else [],
            "target": "4 hours"
        },
        "pr_review_time": {
            "value": f"{np.mean(review_times)/24:.1f} days" if review_times else "N/A",
            "trend": [t/24 for t in review_times[-4:]] if review_times else [],
            "target": "1 day"
        },
        "pr_size": {
            "value": f"{np.mean(pr_sizes):.0f} lines" if pr_sizes else "N/A",
            "trend": pr_sizes[-4:] if pr_sizes else [],
            "target": "200 lines"
        }
    }

def calculate_deployment_metrics(deployments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate deployment-related metrics"""
    # This would ideally come from your CI/CD system or deployment logs
    if not deployments:
        return {
            "deploy_time": {"value": "N/A", "trend": [], "target": "30 mins"},
            "deployment_frequency": {"value": "N/A", "trend": [], "target": "3/day"},
            "change_failure_rate": {"value": "N/A", "trend": [], "target": "2%"},
            "mttr": {"value": "N/A", "trend": [], "target": "2 hours"}
        }
    
    # Calculate actual metrics from deployment data
    # ... implementation depends on your deployment data structure

def calculate_code_churn_metrics(commits: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate code churn and refactoring metrics"""
    # Group commits by file and calculate churn rates
    file_changes = {}
    for commit in commits:
        for file in commit.get('files', []):
            if file['filename'] not in file_changes:
                file_changes[file['filename']] = []
            file_changes[file['filename']].append({
                'date': datetime.strptime(commit['date'], '%Y-%m-%dT%H:%M:%SZ'),
                'changes': file['additions'] + file['deletions']
            })
    
    # Calculate rework (changes to files modified in last 21 days)
    rework_count = 0
    refactor_count = 0
    total_changes = 0
    
    for file_history in file_changes.values():
        for i, change in enumerate(file_history):
            total_changes += 1
            last_change = next((c for c in file_history[:i] if (change['date'] - c['date']).days <= 21), None)
            if last_change:
                rework_count += 1
            elif any(c for c in file_history[:i] if (change['date'] - c['date']).days > 21):
                refactor_count += 1
    
    return {
        "rework_rate": {
            "value": f"{(rework_count/total_changes*100):.1f}%" if total_changes else "N/A",
            "trend": [],  # Would need time-series data
            "target": "4%"
        },
        "refactor_rate": {
            "value": f"{(refactor_count/total_changes*100):.1f}%" if total_changes else "N/A",
            "trend": [],  # Would need time-series data
            "target": "15%"
        }
    }

def calculate_metrics_from_timescale(start_date: datetime, end_date: datetime) -> Dict[str, Any]:
    """Calculate all engineering metrics from TimescaleDB data"""
    # Get data from GitHub
    github_data, user_info = pull_github_data(
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    # Extract relevant data
    all_prs = []
    all_pr_comments = []
    all_commits = []
    for user_data in github_data.values():
        all_prs.extend(user_data.get('pull_requests', []))
        all_pr_comments.extend(user_data.get('pull_request_comments', []))
        all_commits.extend(user_data.get('commits', []))
    
    # Calculate individual metrics
    coding_time = calculate_coding_time(all_prs, all_commits)
    pr_metrics = calculate_pr_metrics(all_prs, all_pr_comments)
    churn_metrics = calculate_code_churn_metrics(all_commits)
    
    # Calculate cycle time (time from first commit to deployment)
    # For now, using placeholder data since we don't have deployment information
    cycle_time = {
        "value": "4.5 days",
        "trend": [5.2, 4.9, 4.7, 4.5],
        "target": "4 days"
    }
    
    # Deployment metrics (placeholder data until we have CI/CD integration)
    deployment_metrics = {
        "deploy_time": {
            "value": "45 mins",
            "trend": [65, 55, 48, 45],
            "target": "30 mins"
        },
        "deployment_frequency": {
            "value": "2.8/day",
            "trend": [2.2, 2.4, 2.6, 2.8],
            "target": "3/day"
        },
        "change_failure_rate": {
            "value": "2.5%",
            "trend": [3.2, 3.0, 2.7, 2.5],
            "target": "2%"
        },
        "mttr": {
            "value": "2.2 hours",
            "trend": [3.1, 2.8, 2.4, 2.2],
            "target": "2 hours"
        }
    }
    
    # Merge frequency calculation
    days_in_range = (end_date - start_date).days
    total_merges = len([pr for pr in all_prs if pr.get('merged_at')])
    merge_frequency = {
        "value": f"{total_merges/max(days_in_range, 1):.1f}/day",
        "trend": [2.8, 2.9, 3.1, 3.2],  # Placeholder trend data
        "target": "4/day"
    }
    
    # Planning metrics (placeholder until we have sprint/planning data)
    planning_metrics = {
        "planning_accuracy": {
            "value": "85%",
            "trend": [82, 83, 84, 85],
            "target": "90%"
        },
        "capacity_accuracy": {
            "value": "92%",
            "trend": [89, 90, 91, 92],
            "target": "95%"
        }
    }
    
    # Combine all metrics
    metrics = {
        "coding_time": coding_time,
        "pr_pickup_time": pr_metrics["pr_pickup_time"],
        "pr_review_time": pr_metrics["pr_review_time"],
        "pr_size": pr_metrics["pr_size"],
        "merge_frequency": merge_frequency,
        "cycle_time": cycle_time,
        **deployment_metrics,
        **churn_metrics,
        **planning_metrics
    }
    
    return metrics 