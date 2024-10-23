"""
TimescaleDB Schema Management using pure Python with psycopg2
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_batch
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from contextlib import contextmanager

class TimescaleDBManager:
    def __init__(self, connection_params: Dict[str, str]):
        """
        Initialize TimescaleDB connection manager
        
        Args:
            connection_params: Dictionary containing connection parameters
                (dbname, user, password, host, port)
        """
        self.conn_params = connection_params
        self.logger = logging.getLogger(__name__)

    @contextmanager
    def get_connection(self, autocommit: bool = False):
        """Context manager for database connections"""
        conn = psycopg2.connect(**self.conn_params)
        if autocommit:
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        try:
            yield conn
        finally:
            conn.close()

    def create_database(self) -> None:
        """Create the database if it doesn't exist"""
        db_name = self.conn_params['dbname']
        temp_params = self.conn_params.copy()
        temp_params['dbname'] = 'postgres'  # Connect to default db first

        create_db_query = f"""
        SELECT 'CREATE DATABASE {db_name}'
        WHERE NOT EXISTS (
            SELECT FROM pg_database WHERE datname = '{db_name}'
        )
        """

        with self.get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(create_db_query)

    def create_extensions(self) -> None:
        """Create required PostgreSQL extensions"""
        extensions = [
            "CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;",
            "CREATE EXTENSION IF NOT EXISTS postgis CASCADE;",
            "CREATE EXTENSION IF NOT EXISTS pg_stat_statements CASCADE;"
        ]

        with self.get_connection(autocommit=True) as conn:
            with conn.cursor() as cur:
                for ext in extensions:
                    cur.execute(ext)

    def create_schema(self) -> None:
        """Create the complete database schema"""
        schema_queries = [
            # Enums
            """
            DO $$ BEGIN
                CREATE TYPE pr_status AS ENUM ('open', 'closed', 'merged');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
            """,

            # Repositories table
            """
            CREATE TABLE IF NOT EXISTS repositories (
                repo_id SERIAL PRIMARY KEY,
                repo_name VARCHAR(255) NOT NULL,
                repo_url VARCHAR(255) NOT NULL,
                created_at TIMESTAMPTZ DEFAULT current_timestamp,
                updated_at TIMESTAMPTZ DEFAULT current_timestamp,
                settings JSONB DEFAULT '{}',
                UNIQUE(repo_name)
            );
            """,

            # SDLC metrics table
            """
            CREATE TABLE IF NOT EXISTS sdlc_metrics (
                time TIMESTAMPTZ NOT NULL,
                repo_id INTEGER REFERENCES repositories(repo_id),
                metric_type VARCHAR(50) NOT NULL,
                metric_value DOUBLE PRECISION NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                event_id VARCHAR(255) NOT NULL,
                metadata JSONB DEFAULT '{}',
                PRIMARY KEY(time, repo_id, metric_type, event_id)
            );
            """,

            # PR metrics table
            """
            CREATE TABLE IF NOT EXISTS pr_metrics (
                time TIMESTAMPTZ NOT NULL,
                repo_id INTEGER REFERENCES repositories(repo_id),
                pr_number INTEGER NOT NULL,
                pr_status pr_status NOT NULL,
                commits_count INTEGER DEFAULT 0,
                changed_files INTEGER DEFAULT 0,
                additions INTEGER DEFAULT 0,
                deletions INTEGER DEFAULT 0,
                review_comments_count INTEGER DEFAULT 0,
                time_to_merge INTERVAL,
                mongodb_ref_id VARCHAR(255),
                metadata JSONB DEFAULT '{}',
                PRIMARY KEY(time, repo_id, pr_number)
            );
            """,

            # Commit metrics table
            """
            CREATE TABLE IF NOT EXISTS commit_metrics (
                time TIMESTAMPTZ NOT NULL,
                repo_id INTEGER REFERENCES repositories(repo_id),
                commit_hash VARCHAR(40) NOT NULL,
                pr_number INTEGER,
                files_changed INTEGER DEFAULT 0,
                insertions INTEGER DEFAULT 0,
                deletions INTEGER DEFAULT 0,
                author_email VARCHAR(255),
                mongodb_ref_id VARCHAR(255),
                metadata JSONB DEFAULT '{}',
                PRIMARY KEY(time, repo_id, commit_hash)
            );
            """,

            # Review metrics table
            """
            CREATE TABLE IF NOT EXISTS review_metrics (
                time TIMESTAMPTZ NOT NULL,
                repo_id INTEGER REFERENCES repositories(repo_id),
                pr_number INTEGER NOT NULL,
                reviewer VARCHAR(255) NOT NULL,
                review_type VARCHAR(50) NOT NULL,
                review_state VARCHAR(50) NOT NULL,
                comment_count INTEGER DEFAULT 0,
                review_duration INTERVAL,
                metadata JSONB DEFAULT '{}',
                PRIMARY KEY(time, repo_id, pr_number, reviewer)
            );
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in schema_queries:
                    cur.execute(query)
            conn.commit()

    def create_hypertables(self) -> None:
        """Create TimescaleDB hypertables"""
        hypertable_queries = [
            """
            SELECT create_hypertable(
                'sdlc_metrics', 'time',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            """,
            """
            SELECT create_hypertable(
                'pr_metrics', 'time',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            """,
            """
            SELECT create_hypertable(
                'commit_metrics', 'time',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            """,
            """
            SELECT create_hypertable(
                'review_metrics', 'time',
                if_not_exists => TRUE,
                migrate_data => TRUE
            );
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in hypertable_queries:
                    cur.execute(query)
            conn.commit()

    def create_indexes(self) -> None:
        """Create database indexes"""
        index_queries = [
            # SDLC metrics indexes
            """
            CREATE INDEX IF NOT EXISTS idx_sdlc_metrics_event_type 
            ON sdlc_metrics(event_type, time DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_sdlc_metrics_repo 
            ON sdlc_metrics(repo_id, time DESC);
            """,

            # PR metrics indexes
            """
            CREATE INDEX IF NOT EXISTS idx_pr_metrics_status 
            ON pr_metrics(pr_status, time DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_pr_metrics_repo_time 
            ON pr_metrics(repo_id, time DESC);
            """,

            # Commit metrics indexes
            """
            CREATE INDEX IF NOT EXISTS idx_commit_metrics_pr 
            ON commit_metrics(pr_number, time DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_commit_metrics_author 
            ON commit_metrics(author_email, time DESC);
            """,

            # Review metrics indexes
            """
            CREATE INDEX IF NOT EXISTS idx_review_metrics_reviewer 
            ON review_metrics(reviewer, time DESC);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_review_metrics_pr 
            ON review_metrics(repo_id, pr_number, time DESC);
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in index_queries:
                    cur.execute(query)
            conn.commit()

    def create_continuous_aggregates(self) -> None:
        """Create continuous aggregates for common queries"""
        aggregate_queries = [
            # Daily PR statistics
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_pr_stats
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('1 day', time) AS bucket,
                repo_id,
                COUNT(*) AS total_prs,
                COUNT(*) FILTER (WHERE pr_status = 'merged') AS merged_prs,
                AVG(changed_files) AS avg_files_changed,
                AVG(additions + deletions) AS avg_changes,
                AVG(EXTRACT(epoch FROM time_to_merge)/3600)::numeric(10,2) AS avg_hours_to_merge
            FROM pr_metrics
            GROUP BY bucket, repo_id
            WITH NO DATA;
            """,

            # Hourly commit statistics
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_commit_stats
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('1 hour', time) AS bucket,
                repo_id,
                COUNT(*) AS total_commits,
                SUM(files_changed) AS total_files_changed,
                SUM(insertions) AS total_insertions,
                SUM(deletions) AS total_deletions
            FROM commit_metrics
            GROUP BY bucket, repo_id
            WITH NO DATA;
            """,

            # Weekly review statistics
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS weekly_review_stats
            WITH (timescaledb.continuous) AS
            SELECT 
                time_bucket('7 days', time) AS bucket,
                repo_id,
                COUNT(DISTINCT reviewer) AS unique_reviewers,
                COUNT(*) AS total_reviews,
                AVG(comment_count) AS avg_comments_per_review,
                AVG(EXTRACT(epoch FROM review_duration)/3600)::numeric(10,2) AS avg_review_hours
            FROM review_metrics
            GROUP BY bucket, repo_id
            WITH NO DATA;
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in aggregate_queries:
                    cur.execute(query)
            conn.commit()

    def create_functions(self) -> None:
        """Create utility functions"""
        function_queries = [
            # Calculate PR velocity
            """
            CREATE OR REPLACE FUNCTION get_pr_velocity(
                p_repo_id INTEGER,
                p_start_time TIMESTAMPTZ,
                p_end_time TIMESTAMPTZ
            )
            RETURNS TABLE (
                day DATE,
                prs_merged INTEGER,
                avg_time_to_merge INTERVAL,
                avg_review_count NUMERIC
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                WITH pr_data AS (
                    SELECT
                        date_trunc('day', time)::DATE AS day,
                        COUNT(*) AS prs_merged,
                        AVG(time_to_merge) AS avg_time_to_merge,
                        COUNT(DISTINCT pr_number) AS unique_prs
                    FROM pr_metrics
                    WHERE repo_id = p_repo_id
                    AND time BETWEEN p_start_time AND p_end_time
                    AND pr_status = 'merged'
                    GROUP BY day
                ),
                review_data AS (
                    SELECT
                        date_trunc('day', time)::DATE AS day,
                        COUNT(*)::NUMERIC / COUNT(DISTINCT pr_number) AS avg_reviews
                    FROM review_metrics
                    WHERE repo_id = p_repo_id
                    AND time BETWEEN p_start_time AND p_end_time
                    GROUP BY day
                )
                SELECT
                    pd.day,
                    pd.prs_merged,
                    pd.avg_time_to_merge,
                    COALESCE(rd.avg_reviews, 0) AS avg_review_count
                FROM pr_data pd
                LEFT JOIN review_data rd ON pd.day = rd.day
                ORDER BY pd.day;
            END;
            $$;
            """,

            # Calculate developer productivity metrics
            """
            CREATE OR REPLACE FUNCTION get_developer_metrics(
                p_repo_id INTEGER,
                p_start_time TIMESTAMPTZ,
                p_end_time TIMESTAMPTZ
            )
            RETURNS TABLE (
                author_email VARCHAR,
                commit_count INTEGER,
                files_changed INTEGER,
                total_changes INTEGER,
                prs_created INTEGER,
                reviews_given INTEGER
            )
            LANGUAGE plpgsql
            AS $$
            BEGIN
                RETURN QUERY
                WITH commit_stats AS (
                    SELECT
                        author_email,
                        COUNT(*) AS commit_count,
                        SUM(files_changed) AS files_changed,
                        SUM(insertions + deletions) AS total_changes
                    FROM commit_metrics
                    WHERE repo_id = p_repo_id
                    AND time BETWEEN p_start_time AND p_end_time
                    GROUP BY author_email
                ),
                pr_stats AS (
                    SELECT
                        (metadata->>'author_email')::VARCHAR AS author_email,
                        COUNT(*) AS prs_created
                    FROM pr_metrics
                    WHERE repo_id = p_repo_id
                    AND time BETWEEN p_start_time AND p_end_time
                    GROUP BY metadata->>'author_email'
                ),
                review_stats AS (
                    SELECT
                        reviewer AS author_email,
                        COUNT(*) AS reviews_given
                    FROM review_metrics
                    WHERE repo_id = p_repo_id
                    AND time BETWEEN p_start_time AND p_end_time
                    GROUP BY reviewer
                )
                SELECT
                    COALESCE(cs.author_email, ps.author_email, rs.author_email),
                    COALESCE(cs.commit_count, 0),
                    COALESCE(cs.files_changed, 0),
                    COALESCE(cs.total_changes, 0),
                    COALESCE(ps.prs_created, 0),
                    COALESCE(rs.reviews_given, 0)
                FROM commit_stats cs
                FULL OUTER JOIN pr_stats ps ON cs.author_email = ps.author_email
                FULL OUTER JOIN review_stats rs ON COALESCE(cs.author_email, ps.author_email) = rs.author_email;
            END;
            $$;
            """
        ]

        with self.get_connection() as conn:
            with conn.cursor() as cur:
                for query in function_queries:
                    cur.execute(query)
            conn.commit()

    def create_retention_policies(self) -> None:
        """Create data retention policies"""
        retention_queries = [
            """
            SELECT add_retention_policy('sdlc_metrics', 
                INTERVAL '1 year',
                if_not_exists => TRUE
            );
            """,
            """
            SELECT add_retention_policy('pr_metrics',
                INTERVAL '2 years',
                if_not_exists => TRUE
            );
            """,
            """
            SELECT add_retention_policy('commit_metrics',
                INTERVAL '2 years',
                if_not_exists => TRUE
            );
            """,
            """
            SELECT add_retention_policy('review_metrics',
                INTERVAL '2 years',
                if_not_exists => TRUE
            );
            """
        ]

        