"""
Main entry point for Streamlit Cloud deployment.
This file is used by Streamlit Cloud as the default app script.
Can also be run locally with: streamlit run streamlit_app.py
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Run the dashboard
from app.dashboard import main

if __name__ == "__main__":
    main()
