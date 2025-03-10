import streamlit as st
from streamlit_ace import st_ace
import streamlit.components.v1 as components
import os
import re
import glob
import markdown
import base64
from pathlib import Path
import importlib.util
import sys
from io import StringIO
import contextlib
import json
from datetime import datetime, date
import calendar
import tempfile
import subprocess

# Constants
PROBLEMS_DIR = "Problems"
SUPPORTED_EXTENSIONS = ['.md', '.html', '.py']
USER_DATA_FILE = "user_data.json"

# Utility Functions
def get_problem_directories():
    """Get all problem directories sorted numerically"""
    if not os.path.exists(PROBLEMS_DIR):
        os.makedirs(PROBLEMS_DIR)
        
    problem_dirs = [d for d in os.listdir(PROBLEMS_DIR) 
                   if os.path.isdir(os.path.join(PROBLEMS_DIR, d))]
    
    def get_number(dirname):
        match = re.match(r'(\d+)_', dirname)
        return int(match.group(1)) if match else float('inf')
    
    return sorted(problem_dirs, key=get_number)

def load_file_content(file_path):
    """Load and return file content with proper encoding"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return ""

def save_file_content(file_path, content):
    """Save content to file with proper encoding"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        st.success(f"Successfully saved changes to {file_path}")
    except Exception as e:
        st.error(f"Error saving file: {e}")

def render_math_content(content, file_ext):
    """Render content with MathJax support"""
    if file_ext == '.md':
        content = markdown.markdown(content)
    
    content = re.sub(r'\\\(', r'$', content)
    content = re.sub(r'\\\)', r'$', content)
    content = re.sub(r'\\\[', r'$$', content)
    content = re.sub(r'\\\]', r'$$', content)
    
    return components.html(
        f"""
        <div style="padding: 20px;">
            {content}
        </div>
        <script>
            window.MathJax = {{
                tex: {{
                    inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                    displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
                }},
                svg: {{
                    fontCache: 'global'
                }}
            }};
        </script>
        <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
        """,
        height=600,
        scrolling=True
    )

def get_problem_solutions(problem_dir):
    """Get all solution files for a problem"""
    solutions = []
    if os.path.exists(problem_dir):
        for file in os.listdir(problem_dir):
            if file.startswith('solution') and file.endswith('.py'):
                solutions.append(file)
    return sorted(solutions)

def run_code_in_file(code):
    """Run Python code in a temporary file and capture output"""
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a temporary Python file
        temp_file = os.path.join(temp_dir, "temp_code.py")
        output_file = os.path.join(temp_dir, "output.txt")
        
        # Write the code to the file
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        try:
            # Run the Python file and redirect output
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Capture both stdout and stderr
            output = result.stdout
            if result.returncode != 0:
                output += f"\nError: {result.stderr}"
                
            # Write output to file as well
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(output)
            
            return output
        except subprocess.TimeoutExpired:
            return "Execution timed out (limit: 30 seconds)"
        except Exception as e:
            return f"Error executing code: {str(e)}"

# Alternative method using exec directly
def run_code_direct(code):
    """Run Python code directly and capture output"""
    # Create a StringIO object to capture stdout
    stdout_capture = StringIO()
    stderr_capture = StringIO()
    
    # Redirect stdout and stderr
    sys_stdout_original = sys.stdout
    sys_stderr_original = sys.stderr
    sys.stdout = stdout_capture
    sys.stderr = stderr_capture
    
    # Create a dictionary for locals
    local_vars = {}
    
    try:
        # Execute the code
        exec(code, globals(), local_vars)
        output = stdout_capture.getvalue()
        
        # Check if there was any output
        if not output.strip():
            output = "Code executed successfully, but produced no output."
            
        return output
    except Exception as e:
        # Capture any exceptions
        error_msg = f"Error: {str(e)}"
        sys.stderr.write(error_msg)
        return error_msg
    finally:
        # Restore stdout and stderr
        sys.stdout = sys_stdout_original
        sys.stderr = sys_stderr_original

