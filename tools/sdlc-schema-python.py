"""
SDLC Schema Management
Handles creation and management of database schemas for TimescaleDB and MongoDB
"""

from typing import Optional, Dict, Any
import logging
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    ForeignKey, Enum, JSON, MetaData, Table, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import JSONB
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
import enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
metadata = MetaData()

class PRStatus(enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"

class TimescaleSchema:
    """TimescaleDB schema management using SQLAlchemy"""
    
    def __init__(self, connection_string: str):
        """
        Initialize TimescaleDB connection
        
        Args:
            connection_string: Database connection string
        """
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.metadata = metadata

    def create_extensions(self) -> None:
        """Create required PostgreSQL extensions"""
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))

    class Repository(Base):
        """Repository model"""
        __tablename__ = 'repositories'

        repo_id = Column(Integer, primary_key=True)
        repo_name = Column(String(255), nullable=False, unique=True)
        repo_url = Column(String(255), nullable=False)
        created_at = Column(DateTime, default=datetime.utcnow)

    class SDLCMetric(Base):
        """SDLC metrics model"""
        __tablename__ = 'sdlc_metrics'

        time = Column(DateTime, primary_key=True)
        repo_id = Column(Integer, ForeignKey('repositories.repo_id'), primary_key=True)
        metric_type = Column(String(50), primary_key=True)
        metric_value = Column(Float, nullable=False)
        event_type = Column(String(50), nullable=False)
        event_id = Column(String(255), primary_key=True)
        metadata = Column(JSONB)

    class PRMetric(Base):
        """Pull Request metrics model"""
        __tablename__ = 'pr_metrics'

        time = Column(DateTime, primary_key=True)
        repo_id = Column(Integer, ForeignKey('repositories.repo_id'), primary_key=True)
        pr_number = Column(Integer, primary_key=True)
        pr_status = Column(Enum(PRStatus), nullable=False)
        commits_count = Column(Integer)
        changed_files = Column(Integer)
        additions = Column(Integer)
        deletions = Column(Integer)
        review_comments_count = Column(Integer)
        mongodb_ref_id = Column(String(255))
        metadata = Column(JSONB)

    class CommitMetric(Base):
        """Commit metrics model"""
        __tablename__ = 'commit_metrics'

        time = Column(DateTime, primary_key=True)
        repo_id = Column(Integer, ForeignKey('repositories.repo_id'), primary_key=True)
        commit_hash = Column(String(40), primary_key=True)
        pr_number = Column(Integer)
        files_changed = Column(Integer)
        insertions = Column(Integer)
        deletions = Column(Integer)
        author_email = Column(String(255))
        mongodb_ref_id = Column(String(255))
        metadata = Column(JSONB)

    def create_hypertables(self) -> None:
        """Create TimescaleDB hypertables"""
        with self.engine.connect() as conn:
            # Create hypertable for SDLC metrics
            conn.execute(text("""
                SELECT create_hypertable(
                    'sdlc_metrics', 'time',
                    if_not_exists => TRUE
                )
            """))

            # Create hypertable for PR metrics
            conn.execute(text("""
                SELECT create_hypertable(
                    'pr_metrics', 'time',
                    if_not_exists => TRUE
                )
            """))

            # Create hypertable for commit metrics
            conn.execute(text("""
                SELECT create_hypertable(
                    'commit_metrics', 'time',
                    if_not_exists => TRUE
                )
            """))

    def create_continuous_aggregates(self) -> None:
        """Create continuous aggregates for common queries"""
        with self.engine.connect() as conn:
            # Daily PR statistics
            conn.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS daily_pr_stats
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('1 day', time) AS bucket,
                       repo_id,
                       COUNT(*) AS total_prs,
                       COUNT(*) FILTER (WHERE pr_status = 'merged') AS merged_prs,
                       AVG(changed_files) AS avg_files_changed,
                       AVG(additions + deletions) AS avg_changes
                FROM pr_metrics
                GROUP BY bucket, repo_id
                WITH NO DATA
            """))

    def create_indexes(self) -> None:
        """Create database indexes"""
        with self.engine.connect() as conn:
            # SDLC metrics indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sdlc_metrics_event_type 
                ON sdlc_metrics(event_type, time DESC)
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sdlc_metrics_repo 
                ON sdlc_metrics(repo_id, time DESC)
            """))

            # PR metrics indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_pr_metrics_status 
                ON pr_metrics(pr_status, time DESC)
            """))

            # Commit metrics indexes
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_commit_metrics_pr 
                ON commit_metrics(pr_number, time DESC)
            """))

    def initialize_schema(self) -> None:
        """Initialize complete database schema"""
        logger.info("Initializing TimescaleDB schema...")
        try:
            self.create_extensions()
            Base.metadata.create_all(self.engine)
            self.create_hypertables()
            self.create_continuous_aggregates()
            self.create_indexes()
            logger.info("TimescaleDB schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TimescaleDB schema: {str(e)}")
            raise

