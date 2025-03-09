import streamlit as st
import sqlite3
from datetime import datetime

# Initialize database
def init_db():
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_progress (
            username TEXT PRIMARY KEY,
            completed_problems TEXT,
            last_activity TEXT
        )
    """)
    conn.commit()
    conn.close()

# Save user progress
def save_progress(username, completed_problems):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_progress (username, completed_problems, last_activity) 
        VALUES (?, ?, ?)
        ON CONFLICT(username) DO UPDATE SET 
            completed_problems = excluded.completed_problems,
            last_activity = excluded.last_activity
    """, (username, ",".join(completed_problems), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# Retrieve user progress
def get_progress(username):
    conn = sqlite3.connect("user_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT completed_problems FROM user_progress WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row[0].split(",") if row and row[0] else []

# Mark problem as completed
def mark_problem_complete(problem_id):
    if "username" not in st.session_state:
        st.error("You must be logged in to track progress.")
        return
    
    username = st.session_state["username"]
    progress = get_progress(username)

    if problem_id not in progress:
        progress.append(problem_id)

    save_progress(username, progress)
    st.success(f"Problem {problem_id} marked as complete!")

# Render user profile
def render_user_profile():
    if "username" not in st.session_state:
        st.error("You must be logged in to see your profile.")
        return
    
    username = st.session_state["username"]
    progress = get_progress(username)
    
    st.title(f"Welcome, {username}!")
    st.write("### Completed Problems:")
    for problem in progress:
        st.write(f"- {problem}")

# Ensure database is initialized at the start
init_db()
