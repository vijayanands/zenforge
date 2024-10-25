# timescaledb_init.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from model.events_schema import Base

class DatabaseManager:
    def __init__(self, connection_string: str):
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)

    def _verify_timescaledb(self):
        """Verify TimescaleDB is properly installed and enabled"""
        with self.engine.connect() as connection:
            try:
                result = connection.execute(
                    text(
                        "SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname = 'timescaledb')"
                    )
                ).scalar()

                if not result:
                    connection.execute(
                        text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE")
                    )
                return True
            except Exception as e:
                print(f"Error verifying TimescaleDB: {e}")
                return False

    def _create_regular_indexes(self):
        """Create indexes for non-hypertables"""
        with self.engine.begin() as connection:
            try:
                # Create indexes for timestamp columns in regular tables
                connection.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_cicd_events_timestamp 
                        ON sdlc_timeseries.cicd_events (timestamp);
                        
                        CREATE INDEX IF NOT EXISTS idx_bugs_created_date 
                        ON sdlc_timeseries.bugs (created_date);
                        
                        CREATE INDEX IF NOT EXISTS idx_jira_items_created_date 
                        ON sdlc_timeseries.jira_items (created_date);
                        
                        CREATE INDEX IF NOT EXISTS idx_sprints_start_date 
                        ON sdlc_timeseries.sprints (start_date);

                        CREATE INDEX IF NOT EXISTS idx_pr_comments_created_at 
                        ON sdlc_timeseries.pr_comments (created_at);
                        """
                    )
                )

                # Create indexes for association tables
                connection.execute(
                    text(
                        """
                        CREATE INDEX IF NOT EXISTS idx_cicd_commit_assoc_cicd 
                        ON sdlc_timeseries.cicd_commit_association (cicd_id);
                        
                        CREATE INDEX IF NOT EXISTS idx_cicd_commit_assoc_commit 
                        ON sdlc_timeseries.cicd_commit_association (commit_id, commit_timestamp);
                        
                        CREATE INDEX IF NOT EXISTS idx_sprint_jira_assoc_sprint 
                        ON sdlc_timeseries.sprint_jira_association (sprint_id);
                        
                        CREATE INDEX IF NOT EXISTS idx_sprint_jira_assoc_jira 
                        ON sdlc_timeseries.sprint_jira_association (jira_id);

                        CREATE INDEX IF NOT EXISTS idx_pr_commit_assoc_pr 
                        ON sdlc_timeseries.pr_commit_association (pr_id, pr_created_at);
                        
                        CREATE INDEX IF NOT EXISTS idx_pr_commit_assoc_commit 
                        ON sdlc_timeseries.pr_commit_association (commit_id, commit_timestamp);
                        """
                    )
                )

                print("Created regular indexes")
            except Exception as e:
                print(f"Error creating indexes: {e}")
                raise

    def _create_hypertables(self):
        """Convert specific tables to hypertables"""
        hypertables = [
            ("design_events", "timestamp", "event_id"),
            ("code_commits", "timestamp", "event_id"),
            ("team_metrics", "week_starting", "event_id"),
            ("pull_requests", "created_at", "project_id"),
        ]

        with self.engine.begin() as connection:
            for table, time_column, project_column in hypertables:
                try:
                    # Create hypertable
                    connection.execute(
                        text(
                            f"""
                            SELECT create_hypertable(
                                'sdlc_timeseries.{table}',
                                '{time_column}',
                                if_not_exists => TRUE,
                                migrate_data => TRUE
                            );
                            """
                        )
                    )
                    print(f"Created hypertable for {table}")

                    # Create additional indexes if needed
                    if project_column and project_column != 'event_id':
                        connection.execute(
                            text(
                                f"""
                                CREATE INDEX IF NOT EXISTS idx_{table}_project_time 
                                ON sdlc_timeseries.{table} ({project_column}, {time_column});
                                """
                            )
                        )
                except Exception as e:
                    print(f"Error creating hypertable for {table}: {e}")
                    raise

    def init_db(self):
        """Initialize the database schema"""
        if not self._verify_timescaledb():
            raise RuntimeError("TimescaleDB verification failed")

        try:
            # Drop and recreate schema
            with self.engine.begin() as connection:
                connection.execute(
                    text("DROP SCHEMA IF EXISTS sdlc_timeseries CASCADE")
                )
                connection.execute(text("CREATE SCHEMA sdlc_timeseries"))
                connection.execute(text("COMMIT"))

            # Create all tables first
            Base.metadata.create_all(self.engine)

            # Create regular indexes
            self._create_regular_indexes()

            # Create hypertables
            self._create_hypertables()

        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def get_session(self):
        return self.Session()
