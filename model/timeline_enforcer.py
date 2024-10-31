from datetime import timedelta, datetime
from random import randint
from typing import List, Dict, Any

from model.sdlc_events import PRStatus


def enforce_design_sprint_timeline(projects: Dict[str, Dict[str, Any]]) -> Dict[str, datetime]:
    """Calculate and enforce design phase completion times for each project"""
    design_completion_times = {}
    
    for proj_id, details in projects.items():
        # Set design phase to complete in first 2-3 weeks
        design_duration = timedelta(days=randint(14, 21))
        design_completion_times[proj_id] = details['start_date'] + design_duration
    
    return design_completion_times

def adjust_sprint_dates(sprints: List[Dict[str, Any]], jira_items: List[Dict[str, Any]], 
                       design_completion_times: Dict[str, datetime]) -> List[Dict[str, Any]]:
    """Adjust sprint dates based on Jira timelines and design completion"""
    project_jiras = {}
    for jira in jira_items:
        if jira['event_id'] not in project_jiras:
            project_jiras[jira['event_id']] = []
        project_jiras[jira['event_id']].append(jira)
    
    adjusted_sprints = []
    for sprint in sprints:
        proj_id = sprint['event_id']
        design_completion = design_completion_times.get(proj_id)
        
        if design_completion:
            # Ensure sprint starts after design completion
            sprint_start = max(design_completion + timedelta(days=1), sprint['start_date'])
            sprint['start_date'] = sprint_start
            
            # Adjust sprint end date based on Jira completions
            sprint_jiras = [j for j in project_jiras.get(proj_id, []) 
                          if j.get('sprint_id') == sprint['id']]
            if sprint_jiras:
                latest_completion = max(j['completed_date'] for j in sprint_jiras 
                                     if j.get('completed_date'))
                sprint['end_date'] = latest_completion
        
        adjusted_sprints.append(sprint)
    
    return adjusted_sprints

def adjust_commit_dates(commits: List[Dict[str, Any]], jira_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adjust commit dates to ensure they happen after Jira completion"""
    jira_completion_times = {j['id']: j.get('completed_date') 
                           for j in jira_items if j.get('completed_date')}
    
    adjusted_commits = []
    for commit in commits:
        jira_completion = jira_completion_times.get(commit['jira_id'])
        if jira_completion:
            # Set commit timestamp to jira completion time plus random minutes
            commit['timestamp'] = jira_completion + timedelta(minutes=randint(5, 60))
        adjusted_commits.append(commit)
    
    return adjusted_commits

def adjust_pr_dates(pull_requests: List[Dict[str, Any]], commits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adjust PR dates to ensure they start after commits"""
    commit_times = {(c['id'], c['timestamp']): c['timestamp'] for c in commits}
    
    adjusted_prs = []
    for pr in pull_requests:
        commit_time = commit_times.get((pr['commit_id'], pr['commit_timestamp']))
        if commit_time:
            # Set PR creation time to commit time plus random minutes
            pr['created_at'] = commit_time + timedelta(minutes=randint(5, 30))
            if pr['status'] == PRStatus.MERGED:
                pr['merged_at'] = pr['created_at'] + timedelta(hours=randint(1, 24))
        adjusted_prs.append(pr)
    
    return adjusted_prs

def enforce_timeline_constraints(all_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enforce all timeline constraints on the data"""
    # Get design completion times
    design_completion_times = enforce_design_sprint_timeline(all_data['projects'])

    # Adjust dates for all entities
    all_data['sprints'] = adjust_sprint_dates(
        all_data['sprints'],
        all_data['jira_items'],
        design_completion_times
    )

    all_data['commits'] = adjust_commit_dates(
        all_data['commits'],
        all_data['jira_items']
    )

    all_data['pull_requests'] = adjust_pr_dates(
        all_data['pull_requests'],
        all_data['commits']
    )

    all_data['cicd_events'] = adjust_cicd_dates(
        all_data['cicd_events'],
        all_data['pull_requests'],
        all_data['relationships']['cicd_commit_associations']
    )

    all_data['bugs'] = adjust_bug_dates(
        all_data['bugs'],
        all_data['cicd_events']
    )

    return all_data

def adjust_bug_dates(bugs: List[Dict[str, Any]], cicd_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Adjust P0 bug dates to ensure they happen after CI/CD completion"""
    build_completion_times = {event['build_id']: event['timestamp'] 
                            for event in cicd_events}
    
    adjusted_bugs = []
    for bug in bugs:
        if bug['severity'] == 'P0':
            build_completion = build_completion_times.get(bug['build_id'])
            if build_completion:
                bug['created_date'] = build_completion + timedelta(hours=randint(1, 24))
                if bug['status'] == 'Fixed':
                    bug['resolved_date'] = bug['created_date'] + timedelta(hours=randint(4, 72))
        adjusted_bugs.append(bug)
    
    return adjusted_bugs


def adjust_cicd_dates(cicd_events: List[Dict[str, Any]],
                      pull_requests: List[Dict[str, Any]],
                      cicd_commit_map: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Adjust CI/CD event dates to ensure they start after PR completion and commits"""
    # Create map of commit timestamps by commit ID
    commit_times = {}
    for pr in pull_requests:
        if pr['commit_id'] and pr['commit_timestamp']:
            commit_times[pr['commit_id']] = pr['commit_timestamp']

    # Create map of PR merge times by commit ID
    pr_merge_times = {pr['commit_id']: pr['merged_at']
                      for pr in pull_requests
                      if pr['status'] == 'MERGED' and pr.get('merged_at')}

    adjusted_events = []
    for event in cicd_events:
        # Get associated commits from the mapping
        associated_commits = cicd_commit_map.get(event['id'], [])

        if associated_commits:
            # Find latest commit time and PR merge time
            latest_commit_time = max(
                (commit_times.get(commit_id) for commit_id in associated_commits
                 if commit_id in commit_times),
                default=None
            )

            merge_times = [pr_merge_times.get(commit_id)
                           for commit_id in associated_commits
                           if commit_id in pr_merge_times]
            latest_merge = max(merge_times) if merge_times else None

            # CICD event must happen after both commit and PR merge
            reference_time = max(
                filter(None, [latest_commit_time, latest_merge])
            ) if latest_commit_time or latest_merge else None

            if reference_time:
                event['timestamp'] = reference_time + timedelta(minutes=randint(5, 30))

        adjusted_events.append(event)

    return sorted(adjusted_events, key=lambda x: x['timestamp'])