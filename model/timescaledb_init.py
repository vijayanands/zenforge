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

    def init_db(self):
        """Initialize the database schema"""
        if not self._verify_timescaledb():
            raise RuntimeError("TimescaleDB verification failed")

        # Drop and recreate schema
        with self.engine.begin() as connection:
            connection.execute(text("DROP SCHEMA IF EXISTS sdlc_timeseries CASCADE"))
            connection.execute(text("CREATE SCHEMA sdlc_timeseries"))

        # Create all tables first
        Base.metadata.create_all(self.engine)

        # Convert tables to hypertables
        hypertables = [
            ("design_events", "timestamp"),
            ("code_commits", "timestamp"),
            ("cicd_events", "timestamp"),
            ("team_metrics", "week_starting"),
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
                            create_default_indexes => FALSE
                        );
                    """
                        )
                    )
                    print(f"Created hypertable for {table}")
                except Exception as e:
                    print(f"Error creating hypertable for {table}: {e}")
                    raise

    def get_session(self):
        return self.Session()