# User Progress Management
class UserProgress:
    def __init__(self):
        self.load_user_data()
    
    def load_user_data(self):
        if os.path.exists(USER_DATA_FILE):
            with open(USER_DATA_FILE, 'r') as f:
                self.data = json.load(f)
        else:
            self.data = {
                "completed_problems": [],
                "daily_progress": {},
                "current_streak": 0,
                "last_daily_challenge": None
            }
    
    def save_user_data(self):
        with open(USER_DATA_FILE, 'w') as f:
            json.dump(self.data, f)
    
    def mark_problem_complete(self, problem_id):
        if problem_id not in self.data["completed_problems"]:
            self.data["completed_problems"].append(problem_id)
            today = date.today().isoformat()
            self.data["daily_progress"][today] = self.data["daily_progress"].get(today, 0) + 1
            self.update_streak()
            self.save_user_data()
    
    def update_streak(self):
        today = date.today()
        streak = 0
        current_date = today
        
        while current_date.isoformat() in self.data["daily_progress"]:
            streak += 1
            current_date = current_date.replace(day=current_date.day - 1)
        
        self.data["current_streak"] = streak

# UI Components
def setup_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="Deep-ML Interactive Platform",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .stButton button {
            width: 100%;
        }
        .stProgress > div > div > div {
            background-color: #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    """Render the application header with navigation"""
    col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
    with col1:
        st.title("Deep-ML")
    with col2:
        if st.button("Problems", key="nav_problems"):
            st.session_state["page"] = "problem_explorer"
    with col3:
        if st.button("Daily Challenge", key="nav_challenge"):
            st.session_state["page"] = "daily_challenge"
    with col4:
        if st.button("Submit Problem", key="nav_submit"):
            st.session_state["page"] = "submit_problem"
    with col5:
        if st.button("Profile", key="nav_profile"):
            st.session_state["page"] = "profile"

def get_problem_metadata():
    """Get metadata for all problems including difficulty and category"""
    problems = []
    for problem_dir in get_problem_directories():
        match = re.match(r'(\d+)_(.+)', problem_dir)
        if match:
            number, name = match.groups()
            
            # Determine difficulty and category
            if int(number) < 10:
                difficulty = "easy"
            elif int(number) < 20:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
            # Determine category based on content
            name_lower = name.lower()
            if "matrix" in name_lower or "eigen" in name_lower:
                category = "Linear Algebra"
            elif "regression" in name_lower or "learning" in name_lower:
                category = "Machine Learning"
            elif "tree" in name_lower or "graph" in name_lower:
                category = "Data Structures"
            else:
                category = "Mathematics"
            
            problems.append({
                "id": int(number),
                "title": name.replace('_', ' '),
                "difficulty": difficulty,
                "category": category,
                "directory": problem_dir
            })
    
    return sorted(problems, key=lambda x: x["id"])

def render_problem_explorer():
    """Render the problem explorer with filtering and sorting"""
    st.header("Problem Explorer")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        difficulty_filter = st.selectbox(
            "Difficulty",
            ["All", "Easy", "Medium", "Hard"],
            key="difficulty_filter"
        )
    
    with col2:
        categories = ["All", "Linear Algebra", "Machine Learning", 
                     "Data Structures", "Mathematics"]
        category_filter = st.selectbox(
            "Category",
            categories,
            key="category_filter"
        )
    
    with col3:
        search = st.text_input("Search", key="problem_search")
    
    # Get and filter problems
    problems = get_problem_metadata()
    
    if difficulty_filter != "All":
        problems = [p for p in problems if p["difficulty"].lower() == difficulty_filter.lower()]
    if category_filter != "All":
        problems = [p for p in problems if p["category"] == category_filter]
    if search:
        problems = [p for p in problems if search.lower() in p["title"].lower()]
    
    # Display problems
    render_problems_table(problems)

def render_problems_table(problems):
    """Render the problems in a table format"""
    for idx, problem in enumerate(problems):
        with st.container():
            cols = st.columns([1, 3, 2, 2, 2])
            
            # Problem ID and Title
            cols[0].write(f"#{problem['id']}")
            cols[1].write(problem["title"])
            
            # Difficulty with color coding
            difficulty_colors = {
                "easy": "green",
                "medium": "orange",
                "hard": "red"
            }
            cols[2].markdown(
                f'<span style="color: {difficulty_colors[problem["difficulty"]]}">'
                f'{problem["difficulty"].capitalize()}</span>',
                unsafe_allow_html=True
            )
            
            # Category
            cols[3].write(problem["category"])
            
            # Actions
            if cols[4].button("Solve", key=f"solve_{problem['id']}_{idx}"):
                st.session_state["current_problem"] = problem
                st.session_state["page"] = "problem_solver"
            
            st.markdown("---")

def render_problem_solver(problem):
    """Render the problem solving environment"""
    st.header(f"Problem {problem['id']}: {problem['title']}")
    
    problem_path = os.path.join(PROBLEMS_DIR, problem['directory'])
    
    # Create tabs
    tabs = st.tabs(["Description", "Editor", "Solutions"])
    
    # Description Tab
    with tabs[0]:
        description_file = next(
            (f for f in os.listdir(problem_path) if f.startswith("learn.")),
            None
        )
        if description_file:
            content = load_file_content(os.path.join(problem_path, description_file))
            render_math_content(content, os.path.splitext(description_file)[1])
    
    # Editor Tab
    with tabs[1]:
        st.write("## Code Editor")
        
        # Use session state to store code and output
        if f"code_{problem['id']}" not in st.session_state:
            st.session_state[f"code_{problem['id']}"] = """# Write your solution here
# Example:
def matrix_dot_vector(matrix, vector):
    result = []
    for row in matrix:
        result.append(sum(a*b for a, b in zip(row, vector)))
    return result

# Test with sample data
matrix = [[1, 2], [3, 4]]
vector = [5, 6]
print(f"Matrix: {matrix}")
print(f"Vector: {vector}")
print(f"Result: {matrix_dot_vector(matrix, vector)}")
"""
        
        if f"output_{problem['id']}" not in st.session_state:
            st.session_state[f"output_{problem['id']}"] = ""
        
        # Code editor
        code = st_ace(
            value=st.session_state[f"code_{problem['id']}"],
            placeholder="Write your solution here...",
            language="python",
            theme="monokai",
            key=f"editor_{problem['id']}",
            height=400
        )
        
        # Update code in session state
        st.session_state[f"code_{problem['id']}"] = code
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Code", key=f"run_{problem['id']}"):
                with st.spinner("Running code..."):
                    try:
                        # Try both methods
                        try:
                            output = run_code_in_file(code)
                        except Exception as e1:
                            try:
                                # Fallback to direct execution
                                output = run_code_direct(code)
                            except Exception as e2:
                                output = f"Error executing code: {str(e1)}\nTried alternate method: {str(e2)}"
                        
                        # Store output in session state
                        st.session_state[f"output_{problem['id']}"] = output
                    except Exception as e:
                        st.session_state[f"output_{problem['id']}"] = f"Unexpected error: {str(e)}"
        
        with col2:
            if st.button("Submit", key=f"submit_{problem['id']}"):
                solution_name = st.text_input(
                    "Save solution as:",
                    value=f"solution_{len(get_problem_solutions(problem_path)) + 1}.py",
                    key=f"solution_name_{problem['id']}"
                )
                if st.button("Save Solution", key=f"save_{problem['id']}"):
                    save_file_content(
                        os.path.join(problem_path, solution_name),
                        code
                    )
                    st.session_state.user_progress.mark_problem_complete(problem['id'])
        
        # Display output
        if st.session_state[f"output_{problem['id']}"]:
            st.write("### Output:")
            st.code(st.session_state[f"output_{problem['id']}"])
    
    # Solutions Tab
    with tabs[2]:
        solutions = get_problem_solutions(problem_path)
        if solutions:
            # Use session state for solution output
            if f"solution_output_{problem['id']}" not in st.session_state:
                st.session_state[f"solution_output_{problem['id']}"] = ""
            
            selected_solution = st.selectbox(
                "Select Solution",
                solutions,
                key=f"solution_select_{problem['id']}"
            )
            
            if selected_solution:
                solution_content = load_file_content(
                    os.path.join(problem_path, selected_solution)
                )
                st.code(solution_content, language='python')
                
                if st.button("Run Solution", key=f"run_solution_{problem['id']}"):
                    with st.spinner("Running solution..."):
                        try:
                            # Try both methods
                            try:
                                output = run_code_in_file(solution_content)
                            except Exception as e1:
                                try:
                                    # Fallback to direct execution
                                    output = run_code_direct(solution_content)
                                except Exception as e2:
                                    output = f"Error executing code: {str(e1)}\nTried alternate method: {str(e2)}"
                            
                            # Store output in session state
                            st.session_state[f"solution_output_{problem['id']}"] = output
                        except Exception as e:
                            st.session_state[f"solution_output_{problem['id']}"] = f"Unexpected error: {str(e)}"
                
                # Display solution output
                if st.session_state[f"solution_output_{problem['id']}"]:
                    st.write("### Output:")
                    st.code(st.session_state[f"solution_output_{problem['id']}"])
        else:
            st.info("No solutions available yet.")

def render_daily_challenge():
    """Render the daily challenge"""
    st.header("Daily Challenge")
    
    today = date.today()
    problems = get_problem_metadata()
    
    if problems:
        # Select a problem based on the date
        problem_index = today.toordinal() % len(problems)
        problem = problems[problem_index]
        
        st.write(f"### Problem {problem['id']}: {problem['title']}")
        st.write(f"**Difficulty:** {problem['difficulty'].capitalize()}")
        st.write(f"**Category:** {problem['category']}")
        
        if st.button("Start Challenge", key="start_daily_challenge"):
            st.session_state["current_problem"] = problem
            st.session_state["page"] = "problem_solver"
    else:
        st.warning("No problems available for daily challenge.")

def render_user_profile():
    """Render user profile and statistics"""
    st.header("Your Profile")
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_problems = len(get_problem_directories())
        completed = len(st.session_state.user_progress.data["completed_problems"])
        completion_rate = (completed / total_problems * 100) if total_problems > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")
    
    with col2:
        st.metric("Problems Solved", completed)
    
    with col3:
        st.metric("Current Streak", f"{st.session_state.user_progress.data['current_streak']} days")
    
    # Progress Calendar
    st.write("## Progress Calendar")
    today = date.today()
    cal = calendar.monthcalendar(today.year, today.month)
    
    # Create calendar grid
    cols = st.columns(7)
    for i, day in enumerate(["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]):
        cols[i].write(f"**{day}**")
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("")
            else:
                date_str = f"{today.year}-{today.month:02d}-{day:02d}"
                if date_str in st.session_state.user_progress.data["daily_progress"]:
                    cols[i].markdown(f"**{day}** ✅")
                else:
                    cols[i].write(str(day))
    
    # Problem History
    st.write("## Problem History")
    if completed > 0:
        problems = get_problem_metadata()
        completed_problems = [p for p in problems 
                            if p["id"] in st.session_state.user_progress.data["completed_problems"]]
        
        for problem in completed_problems:
            with st.expander(f"Problem {problem['id']}: {problem['title']}"):
                st.write(f"**Category:** {problem['category']}")
                st.write(f"**Difficulty:** {problem['difficulty'].capitalize()}")
                
                # Show solutions
                problem_path = os.path.join(PROBLEMS_DIR, problem['directory'])
                solutions = get_problem_solutions(problem_path)
                if solutions:
                    st.write("**Your Solutions:**")
                    for solution in solutions:
                        st.code(load_file_content(os.path.join(problem_path, solution)), 
                               language='python')
    else:
        st.info("You haven't solved any problems yet. Start solving to build your history!")

def render_submit_problem():
    """Render the problem submission form"""
    st.header("Submit a New Problem")
    
    with st.form("problem_submission"):
        st.write("### Problem Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            problem_number = st.number_input(
                "Problem Number",
                min_value=1,
                help="Must be unique"
            )
            
            problem_title = st.text_input(
                "Problem Title",
                help="A descriptive title for the problem"
            )
            
            difficulty = st.selectbox(
                "Difficulty Level",
                ["Easy", "Medium", "Hard"]
            )
        
        with col2:
            category = st.selectbox(
                "Category",
                ["Linear Algebra", "Machine Learning", "Data Structures", "Mathematics"]
            )
            
            tags = st.text_input(
                "Tags",
                help="Comma-separated tags"
            )
        
        st.write("### Problem Content")
        
        description = st.text_area(
            "Problem Description (Markdown)",
            height=200,
            help="Support Markdown and LaTeX"
        )
        
        sample_solution = st.text_area(
            "Sample Solution",
            height=200,
            help="Python code"
        )
        
        submitted = st.form_submit_button("Submit Problem")
        
        if submitted:
            try:
                # Create problem directory
                problem_dir = f"{problem_number}_{problem_title.replace(' ', '_')}"
                problem_path = os.path.join(PROBLEMS_DIR, problem_dir)
                os.makedirs(problem_path, exist_ok=True)
                
                # Save description
                with open(os.path.join(problem_path, 'learn.md'), 'w') as f:
                    f.write(description)
                
                # Save sample solution
                with open(os.path.join(problem_path, 'solution.py'), 'w') as f:
                    f.write(sample_solution)
                
                st.success("Problem submitted successfully!")
                
            except Exception as e:
                st.error(f"Error submitting problem: {str(e)}")

def main():
    """Main application function"""
    setup_page()
    
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state["page"] = "home"
    if "user_progress" not in st.session_state:
        st.session_state["user_progress"] = UserProgress()
    if "current_problem" not in st.session_state:
        st.session_state["current_problem"] = None
    if "nav_selection" not in st.session_state:
        st.session_state["nav_selection"] = "Home"
    
    # Render header
    render_header()
    
    # Sidebar navigation - using session state to prevent unnecessary reruns
    with st.sidebar:
        st.title("Navigation")
        current_nav = st.radio(
            "Go to",
            ["Home", "Problem Explorer", "Daily Challenge", "Profile", "Submit Problem"],
            key="navigation",
            index=["Home", "Problem Explorer", "Daily Challenge", "Profile", "Submit Problem"].index(st.session_state["nav_selection"])
        )
        
        # Only update and rerun if navigation actually changed
        if current_nav != st.session_state["nav_selection"]:
            st.session_state["nav_selection"] = current_nav
            st.session_state["page"] = current_nav.lower().replace(" ", "_")
            st.rerun()
    
    # Main content
    if st.session_state["page"] == "home":
        render_daily_challenge()
        st.markdown("---")
        render_problem_explorer()
    
    elif st.session_state["page"] == "problem_explorer":
        render_problem_explorer()
    
    elif st.session_state["page"] == "daily_challenge":
        render_daily_challenge()
    
    elif st.session_state["page"] == "profile":
        render_user_profile()
    
    elif st.session_state["page"] == "submit_problem":
        render_submit_problem()
    
    elif st.session_state["page"] == "problem_solver" and st.session_state["current_problem"]:
        render_problem_solver(st.session_state["current_problem"])

if __name__ == "__main__":
    main()