class MongoSchema:
    """MongoDB schema management"""
    
    def __init__(self, connection_string: str, database_name: str):
        """
        Initialize MongoDB connection
        
        Args:
            connection_string: MongoDB connection string
            database_name: Database name
        """
        self.client = MongoClient(connection_string)
        self.db = self.client[database_name]

    def create_collections(self) -> None:
        """Create MongoDB collections with validators"""
        # Pull Requests collection
        pr_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["pr_number", "repo_id", "title", "created_at", "status"],
                "properties": {
                    "pr_number": {"bsonType": "int"},
                    "repo_id": {"bsonType": "int"},
                    "title": {"bsonType": "string"},
                    "description": {"bsonType": "string"},
                    "created_at": {"bsonType": "date"},
                    "updated_at": {"bsonType": "date"},
                    "closed_at": {"bsonType": "date"},
                    "status": {"enum": ["open", "closed", "merged"]},
                    "author": {
                        "bsonType": "object",
                        "required": ["id", "username"],
                        "properties": {
                            "id": {"bsonType": "int"},
                            "username": {"bsonType": "string"},
                            "email": {"bsonType": "string"}
                        }
                    },
                    "labels": {"bsonType": "array"},
                    "reviewers": {"bsonType": "array"},
                    "timeline": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["event_type", "created_at"],
                            "properties": {
                                "event_type": {"bsonType": "string"},
                                "created_at": {"bsonType": "date"},
                                "actor": {"bsonType": "string"},
                                "details": {"bsonType": "object"}
                            }
                        }
                    }
                }
            }
        }

        # Commits collection
        commit_validator = {
            "$jsonSchema": {
                "bsonType": "object",
                "required": ["commit_hash", "repo_id", "created_at"],
                "properties": {
                    "commit_hash": {"bsonType": "string"},
                    "repo_id": {"bsonType": "int"},
                    "pr_number": {"bsonType": "int"},
                    "created_at": {"bsonType": "date"},
                    "author": {
                        "bsonType": "object",
                        "required": ["name", "email"],
                        "properties": {
                            "name": {"bsonType": "string"},
                            "email": {"bsonType": "string"}
                        }
                    },
                    "message": {"bsonType": "string"},
                    "stats": {
                        "bsonType": "object",
                        "properties": {
                            "files_changed": {"bsonType": "int"},
                            "insertions": {"bsonType": "int"},
                            "deletions": {"bsonType": "int"}
                        }
                    },
                    "files": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "properties": {
                                "filename": {"bsonType": "string"},
                                "status": {"bsonType": "string"},
                                "additions": {"bsonType": "int"},
                                "deletions": {"bsonType": "int"}
                            }
                        }
                    }
                }
            }
        }

        try:
            self.db.create_collection("pullRequests", validator=pr_validator)
            self.db.create_collection("commits", validator=commit_validator)
            logger.info("MongoDB collections created successfully")
        except Exception as e:
            logger.warning(f"Collections might already exist: {str(e)}")

    def create_indexes(self) -> None:
        """Create MongoDB indexes"""
        try:
            # Pull Requests indexes
            self.db.pullRequests.create_index(
                [("repo_id", ASCENDING), ("pr_number", ASCENDING)],
                unique=True
            )
            self.db.pullRequests.create_index([("created_at", ASCENDING)])
            self.db.pullRequests.create_index([("status", ASCENDING)])
            self.db.pullRequests.create_index([("author.username", ASCENDING)])

            # Commits indexes
            self.db.commits.create_index(
                [("repo_id", ASCENDING), ("commit_hash", ASCENDING)],
                unique=True
            )
            self.db.commits.create_index([("created_at", ASCENDING)])
            self.db.commits.create_index([("pr_number", ASCENDING)])
            self.db.commits.create_index([("author.email", ASCENDING)])

            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.error(f"Error creating MongoDB indexes: {str(e)}")
            raise

    def initialize_schema(self) -> None:
        """Initialize complete MongoDB schema"""
        logger.info("Initializing MongoDB schema...")
        try:
            self.create_collections()
            self.create_indexes()
            logger.info("MongoDB schema initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing MongoDB schema: {str(e)}")
            raise

class SchemaManager:
    """Combined schema management for both databases"""
    
    def __init__(
        self,
        timescale_connection: str,
        mongo_connection: str,
        mongo_database: str
    ):
        """
        Initialize schema manager
        
        Args:
            timescale_connection: TimescaleDB connection string
            mongo_connection: MongoDB connection string
            mongo_database: MongoDB database name
        """
        self.timescale = TimescaleSchema(timescale_connection)
        self.mongo = MongoSchema(mongo_connection, mongo_database)

    def initialize_all(self) -> None:
        """Initialize schemas for both databases"""
        logger.info("Initializing all database schemas...")
        try:
            self.timescale.initialize_schema()
            self.mongo.initialize_schema()
            logger.info("All database schemas initialized successfully")
        except Exception as e:
            logger.error(f"Error during schema initialization: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    # Initialize schema manager
    schema_manager = SchemaManager(
        timescale_connection="postgresql://user:pass@localhost:5432/sdlc_db",
        mongo_connection="mongodb://localhost:27017",
        mongo_database="sdlc_data"
    )

    try:
        # Initialize all schemas
        schema_manager.initialize_all()
    except Exception as e:
        logger.error(f"Failed to initialize schemas: {str(e)}")
