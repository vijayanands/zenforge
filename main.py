import os
import sys
from pathlib import Path

def run_streamlit():
    """Run Streamlit app programmatically"""
    import streamlit.web.cli as stcli
    
    # Get the absolute path to streamlit_app.py
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

if __name__ == "__main__":
    print("Starting Streamlit app...")
    run_streamlit()
