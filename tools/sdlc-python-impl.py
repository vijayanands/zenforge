"""
SDLC Data Processing System
Handles GitHub webhook data, stores in MongoDB, and summarizes in TimescaleDB
"""

import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union
import logging

import psycopg2
from psycopg2.extras import execute_values
from pymongo import MongoClient
from pymongo.database import Database
from psycopg2.extensions import connection

class SDLCDataProcessor:
    def __init__(
        self,
        timescale_dsn: str,
        mongo_uri: str,
        mongo_db_name: str
    ):
        """
        Initialize connections to TimescaleDB and MongoDB
        
        Args:
            timescale_dsn: Connection string for TimescaleDB
            mongo_uri: MongoDB connection URI
            mongo_db_name: MongoDB database name
        """
        self.timescale_conn = psycopg2.connect(timescale_dsn)
        self.mongo_client = MongoClient(mongo_uri)
        self.mongo_db = self.mongo_client[mongo_db_name]
        self.logger = logging.getLogger(__name__)

    def process_github_webhook(self, event_type: str, payload: Dict) -> None:
        """
        Process GitHub webhook events and store in appropriate databases
        
        Args:
            event_type: GitHub webhook event type
            payload: Webhook payload data
        """
        try:
            if event_type == "pull_request":
                self._handle_pr_event(payload)
            elif event_type == "push":
                self._handle_push_event(payload)
            elif event_type == "pull_request_review":
                self._handle_pr_review_event(payload)
            else:
                self.logger.info(f"Unhandled event type: {event_type}")
        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise

    def _handle_pr_event(self, payload: Dict) -> None:
        """Handle Pull Request events"""
        # Store complete data in MongoDB
        pr_doc = self._prepare_pr_document(payload)
        mongo_result = self.mongo_db.pullRequests.update_one(
            {
                "repo_id": pr_doc["repo_id"],
                "pr_number": pr_doc["pr_number"]
            },
            {"$set": pr_doc},
            upsert=True
        )

        # Extract metrics for TimescaleDB
        pr_metrics = self._extract_pr_metrics(payload)
        self._store_pr_metrics(pr_metrics)

    def _handle_push_event(self, payload: Dict) -> None:
        """Handle Push (commit) events"""
        commits = self._prepare_commit_documents(payload)
        
        # Store in MongoDB
        for commit in commits:
            self.mongo_db.commits.update_one(
                {
                    "repo_id": commit["repo_id"],
                    "commit_hash": commit["commit_hash"]
                },
                {"$set": commit},
                upsert=True
            )

        # Extract and store commit metrics
        commit_metrics = [self._extract_commit_metrics(c) for c in commits]
        self._store_commit_metrics(commit_metrics)

    def _store_pr_metrics(self, metrics: Dict) -> None:
        """Store PR metrics in TimescaleDB"""
        query = """
        INSERT INTO pr_metrics (
            time, repo_id, pr_number, pr_status, commits_count,
            changed_files, additions, deletions, review_comments_count,
            mongodb_ref_id, metadata
        ) VALUES (
            %(time)s, %(repo_id)s, %(pr_number)s, %(pr_status)s, 
            %(commits_count)s, %(changed_files)s, %(additions)s,
            %(deletions)s, %(review_comments_count)s, %(mongodb_ref_id)s,
            %(metadata)s
        )
        ON CONFLICT (time, repo_id, pr_number)
        DO UPDATE SET
            pr_status = EXCLUDED.pr_status,
            commits_count = EXCLUDED.commits_count,
            changed_files = EXCLUDED.changed_files,
            additions = EXCLUDED.additions,
            deletions = EXCLUDED.deletions,
            review_comments_count = EXCLUDED.review_comments_count,
            metadata = EXCLUDED.metadata
        """
        with self.timescale_conn.cursor() as cur:
            cur.execute(query, metrics)
        self.timescale_conn.commit()

    def _extract_pr_metrics(self, payload: Dict) -> Dict:
        """Extract metrics from PR payload"""
        pr = payload["pull_request"]
        return {
            "time": datetime.now(timezone.utc),
            "repo_id": payload["repository"]["id"],
            "pr_number": pr["number"],
            "pr_status": pr["state"],
            "commits_count": pr["commits"],
            "changed_files": pr["changed_files"],
            "additions": pr["additions"],
            "deletions": pr["deletions"],
            "review_comments_count": pr["review_comments"],
            "mongodb_ref_id": str(pr["id"]),
            "metadata": {
                "title": pr["title"],
                "labels": [l["name"] for l in pr["labels"]],
                "author": pr["user"]["login"]
            }
        }

    def get_pr_velocity_metrics(
        self,
        repo_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict]:
        """
        Get PR velocity metrics for a repository
        
        Args:
            repo_id: Repository ID
            start_date: Start date for metrics
            end_date: End date for metrics
            
        Returns:
            List of daily PR velocity metrics
        """
        query = """
        SELECT * FROM get_pr_velocity(%s, %s, %s)
        """
        with self.timescale_conn.cursor() as cur:
            cur.execute(query, (repo_id, start_date, end_date))
            results = cur.fetchall()
            
        return [
            {
                "date": row[0],
                "prs_merged": row[1],
                "avg_time_to_merge": row[2]
            }
            for row in results
        ]

    def get_detailed_pr_info(self, repo_id: int, pr_number: int) -> Dict:
        """
        Get detailed PR information combining data from both databases
        
        Args:
            repo_id: Repository ID
            pr_number: Pull Request number
            
        Returns:
            Combined PR information
        """
        # Get metrics from TimescaleDB
        metrics_query = """
        SELECT time, pr_status, commits_count, changed_files,
               additions, deletions, review_comments_count, metadata
        FROM pr_metrics
        WHERE repo_id = %s AND pr_number = %s
        ORDER BY time DESC
        LIMIT 1
        """
        
        with self.timescale_conn.cursor() as cur:
            cur.execute(metrics_query, (repo_id, pr_number))
            metrics = cur.fetchone()

        # Get detailed info from MongoDB
        mongo_pr = self.mongo_db.pullRequests.find_one(
            {"repo_id": repo_id, "pr_number": pr_number}
        )

        if not metrics or not mongo_pr:
            return None

        # Combine information
        return {
            "metrics": {
                "time": metrics[0],
                "status": metrics[1],
                "commits_count": metrics[2],
                "changed_files": metrics[3],
                "additions": metrics[4],
                "deletions": metrics[5],
                "review_comments": metrics[6],
                "metadata": metrics[7]
            },
            "details": {
                "title": mongo_pr["title"],
                "description": mongo_pr["description"],
                "author": mongo_pr["author"],
                "timeline": mongo_pr["timeline"],
                "labels": mongo_pr["labels"],
                "reviewers": mongo_pr["reviewers"]
            }
        }

    def calculate_pr_stats(
        self,
        repo_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate PR statistics for a given time period
        
        Args:
            repo_id: Repository ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary of PR statistics
        """
        query = """
        WITH pr_data AS (
            SELECT
                pr_status,
                changed_files,
                additions + deletions as total_changes,
                review_comments_count
            FROM pr_metrics
            WHERE repo_id = %s
            AND time BETWEEN %s AND %s
        )
        SELECT
            COUNT(*) as total_prs,
            COUNT(*) FILTER (WHERE pr_status = 'merged') as merged_prs,
            AVG(changed_files) as avg_files_changed,
            AVG(total_changes) as avg_changes,
            AVG(review_comments_count) as avg_review_comments
        FROM pr_data
        """
        
        with self.timescale_conn.cursor() as cur:
            cur.execute(query, (repo_id, start_date, end_date))
            result = cur.fetchone()

        return {
            "total_prs": result[0],
            "merged_prs": result[1],
            "avg_files_changed": float(result[2]) if result[2] else 0,
            "avg_changes": float(result[3]) if result[3] else 0,
            "avg_review_comments": float(result[4]) if result[4] else 0
        }

    def close(self) -> None:
        """Close database connections"""
        self.timescale_conn.close()
        self.mongo_client.close()

class SDLCAnalytics:
    """Analytics helper class for SDLC data"""
    
    def __init__(self, processor: SDLCDataProcessor):
        self.processor = processor

    def calculate_developer_metrics(
        self,
        repo_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Calculate developer-specific metrics
        
        Args:
            repo_id: Repository ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary of developer metrics
        """
        # Query MongoDB for detailed developer activity
        pipeline = [
            {
                "$match": {
                    "repo_id": repo_id,
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$group": {
                    "_id": "$author.username",
                    "total_prs": {"$sum": 1},
                    "total_commits": {
                        "$sum": "$stats.commits_count"
                    },
                    "total_changes": {
                        "$sum": {
                            "$add": ["$stats.additions", "$stats.deletions"]
                        }
                    }
                }
            }
        ]
        
        developer_stats = list(
            self.processor.mongo_db.pullRequests.aggregate(pipeline)
        )
        
        return {
            dev["_id"]: {
                "prs_created": dev["total_prs"],
                "total_commits": dev["total_commits"],
                "total_changes": dev["total_changes"]
            }
            for dev in developer_stats
        }

    def get_pr_review_stats(
        self,
        repo_id: int,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """
        Get PR review statistics
        
        Args:
            repo_id: Repository ID
            start_date: Start date for analysis
            end_date: End date for analysis
            
        Returns:
            Dictionary of review statistics
        """
        pipeline = [
            {
                "$match": {
                    "repo_id": repo_id,
                    "created_at": {
                        "$gte": start_date,
                        "$lte": end_date
                    }
                }
            },
            {
                "$unwind": "$timeline"
            },
            {
                "$match": {
                    "timeline.event_type": "review_submitted"
                }
            },
            {
                "$group": {
                    "_id": "$pr_number",
                    "review_count": {"$sum": 1},
                    "reviewers": {"$addToSet": "$timeline.actor"}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_reviews": {"$sum": "$review_count"},
                    "avg_reviews_per_pr": {"$avg": "$review_count"},
                    "unique_reviewers": {
                        "$addToSet": "$reviewers"
                    }
                }
            }
        ]
        
        review_stats = list(
            self.processor.mongo_db.pullRequests.aggregate(pipeline)
        )
        
        if not review_stats:
            return {
                "total_reviews": 0,
                "avg_reviews_per_pr": 0,
                "unique_reviewers": 0
            }
            
        stats = review_stats[0]
        return {
            "total_reviews": stats["total_reviews"],
            "avg_reviews_per_pr": round(stats["avg_reviews_per_pr"], 2),
            "unique_reviewers": len(stats["unique_reviewers"])
        }

# Example usage
if __name__ == "__main__":
    # Initialize processor with connection details
    processor = SDLCDataProcessor(
        timescale_dsn="postgresql://user:pass@localhost:5432/sdlc_db",
        mongo_uri="mongodb://localhost:27017",
        mongo_db_name="sdlc_data"
    )
    
    # Initialize analytics
    analytics = SDLCAnalytics(processor)
    
    # Example webhook processing
    webhook_payload = {
        "event_type": "pull_request",
        "payload": {
            # ... webhook data ...
        }
    }
    
    try:
        # Process webhook
        processor.process_github_webhook(
            webhook_payload["event_type"],
            webhook_payload["payload"]
        )
        
        # Get PR velocity metrics
        velocity_metrics = processor.get_pr_velocity_metrics(
            repo_id=123,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        # Get developer metrics
        dev_metrics = analytics.calculate_developer_metrics(
            repo_id=123,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 31)
        )
        
        print("Velocity Metrics:", velocity_metrics)
        print("Developer Metrics:", dev_metrics)
        
    finally:
        processor.close()
