#!/bin/bash

# Stop on error
set -e

echo "🛠️  Setting up the Job Application Tracker..."

# 1. Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 and try again."
    exit 1
fi

# 2. Create a virtual environment (if it doesn't exist)
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
else
    echo "✅ Virtual environment already exists."
fi

# 3. Activate the virtual environment
source .venv/bin/activate

# 4. Install dependencies
if [ -f "requirements.txt" ]; then
    echo "⬇️  Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found! Skipping dependency install."
fi

echo "✅ Setup complete! You can now run the app using: ./run.sh"