#!/bin/bash

# Use /bin/bash for better compatibility than zsh
# This script ensures the app runs inside the virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Navigate to the script directory to ensure databases are found correctly
cd "$SCRIPT_DIR"

# Check if the virtual environment exists
if [ -d ".venv" ]; then
    # Activate the virtual environment
    source .venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Running with system Python..."
    # You might want to force them to run setup.sh here, but we'll try to run globally as a fallback
fi

# Run the Streamlit app
echo "🚀 Launching Job Tracker..."
streamlit run job_tracker.py