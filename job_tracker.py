import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# --- Configuration & Security ---
DB_FILE = "job_applications.db"
# Number of days after which an 'Applied' job is considered 'Ghosted'
GHOST_THRESHOLD_DAYS = 45 

# --- Database Functions ---
def get_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    return conn

def init_db():
    """Initializes the database with necessary tables and default data."""
    conn = get_connection()
    c = conn.cursor()
    
    # 1. Applications Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date_applied DATE,
            company TEXT,
            title TEXT,
            status TEXT,
            resume_version TEXT,
            job_link TEXT,
            description TEXT
        )
    ''')
    
    # 2. Resumes Table (New)
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    ''')
    
    # Seed default resume if table is empty
    c.execute("SELECT count(*) FROM resumes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO resumes (name) VALUES (?)", ("Default Resume",))

    conn.commit()
    conn.close()

def add_resume(name):
    """Adds a new resume version to the database."""
    try:
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO resumes (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False # Duplicate name

def get_resumes():
    """Fetches list of available resume versions."""
    conn = get_connection()
    df = pd.read_sql("SELECT name FROM resumes ORDER BY id DESC", conn)
    conn.close()
    return df['name'].tolist()

def add_application(date_applied, company, title, status, resume_version, job_link, description):
    """Adds a new job application to the database."""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO applications (date_applied, company, title, status, resume_version, job_link, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (date_applied, company, title, status, resume_version, job_link, description))
    conn.commit()
    conn.close()

def get_all_applications():
    """Fetches all applications for the list view."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM applications ORDER BY date_applied DESC", conn)
    conn.close()
    return df

def update_status(job_id, new_status):
    """Updates the status of an application."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE applications SET status = ? WHERE id = ?", (new_status, job_id))
    conn.commit()
    conn.close()

