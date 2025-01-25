import os
import fcntl
from datetime import datetime, timedelta, timezone
import pytz
from typing import List, Dict, Any, Optional
import schedule
import time
import json
from pathlib import Path
import pinecone
from pymongo import MongoClient
import logging
from tools.github.github import pull_github_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Pinecone
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "gcp-starter")
PINECONE_INDEX = "github-data"

# Initialize MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB = "github_analytics"
MONGO_COLLECTION = "github_data"
SYNC_LOCK_FILE = "/tmp/github_sync.lock"
SYNC_STATE_COLLECTION = "sync_state"

class LockFile:
    """Context manager for handling file locks"""
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.fd = None

    def __enter__(self):
        self.fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self
        except IOError:
            self.fd.close()
            raise RuntimeError("Another sync process is already running")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            self.fd.close()
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)

class GitHubDataSync:
    def __init__(self):
        # Initialize Pinecone
        pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)
        if PINECONE_INDEX not in pinecone.list_indexes():
            pinecone.create_index(PINECONE_INDEX, dimension=1536)
        self.pinecone_index = pinecone.Index(PINECONE_INDEX)
        
        # Initialize MongoDB
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[MONGO_DB]
        self.collection = self.db[MONGO_COLLECTION]
        self.sync_state = self.db[SYNC_STATE_COLLECTION]
        
        # Create indexes
        self.collection.create_index([("repo", 1), ("timestamp", 1)])
        self.sync_state.create_index([("repo", 1)], unique=True)
        
    def _load_repo_list(self) -> List[Dict[str, str]]:
        """Load repository list from config file"""
        config_path = Path("config/github_repos.json")
        if not config_path.exists():
            raise FileNotFoundError("Repository configuration file not found")
            
        with open(config_path) as f:
            return json.load(f)
            
    def _get_sync_state(self, repo: str) -> Optional[datetime]:
        """Get the last successful sync state for a repository"""
        state = self.sync_state.find_one({"repo": repo})
        return state["last_successful_sync"] if state else None

    def _update_sync_state(self, repo: str, sync_time: datetime, status: str = "success"):
        """Update the sync state for a repository"""
        self.sync_state.update_one(
            {"repo": repo},
            {
                "$set": {
                    "last_successful_sync": sync_time,
                    "status": status,
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )

    def _store_data(self, data: Dict[str, Any], repo: str):
        """Store data in both Pinecone and MongoDB"""
        # Store in MongoDB
        data["timestamp"] = datetime.now(timezone.utc)
        data["repo"] = repo
        self.collection.insert_one(data)
        
        # Convert to vector format and store in Pinecone
        # Note: You'll need to implement the vectorization logic based on your needs
        vectors = self._vectorize_data(data)
        self.pinecone_index.upsert(vectors)
        
    def _vectorize_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert GitHub data to vectors for Pinecone storage"""
        # Implement your vectorization logic here
        # This is a placeholder - you'll need to implement actual embedding logic
        pass
        
    def bootstrap(self, force: bool = False):
        """Bootstrap data from all repositories"""
        if force:
            # Clear existing data
            self.collection.delete_many({})
            self.pinecone_index.delete(delete_all=True)
            
        repos = self._load_repo_list()
        
        for repo in repos:
            print(f"Bootstrapping data for {repo['owner']}/{repo['name']}")
            github_data, user_info = pull_github_data(
                start_date="2020-01-01",  # Or your desired start date
                end_date=datetime.now().strftime("%Y-%m-%d"),
                owner=repo["owner"],
                repo=repo["name"]
            )
            
            self._store_data({
                "github_data": github_data,
                "user_info": user_info,
                "repo": f"{repo['owner']}/{repo['name']}"
            }, f"{repo['owner']}/{repo['name']}")
            
    def sync(self):
        """Synchronize data from all repositories with lock protection"""
        try:
            with LockFile(SYNC_LOCK_FILE):
                logger.info("Starting sync process")
                repos = self._load_repo_list()
                
                for repo in repos:
                    repo_name = f"{repo['owner']}/{repo['name']}"
                    try:
                        last_sync = self._get_sync_state(repo_name)
                        if last_sync:
                            start_date = last_sync
                        else:
                            start_date = datetime.now(timezone.utc) - timedelta(days=1)
                            
                        logger.info(f"Syncing data for {repo_name} since {start_date}")
                        
                        github_data, user_info = pull_github_data(
                            start_date=start_date.strftime("%Y-%m-%d"),
                            end_date=datetime.now().strftime("%Y-%m-%d"),
                            owner=repo["owner"],
                            repo=repo["name"]
                        )
                        
                        self._store_data({
                            "github_data": github_data,
                            "user_info": user_info,
                            "repo": repo_name
                        }, repo_name)
                        
                        # Update sync state only after successful storage
                        self._update_sync_state(repo_name, datetime.now(timezone.utc))
                        logger.info(f"Successfully synced {repo_name}")
                        
                    except Exception as e:
                        logger.error(f"Error syncing {repo_name}: {str(e)}")
                        self._update_sync_state(repo_name, datetime.now(timezone.utc), "failed")
                        continue
                
                logger.info("Sync process completed")
                
        except RuntimeError as e:
            logger.warning(f"Sync process already running: {str(e)}")
        except Exception as e:
            logger.error(f"Error in sync process: {str(e)}")

    def schedule_sync(self, frequency: str = "daily"):
        """Schedule regular synchronization"""
        pst = pytz.timezone('America/Los_Angeles')
        
        if frequency == "daily":
            schedule.every().day.at("00:00").do(self.sync)
        elif frequency == "hourly":
            schedule.every().hour.do(self.sync)
        elif frequency == "weekly":
            schedule.every().week.at("00:00").do(self.sync)
        else:
            raise ValueError(f"Unsupported frequency: {frequency}")
            
        logger.info(f"Scheduled sync with {frequency} frequency")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in scheduled sync: {str(e)}")
                time.sleep(300)  # Wait 5 minutes before retrying

def main():
    syncer = GitHubDataSync()
    
    import argparse
    parser = argparse.ArgumentParser(description='GitHub Data Synchronization Tool')
    parser.add_argument('--bootstrap', action='store_true', help='Bootstrap historical data')
    parser.add_argument('--force', action='store_true', help='Force bootstrap (clear existing data)')
    parser.add_argument('--schedule', choices=['daily', 'hourly', 'weekly'], 
                       help='Schedule regular synchronization')
    parser.add_argument('--once', action='store_true', help='Run sync once and exit')
    
    args = parser.parse_args()
    
    try:
        if args.bootstrap:
            syncer.bootstrap(force=args.force)
        elif args.schedule:
            syncer.schedule_sync(args.schedule)
        elif args.once:
            syncer.sync()
        else:
            parser.print_help()
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

if __name__ == "__main__":
    main() 