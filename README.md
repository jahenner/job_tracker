# 📂 Job Application Tracker

A secure, local-first database to track your job applications, resume versions, and status updates. Built with Python and Streamlit.

## Features

Local Database: Uses SQLite to store your data locally (no data leaves your machine).

Status Tracking: Track applications from "Applied" to "Offer" (or "Ghosted").

Resume Versioning: Remember exactly which PDF you sent to which company.

Auto-Ghosting: Automatically marks applications as "Ghosted" if there is no activity for 45 days.

## 🚀 Quick Start (Mac/Linux)

Clone the repository:
```
git clone https://github.com/jahenner/job_tracker.git
cd job-tracker
```

Run the setup script (One time only):
This creates a virtual environment and installs the necessary libraries (streamlit, pandas) so they don't interfere with your system Python.
```
chmod +x setup.sh
./setup.sh
```

Run the app:
```
chmod +x run.sh
./run.sh
```

## 💻 Manual Setup (Windows)

If you are on Windows, you can run the following commands in PowerShell or Command Prompt:

Create a virtual environment:
```
python -m venv .venv
```

Activate it:
```
.\.venv\Scripts\activate
```

Install requirements:
```
pip install -r requirements.txt
```

Run the app:
```
streamlit run job_tracker.py
```
