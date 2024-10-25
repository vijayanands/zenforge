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
            # Create indexes for timestamp columns in regular tables
            indexes = [
                ("cicd_events", "timestamp"),
                ("bugs", "created_date"),
                ("jira_items", "created_date"),
                ("sprints", "start_date")
            ]

            for table, column in indexes:
                try:
                    connection.execute(
                        text(
                            f"""
                            CREATE INDEX IF NOT EXISTS idx_{table}_{column} 
                            ON sdlc_timeseries.{table} ({column});
                            """
                        )
                    )
                    print(f"Created index for {table}.{column}")
                except Exception as e:
                    print(f"Error creating index for {table}: {e}")
                    raise

    def _create_hypertables(self):
        """Convert specific tables to hypertables"""
        hypertables = [
            ("design_events", "timestamp"),
            ("code_commits", "timestamp"),
            ("team_metrics", "week_starting")
        ]

        with self.engine.begin() as connection:
            for table, time_column in hypertables:
                try:
                    connection.execute(
                        text(
                            f"""
                            SELECT create_hypertable(
                                'sdlc_timeseries.{table}',
                                '{time_column}',
                                if_not_exists => TRUE,
                                create_default_indexes => TRUE
                            );
                            """
                        )
                    )
                    print(f"Created hypertable for {table}")

                    # Create additional indexes for foreign keys
                    connection.execute(
                        text(
                            f"""
                            CREATE INDEX IF NOT EXISTS idx_{table}_event_time 
                            ON sdlc_timeseries.{table} (event_id, {time_column});
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
                connection.execute(text("DROP SCHEMA IF EXISTS sdlc_timeseries CASCADE"))
                connection.execute(text("CREATE SCHEMA sdlc_timeseries"))

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
