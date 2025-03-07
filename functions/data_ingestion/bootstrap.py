import json
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path

from functions.data_ingestion.ingestion import ingest_data
from utils import get_log_level

# Set up logging
logging.basicConfig(
    level=get_log_level(),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pinecone_ingestion.log'),
        logging.StreamHandler()
    ]
)

def get_last_ingestion_timestamp() -> datetime:
    """Read the last ingestion timestamp from file"""
    timestamp_file = Path(__file__).parent / 'last_ingestion.json'
    if timestamp_file.exists():
        with open(timestamp_file) as f:
            data = json.load(f)
            return datetime.fromisoformat(data['last_timestamp'])
    return datetime(2024, 1, 1)  # Default start date

def save_last_ingestion_timestamp(timestamp: datetime) -> None:
    """Save the last ingestion timestamp to file"""
    timestamp_file = Path(__file__).parent / 'last_ingestion.json'
    with open(timestamp_file, 'w', encoding='utf-8') as f:  # Ensure correct encoding
        json.dump({'last_timestamp': timestamp.isoformat()}, f)  # f should be compatible

def ingest_data_into_pinecone_until_now():
    """
    Ingest data into Pinecone in weekly chunks, starting from the last ingestion timestamp
    until the current date. Sleeps for 15 minutes between chunks.
    """
    current_date = datetime.now()
    start_date = get_last_ingestion_timestamp()
    
    logging.info(f"Starting ingestion process from {start_date} until {current_date}")
    
    while start_date < current_date:
        # Calculate end date for this chunk (1 week later or current date)
        end_date = min(start_date + timedelta(days=7), current_date)
        
        try:
            logging.info(f"Importing data for period: {start_date} to {end_date}")
            ingest_data(start_date, end_date, False)
            logging.info(f"Successfully imported data for period ending {end_date}")
            
            # Save the successful import timestamp
            save_last_ingestion_timestamp(end_date)
            
            # Update start_date for next iteration
            start_date = end_date
            
            # If we haven't reached current date, sleep for 15 minutes
            if start_date < current_date:
                logging.info("Sleeping for 15 minutes before next import...")
                time.sleep(900)  # 15 minutes in seconds
                
        except Exception as e:
            logging.error(f"Error during import for period {start_date} to {end_date}: {str(e)}")
            logging.info("Retrying in 15 minutes...")
            time.sleep(900)
            continue
    
    logging.info("Data ingestion completed successfully")
    return current_date

def bootstrap_data():
    try:
        logging.info("Starting Pinecone data ingestion process")
        final_timestamp = ingest_data_into_pinecone_until_now()
        logging.info(f"Completed all data ingestion up to {final_timestamp}")
    except Exception as e:
        logging.error(f"Fatal error in data ingestion process: {str(e)}")
        raise

if __name__ == "__main__":
    bootstrap_data()