def delete_application(job_id):
    """Deletes an application by ID."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM applications WHERE id = ?", (job_id,))
    conn.commit()
    conn.close()

def auto_ghost_applications():
    """
    Automatically updates 'Applied' or 'Screening' jobs to 'Ghosted' 
    if they are older than GHOST_THRESHOLD_DAYS.
    """
    conn = get_connection()
    c = conn.cursor()
    
    # Calculate the cutoff date
    cutoff_date = datetime.now() - timedelta(days=GHOST_THRESHOLD_DAYS)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')
    
    # Update query
    c.execute('''
        UPDATE applications 
        SET status = 'Ghosted' 
        WHERE status IN ('Applied', 'Screening') 
        AND date_applied < ?
    ''', (cutoff_str,))
    
    rows_affected = c.rowcount
    conn.commit()
    conn.close()
    return rows_affected

# --- UI Layout ---
def main():
    st.set_page_config(page_title="Job Application Tracker", layout="wide")
    
    # Initialize DB
    init_db()

    # Run Auto-Ghosting Logic on startup
    ghosted_count = auto_ghost_applications()
    if ghosted_count > 0:
        st.toast(f"👻 Updated {ghosted_count} old applications to 'Ghosted' status.", icon="👻")

    st.title("📂 Job Application Database")

    # --- Sidebar ---
    with st.sidebar:
        st.header("Add New Application")
        
        # Resume Management Section
        with st.expander("⚙️ Manage Resumes"):
            new_resume_name = st.text_input("Add New Resume Name")
            if st.button("Add Resume"):
                if new_resume_name:
                    success = add_resume(new_resume_name)
                    if success:
                        st.success(f"Added '{new_resume_name}'")
                        st.rerun()
                    else:
                        st.error("Resume name already exists.")
        
        # Get latest resume options
        resume_options = get_resumes()

        with st.form("add_job_form", clear_on_submit=True):
            date_applied = st.date_input("Date Applied", datetime.now())
            company = st.text_input("Company Name")
            title = st.text_input("Job Title")
            status = st.selectbox("Current Status", ["Applied", "Screening", "Interviewing", "Offer", "Rejected", "Ghosted"])
            
            # UPDATED: Resume is now a dropdown
            resume_version = st.selectbox("Resume Version Sent", resume_options)
            
            job_link = st.text_input("Link to Posting (URL)")
            description = st.text_area("Job Description / Notes (Paste full text here)")
            
            submitted = st.form_submit_button("Save Application")
            
            if submitted:
                if company and title:
                    add_application(date_applied, company, title, status, resume_version, job_link, description)
                    st.success(f"Saved application for {title} at {company}!")
                    st.rerun() # Refresh data immediately
                else:
                    st.error("Company and Job Title are required.")

    # --- Main Content Area ---
    
    # Fetch Data
    df = get_all_applications()

    if df.empty:
        st.info("No job applications found. Add one using the sidebar!")
    else:
        # Top-level metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Applications", len(df))
        col2.metric("Active Processes", len(df[~df['status'].isin(['Rejected', 'Ghosted'])]))
        col3.metric("Offers", len(df[df['status'] == 'Offer']))

        st.markdown("---")

        # 1. List View (Dataframe)
        st.subheader("📋 Application List")
        st.caption("Select a row below to view details")
        
        # We format the date column for better readability
        display_df = df.copy()
        display_df['date_applied'] = pd.to_datetime(display_df['date_applied']).dt.strftime('%Y-%m-%d')
        
        # Display interactive table with selection enabled
        selection = st.dataframe(
            display_df[['id', 'date_applied', 'company', 'title', 'status', 'resume_version']],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row"
        )

        st.markdown("---")

        # 2. Expanded View
        st.subheader("🔍 Expanded Job Details")
        
        # --- Logic to Resolve Selected Job ID ---
        selected_id = None
        
        # Priority A: User manually clicked a row in the table just now
        if len(selection.selection.rows) > 0:
            selected_index = selection.selection.rows[0]
            selected_id = int(display_df.iloc[selected_index]['id'])
            
            # If user explicitly clicks a row, we clear the "auto-remembered" update ID
            # so the UI feels responsive to their click
            if 'updated_job_id' in st.session_state:
                del st.session_state.updated_job_id

        # Priority B: User just updated a job, and the table selection was cleared by the refresh
        # We want to keep showing the details for that job.
        elif 'updated_job_id' in st.session_state:
            # Verify the ID still exists in the data (e.g., wasn't deleted)
            if st.session_state.updated_job_id in display_df['id'].values:
                selected_id = st.session_state.updated_job_id
        # ----------------------------------------

        if selected_id is not None:
            # Fetch full job data
            job_data = df[df['id'] == selected_id].iloc[0]

            # Layout for details
            d_col1, d_col2 = st.columns([2, 1])

            with d_col1:
                st.markdown(f"### {job_data['title']} @ {job_data['company']}")
                if job_data['job_link']:
                    st.markdown(f"**Original Link:** [{job_data['job_link']}]({job_data['job_link']})")
                
                st.markdown("#### Job Description / Notes")
                st.markdown("---")
                st.markdown(job_data['description'])
            
            with d_col2:
                # Status Management Section
                st.subheader("Status Management")
                status_options = ["Applied", "Screening", "Interviewing", "Offer", "Rejected", "Ghosted"]
                
                # Determine current index for default value
                current_index = 0
                if job_data['status'] in status_options:
                    current_index = status_options.index(job_data['status'])
                
                # Use a dynamic key based on ID so state doesn't leak between jobs
                new_status = st.selectbox(
                    "Current Status", 
                    status_options, 
                    index=current_index, 
                    key=f"status_update_box_{selected_id}"
                )
                
                # Show update button only if status has changed
                if new_status != job_data['status']:
                    if st.button("Update Status"):
                        update_status(selected_id, new_status)
                        
                        # --- NEW: Save this ID to session state before rerun ---
                        st.session_state.updated_job_id = selected_id
                        # -------------------------------------------------------
                        
                        st.success(f"Status updated to {new_status}!")
                        st.rerun()

                st.divider()
                st.write(f"**Applied:** {job_data['date_applied']}")
                st.write(f"**Resume Used:** {job_data['resume_version']}")
                
                st.divider()
                st.warning("Danger Zone")
                if st.button(f"Delete Application {selected_id}", type="primary"):
                    delete_application(selected_id)
                    st.success("Deleted!")
                    st.rerun()
        else:
            st.info("👆 Select a job in the table above to view details.")

if __name__ == "__main__":
    # Check if the script is running with the Streamlit runtime
    if st.runtime.exists():
        main()
    else:
        # If run as a standard Python script, warn the user
        print(f"⚠️  Please run this app using Streamlit: streamlit run {os.path.basename(__file__)}")