import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_sample_data():
    # Set seed for reproducibility
    np.random.seed(42)

    # Start date for the first project
    base_start_date = datetime(2024, 1, 1)

    # Project base information
    projects = {
        "PRJ-001": {
            "title": "Customer Portal Redesign",
            "description": "Modernize the customer portal with improved UX and additional self-service features",
            "start_date": base_start_date,
            "complexity": "High",
            "team_size": 12,
        },
        "PRJ-002": {
            "title": "Payment Gateway Integration",
            "description": "Implement new payment gateway with support for multiple currencies and payment methods",
            "start_date": base_start_date + timedelta(days=15),
            "complexity": "Medium",
            "team_size": 8,
        },
        "PRJ-003": {
            "title": "Mobile App Analytics",
            "description": "Add comprehensive analytics and tracking to mobile applications",
            "start_date": base_start_date + timedelta(days=30),
            "complexity": "Medium",
            "team_size": 6,
        },
        "PRJ-004": {
            "title": "API Gateway Migration",
            "description": "Migrate existing APIs to new gateway with improved security and monitoring",
            "start_date": base_start_date + timedelta(days=45),
            "complexity": "High",
            "team_size": 10,
        },
    }

    # Generate Project Details Sheet
    project_details = []
    for proj_id, details in projects.items():
        project_details.append(
            {
                "project_id": proj_id,
                "title": details["title"],
                "description": details["description"],
                "start_date": details["start_date"],
                "status": "In Progress",
                "complexity": details["complexity"],
                "team_size": details["team_size"],
                "estimated_duration_weeks": np.random.randint(12, 24),
                "budget_allocated": np.random.randint(100000, 500000),
                "priority": np.random.choice(
                    ["High", "Medium", "Low"], p=[0.5, 0.3, 0.2]
                ),
            }
        )

    # Generate Design Events
    design_events = []
    design_phases = [
        "requirements",
        "ux_design",
        "architecture",
        "database_design",
        "api_design",
        "security_review",
    ]

    for proj_id, details in projects.items():
        start_date = details["start_date"]

        for phase in design_phases:
            # Initial start
            design_events.append(
                {
                    "project_id": proj_id,
                    "event_id": f"{proj_id}-{phase.upper()}",
                    "design_type": phase,
                    "stage": "start",
                    "timestamp": start_date,
                    "author": f"{phase.split('_')[0]}@example.com",
                    "jira": f"{proj_id}-{phase.upper()}-1",
                    "stakeholders": np.random.choice(
                        [
                            "Product,Dev,QA",
                            "Dev,Arch",
                            "UX,Dev,Product",
                            "Dev,Security",
                        ],
                        p=[0.4, 0.2, 0.2, 0.2],
                    ),
                    "review_status": "Pending",
                }
            )

            # Add some revisions
            num_revisions = np.random.randint(1, 4)
            for rev in range(num_revisions):
                design_events.append(
                    {
                        "project_id": proj_id,
                        "event_id": f"{proj_id}-{phase.upper()}-REV{rev+1}",
                        "design_type": phase,
                        "stage": "revision",
                        "timestamp": start_date + timedelta(days=rev + 2),
                        "author": f"{phase.split('_')[0]}@example.com",
                        "jira": f"{proj_id}-{phase.upper()}-1",
                        "stakeholders": np.random.choice(
                            [
                                "Product,Dev,QA",
                                "Dev,Arch",
                                "UX,Dev,Product",
                                "Dev,Security",
                            ]
                        ),
                        "review_status": "In Review",
                    }
                )

            # Final completion
            design_events.append(
                {
                    "project_id": proj_id,
                    "event_id": f"{proj_id}-{phase.upper()}",
                    "design_type": phase,
                    "stage": "end",
                    "timestamp": start_date + timedelta(days=num_revisions + 3),
                    "author": f"{phase.split('_')[0]}@example.com",
                    "jira": f"{proj_id}-{phase.upper()}-1",
                    "stakeholders": np.random.choice(
                        ["Product,Dev,QA", "Dev,Arch", "UX,Dev,Product", "Dev,Security"]
                    ),
                    "review_status": "Approved",
                }
            )

            start_date += timedelta(days=num_revisions + 4)

    # Generate Epics, Stories, and Tasks
    jira_items = []
    for proj_id, details in projects.items():
        start_date = details["start_date"] + timedelta(days=13)

        # Epics (increased from 3 to 5)
        for epic_num in range(1, 6):
            epic_id = f"{proj_id}-E{epic_num}"
            epic_completion = start_date + timedelta(days=epic_num + 25)

            jira_items.append(
                {
                    "project_id": proj_id,
                    "jira_id": epic_id,
                    "type": "Epic",
                    "title": f"Epic {epic_num} for {details['title']}",
                    "status": "Done",
                    "created_date": start_date + timedelta(days=epic_num),
                    "completed_date": epic_completion,
                    "priority": np.random.choice(["High", "Medium", "Low"]),
                    "story_points": np.random.randint(20, 40),
                    "assigned_team": np.random.choice(["Team A", "Team B", "Team C"]),
                }
            )

            # Stories for each Epic (increased from 3 to 5)
            for story_num in range(1, 6):
                story_id = f"{epic_id}-S{story_num}"
                story_completion = start_date + timedelta(
                    days=epic_num + story_num + 20
                )

                jira_items.append(
                    {
                        "project_id": proj_id,
                        "jira_id": story_id,
                        "parent_id": epic_id,
                        "type": "Story",
                        "title": f"Story {story_num} for Epic {epic_num}",
                        "status": "Done",
                        "created_date": start_date
                        + timedelta(days=epic_num + story_num),
                        "completed_date": story_completion,
                        "priority": np.random.choice(["High", "Medium", "Low"]),
                        "story_points": np.random.randint(5, 13),
                        "assigned_team": np.random.choice(
                            ["Team A", "Team B", "Team C"]
                        ),
                    }
                )

                # Tasks for each Story (increased from 3 to 5)
                for task_num in range(1, 6):
                    task_id = f"{story_id}-T{task_num}"
                    jira_items.append(
                        {
                            "project_id": proj_id,
                            "jira_id": task_id,
                            "parent_id": story_id,
                            "type": "Task",
                            "title": f"Task {task_num} for Story {story_num}",
                            "status": "Done",
                            "created_date": start_date
                            + timedelta(days=epic_num + story_num + task_num),
                            "completed_date": start_date
                            + timedelta(days=epic_num + story_num + task_num + 15),
                            "priority": np.random.choice(["High", "Medium", "Low"]),
                            "story_points": np.random.randint(1, 5),
                            "assigned_developer": f"dev{np.random.randint(1, 6)}@example.com",
                            "estimated_hours": np.random.randint(4, 16),
                            "actual_hours": np.random.randint(4, 20),
                        }
                    )

    # Generate Code Commits (increased from 50 to 200 per project)
    commits = []
    for proj_id, details in projects.items():
        start_date = details["start_date"] + timedelta(days=20)

        for i in range(200):
            commit_date = start_date + timedelta(
                days=i // 4
            )  # 4 commits per day on average

            # Generate more varied commit metrics
            files_changed = np.random.randint(1, 20)
            lines_added = np.random.randint(10, 500)
            lines_removed = np.random.randint(5, 300)

            commits.append(
                {
                    "project_id": proj_id,
                    "timestamp": commit_date,
                    "event_id": f"commit_{uuid.uuid4().hex[:8]}",
                    "repository": f"{proj_id.lower()}-repo",
                    "branch": f"feature/sprint-{i//40 + 1}",
                    "author": f"dev{i%5 + 1}@example.com",
                    "commit_hash": uuid.uuid4().hex[:8],
                    "files_changed": files_changed,
                    "lines_added": lines_added,
                    "lines_removed": lines_removed,
                    "code_coverage": np.random.uniform(75, 98),
                    "lint_score": np.random.uniform(80, 99),
                    "commit_type": np.random.choice(
                        ["feature", "bugfix", "refactor", "docs", "test"],
                        p=[0.4, 0.3, 0.15, 0.1, 0.05],
                    ),
                    "review_time_minutes": np.random.randint(10, 120),
                    "comments_count": np.random.randint(0, 10),
                    "approved_by": f"reviewer{np.random.randint(1,4)}@example.com",
                }
            )

    # Generate CI/CD Events (increased from 20 to 50 deployments per project)
    cicd_events = []
    environments = ["dev", "staging", "qa", "uat", "production"]

    for proj_id, details in projects.items():
        deploy_start = details["start_date"] + timedelta(days=25)

        for i in range(50):
            deploy_date = deploy_start + timedelta(days=i)

            for env in environments:
                # Build event
                build_id = f"build_{uuid.uuid4().hex[:8]}"
                build_success = np.random.random() > 0.15  # 85% success rate

                build_metrics = {
                    "test_coverage": np.random.uniform(80, 95),
                    "failed_tests": (
                        np.random.randint(0, 10)
                        if build_success
                        else np.random.randint(10, 30)
                    ),
                    "warnings": np.random.randint(0, 20),
                    "security_issues": np.random.randint(0, 5),
                }

                cicd_events.append(
                    {
                        "project_id": proj_id,
                        "timestamp": deploy_date,
                        "event_id": build_id,
                        "environment": env,
                        "event_type": "build",
                        "status": "success" if build_success else "failed",
                        "duration_seconds": np.random.randint(180, 900),
                        "metrics": build_metrics,
                    }
                )

                if build_success:
                    # Deployment event
                    deploy_success = np.random.random() > 0.1  # 90% success rate
                    deploy_metrics = {
                        "startup_time": np.random.uniform(5, 30),
                        "memory_usage": np.random.randint(512, 2048),
                        "cpu_usage": np.random.uniform(20, 80),
                        "response_time": np.random.uniform(100, 500),
                    }

                    cicd_events.append(
                        {
                            "project_id": proj_id,
                            "timestamp": deploy_date + timedelta(minutes=15),
                            "event_id": f"deploy_{uuid.uuid4().hex[:8]}",
                            "environment": env,
                            "event_type": "deployment",
                            "build_id": build_id,
                            "status": "success" if deploy_success else "failed",
                            "duration_seconds": np.random.randint(300, 1200),
                            "metrics": deploy_metrics,
                        }
                    )

                    # Add rollback if deployment failed
                    if not deploy_success:
                        rollback_reasons = [
                            "Performance degradation",
                            "Critical bug found",
                            "Integration test failure",
                            "Database migration issue",
                            "Memory leak detected",
                            "API compatibility issue",
                            "Security vulnerability",
                            "Data inconsistency",
                        ]

                        cicd_events.append(
                            {
                                "project_id": proj_id,
                                "timestamp": deploy_date + timedelta(minutes=30),
                                "event_id": f"rollback_{uuid.uuid4().hex[:8]}",
                                "environment": env,
                                "event_type": "rollback",
                                "build_id": build_id,
                                "status": "success",
                                "reason": np.random.choice(rollback_reasons),
                                "duration_seconds": np.random.randint(180, 600),
                            }
                        )

    # Generate P0 Bugs (increased from 5 to 15 per project)
    bugs = []
    bug_types = ["Security", "Performance", "Functionality", "Data", "UI/UX"]
    impact_areas = ["Customer", "Internal", "Integration", "Infrastructure"]

    for proj_id, details in projects.items():
        bug_start = details["start_date"] + timedelta(days=30)

        for i in range(15):
            bug_date = bug_start + timedelta(days=i * 2)
            resolution_time = np.random.randint(4, 72)  # 4 to 72 hours

            bugs.append(
                {
                    "project_id": proj_id,
                    "jira_id": f"{proj_id}-BUG-{i+1}",
                    "type": "Bug",
                    "bug_type": np.random.choice(bug_types),
                    "impact_area": np.random.choice(impact_areas),
                    "severity": "P0",
                    "title": f"Critical bug in {details['title']}",
                    "status": np.random.choice(
                        ["Fixed", "Fixed", "Fixed", "In Progress"],
                        p=[0.7, 0.1, 0.1, 0.1],
                    ),
                    "created_date": bug_date,
                    "resolved_date": bug_date + timedelta(hours=resolution_time),
                    "resolution_time_hours": resolution_time,
                    "assigned_to": f"dev{np.random.randint(1,6)}@example.com",
                    "environment_found": np.random.choice(
                        ["Production", "Staging", "QA"]
                    ),
                    "number_of_customers_affected": (
                        np.random.randint(1, 1000) if np.random.random() > 0.5 else 0
                    ),
                    "root_cause": np.random.choice(
                        [
                            "Code logic error",
                            "Database deadlock",
                            "Memory leak",
                            "Race condition",
                            "Configuration error",
                            "Third-party API failure",
                            "Network timeout",
                            "Input validation",
                            "Cache inconsistency",
                        ]
                    ),
                    "fix_version": f"{proj_id.lower()}-v1.{np.random.randint(0,9)}.{np.random.randint(0,9)}",
                    "regression_test_status": np.random.choice(
                        ["Passed", "In Progress"]
                    ),
                    "customer_communication_needed": np.random.choice([True, False]),
                    "postmortem_link": (
                        f"https://wiki.example.com/postmortem/{proj_id}-BUG-{i+1}"
                        if np.random.random() > 0.7
                        else None
                    ),
                }
            )

    # Generate Sprint Data
    sprints = []
    for proj_id, details in projects.items():
        sprint_start = details["start_date"] + timedelta(days=14)

        for sprint_num in range(1, 9):  # 8 sprints per project
            sprint_start_date = sprint_start + timedelta(days=(sprint_num - 1) * 14)
            sprint_end_date = sprint_start_date + timedelta(days=14)

            planned_story_points = np.random.randint(30, 50)
            completed_story_points = int(
                planned_story_points * np.random.uniform(0.7, 1.1)
            )

            sprints.append(
                {
                    "project_id": proj_id,
                    "sprint_id": f"{proj_id}-Sprint-{sprint_num}",
                    "start_date": sprint_start_date,
                    "end_date": sprint_end_date,
                    "planned_story_points": planned_story_points,
                    "completed_story_points": completed_story_points,
                    "planned_stories": np.random.randint(8, 15),
                    "completed_stories": np.random.randint(6, 12),
                    "team_velocity": completed_story_points,
                    "burndown_efficiency": np.random.uniform(0.8, 1.2),
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
                    "blockers_encountered": np.random.randint(0, 4),
                    "team_satisfaction_score": np.random.randint(7, 10),
                    "status": "Completed",
                }
            )

    # Generate Team Performance Metrics
    team_metrics = []
    for proj_id, details in projects.items():
        start_date = details["start_date"]

        for week in range(12):  # 12 weeks of metrics
            week_start = start_date + timedelta(weeks=week)

            team_metrics.append(
                {
                    "project_id": proj_id,
                    "week_starting": week_start,
                    "team_size": details["team_size"],
                    "velocity": np.random.randint(20, 40),
                    "code_review_turnaround_hours": np.random.uniform(2, 48),
                    "build_success_rate": np.random.uniform(85, 100),
                    "test_coverage": np.random.uniform(75, 95),
                    "bugs_reported": np.random.randint(2, 10),
                    "bugs_fixed": np.random.randint(1, 8),
                    "technical_debt_hours": np.random.randint(10, 40),
                    "pair_programming_hours": np.random.randint(5, 20),
                    "code_review_comments": np.random.randint(20, 100),
                    "documentation_updates": np.random.randint(2, 8),
                    "knowledge_sharing_sessions": np.random.randint(1, 3),
                    "team_satisfaction": np.random.uniform(7, 9.5),
                    "sprint_completion_rate": np.random.uniform(80, 100),
                }
            )

    # Create DataFrames
    df_projects = pd.DataFrame(project_details)
    df_design = pd.DataFrame(design_events)
    df_jira = pd.DataFrame(jira_items)
    df_commits = pd.DataFrame(commits)
    df_cicd = pd.DataFrame(cicd_events)
    df_bugs = pd.DataFrame(bugs)
    df_sprints = pd.DataFrame(sprints)
    df_team_metrics = pd.DataFrame(team_metrics)

    # Add calculated metrics to projects DataFrame
    for proj_id in projects.keys():
        proj_commits = df_commits[df_commits["project_id"] == proj_id]
        proj_bugs = df_bugs[df_bugs["project_id"] == proj_id]

        df_projects.loc[df_projects["project_id"] == proj_id, "total_commits"] = len(
            proj_commits
        )
        df_projects.loc[df_projects["project_id"] == proj_id, "avg_code_coverage"] = (
            proj_commits["code_coverage"].mean()
        )
        df_projects.loc[df_projects["project_id"] == proj_id, "total_p0_bugs"] = len(
            proj_bugs
        )

    # Write to Excel with formatting
    with pd.ExcelWriter("sdlc_sample_data.xlsx", engine="openpyxl") as writer:
        # Write each DataFrame to a separate sheet
        df_projects.to_excel(writer, sheet_name="Projects", index=False)
        df_design.to_excel(writer, sheet_name="Design_Events", index=False)
        df_jira.to_excel(writer, sheet_name="Jira_Items", index=False)
        df_commits.to_excel(writer, sheet_name="Commits", index=False)
        df_cicd.to_excel(writer, sheet_name="CICD_Events", index=False)
        df_bugs.to_excel(writer, sheet_name="P0_Bugs", index=False)
        df_sprints.to_excel(writer, sheet_name="Sprints", index=False)
        df_team_metrics.to_excel(writer, sheet_name="Team_Metrics", index=False)

        # Get workbook and worksheet references
        workbook = writer.book

        # Format each worksheet
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]

            # Auto-fit column widths
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = max_length + 2
                worksheet.column_dimensions[column[0].column_letter].width = min(
                    adjusted_width, 50
                )


if __name__ == "__main__":
    generate_sample_data()
