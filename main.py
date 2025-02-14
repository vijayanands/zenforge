import os
import sys
from pathlib import Path
import argparse
from functions.data_ingestion.bootstrap import bootstrap_data

def run_streamlit():
    """Run Streamlit app programmatically"""
    import streamlit.web.cli as stcli
    
    # Get the absolute path to app.py
    app_path = Path(__file__).parent / "streamlit_app.py"
    
    # Set up command line arguments
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port=8501",
        "--server.address=localhost",
        "--browser.serverAddress=localhost",
        "--server.headless=false",
        "--browser.serverPort=8501",
        "--browser.gatherUsageStats=false"
    ]
    
    if os.environ.get('STREAMLIT_BROWSER_GATHER_USAGE_STATS', None) is None:
        os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    sys.exit(stcli.main())

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='ZenForge Application')
    parser.add_argument(
        '--bootstrap',
        action='store_true',
        default=False,
        help='Bootstrap data before starting the application'
    )
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    
    if args.bootstrap:
        print("Bootstrapping data...")
        try:
            bootstrap_data()
            print("Data bootstrapping completed successfully.")
        except Exception as e:
            print(f"Error bootstrapping data: {str(e)}")
            sys.exit(1)
    
    print("Starting Streamlit app...")
    run_streamlit()
