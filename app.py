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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, Any, Tuple
import traceback
from login import login_page, reset_password_page
from dataprogress import init_db
import google.generativeai as genai

# Configure Gemini AI
GOOGLE_API_KEY = "AIzaSyCwDX96UpqCpWZQsN7RDgtjgW0Pl8uf7bk"
genai.configure(api_key=GOOGLE_API_KEY)

# def get_gemini_suggestion(error_message):
#     """Get a suggestion from Gemini AI based on the error message."""
#     try:
#         response = genai.generate_text(f"Suggest a fix for this Python error: {error_message}")
#         return response.text
#     except Exception as e:
#         return f"Error retrieving suggestion: {str(e)}"

gemini_model = genai.GenerativeModel("gemini-pro")

def get_gemini_suggestion(error_message):
    """Get a suggestion from Gemini AI based on the error message."""
    try:
        response = gemini_model.generate_content(f"Suggest a fix for this Python error: {error_message}")
        return response.text
    except Exception as e:
        return f"Error retrieving suggestion: {str(e)}"
# Constants
PROBLEMS_DIR = "Problems"
SUPPORTED_EXTENSIONS = ['.md', '.html', '.py']
USER_DATA_FILE = "user_data.json"

class CodeExecutor:
    def __init__(self):
        self.globals = {
            'np': np,
            'pd': pd,
            'plt': plt,
            'sns': sns,
        }
        self.locals = {}
    
    def execute(self, code: str) -> Tuple[str, str, Dict[str, Any]]:
        """Execute code and return stdout, stderr, and local variables"""
        stdout = StringIO()
        stderr = StringIO()
        
        if 'plt' in code:
            plt.figure()
        
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(code, self.globals, self.locals)
                
                if 'plt' in code:
                    fig = plt.gcf()
                    if len(fig.axes) > 0:
                        plt_path = "temp_plot.png"
                        plt.savefig(plt_path)
                        plt.close()
                        self.locals['_plot_path'] = plt_path
                
        except Exception as e:
            stderr.write(f"Error: {str(e)}\n")
            stderr.write(traceback.format_exc())
        
        return stdout.getvalue(), stderr.getvalue(), self.locals

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

def setup_page():
    """Configure the Streamlit page settings"""
    st.set_page_config(
        page_title="ML Interactive Platform",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Inject custom CSS to style the login form properly
    

def render_header():
    """Render the application header with navigation"""
    col2, col3, col4, col5 = st.columns([ 1, 1, 1, 1])
 
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
    """Get metadata for all problems"""
    problems = []
    for problem_dir in get_problem_directories():
        match = re.match(r'(\d+)_(.+)', problem_dir)
        if match:
            number, name = match.groups()
            
            if int(number) < 10:
                difficulty = "easy"
            elif int(number) < 20:
                difficulty = "medium"
            else:
                difficulty = "hard"
            
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
    st.markdown(
    """
    <style>
    .custom-header {
        
        font-size: 20px;     /* Adjust the font size */
        font-weight: bold;   /* Make it bold */
       
       
    }
    </style>
    <h2 class="custom-header">Problem Explorer</h2>
    """,
    unsafe_allow_html=True
)
    
    
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
    
    problems = get_problem_metadata()
    
    if difficulty_filter != "All":
        problems = [p for p in problems if p["difficulty"].lower() == difficulty_filter.lower()]
    if category_filter != "All":
        problems = [p for p in problems if p["category"] == category_filter]
    if search:
        problems = [p for p in problems if search.lower() in p["title"].lower()]
    
    render_problems_table(problems)

def render_problems_table(problems):
    """Render the problems in a table format"""
    for idx, problem in enumerate(problems):
        with st.container():
            cols = st.columns([1, 3, 2, 2, 2])
            
            cols[0].write(f"#{problem['id']}")
            cols[1].write(problem["title"])
            
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
            
            cols[3].write(problem["category"])
            
            if cols[4].button("Solve", key=f"solve_{problem['id']}_{idx}"):
                st.session_state["current_problem"] = problem
                st.session_state["page"] = "problem_solver"
            
            st.markdown("---")

def render_solutions_tab(problem_path):
    """Render the solutions tab with solution selection and execution"""
    solutions = get_problem_solutions(problem_path)
    
    if not solutions:
        st.info("No solutions available yet.")
        return
    
    selected_solution = st.selectbox(
        "Select Solution",
        solutions,
        key=f"solution_select_{os.path.basename(problem_path)}"
    )
    
    if selected_solution:
        # Display solution code
        solution_content = load_file_content(os.path.join(problem_path, selected_solution))
        with st.container(height=400):
            st.code(solution_content, language='python')
        
        # Run solution button
        if st.button("Run Solution", key=f"run_solution_{os.path.basename(problem_path)}"):
            with st.spinner("Executing solution..."):
                try:
                    stdout, stderr, locals_dict = st.session_state.code_executor.execute(solution_content)
                    
                    # Display standard output
                    if stdout:
                        st.write("### Output:")
                        st.code(stdout)
                    
                    # Display plots
                    if '_plot_path' in locals_dict:
                        st.write("### Plot Output:")
                        st.image(locals_dict['_plot_path'])
                        os.remove(locals_dict['_plot_path'])
                    
                    # Display variables
                    if locals_dict:
                        st.write("### Variables:")
                        for var_name, var_value in locals_dict.items():
                            if not var_name.startswith('_'):
                                if isinstance(var_value, (pd.DataFrame, pd.Series)):
                                    st.write(f"**{var_name}:**")
                                    st.dataframe(var_value)
                                elif isinstance(var_value, (np.ndarray, list, dict, set)):
                                    st.write(f"**{var_name}:**")
                                    st.write(var_value)
                    
                    # Display errors
                    if stderr:
                        st.error(f"Errors:\n{stderr}")
                except Exception as e:
                    st.error(f"Error executing solution: {str(e)}")

# The CodeExecutor class should also be updated for better error handling
class CodeExecutor:
    def __init__(self):
        self.globals = {
            'np': np,
            'pd': pd,
            'plt': plt,
            'sns': sns,
        }
        self.locals = {}
    
    def execute(self, code: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Execute code and return stdout, stderr, and local variables
        
        Args:
            code (str): Python code to execute
            
        Returns:
            Tuple[str, str, Dict[str, Any]]: (stdout, stderr, local variables)
        """
        stdout = StringIO()
        stderr = StringIO()
        
        try:
            # Clear previous matplotlib plots
            plt.close('all')
            
            # Create new figure if plotting code is present
            if 'plt' in code:
                plt.figure()
            
            # Execute the code
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                exec(code, self.globals, self.locals)
                
                # Handle plots
                if 'plt' in code:
                    fig = plt.gcf()
                    if len(fig.axes) > 0:
                        plt_path = "temp_plot.png"
                        plt.savefig(plt_path)
                        plt.close()
                        self.locals['_plot_path'] = plt_path
        
        except Exception as e:
            stderr.write(f"Error: {str(e)}\n")
            stderr.write(traceback.format_exc())
        
        finally:
            # Clean up matplotlib resources
            plt.close('all')
        
        return stdout.getvalue(), stderr.getvalue(), self.locals

# Update the render_problem_solver function to use the improved components
def render_problem_solver(problem):
    """Render the problem-solving environment."""
    st.markdown(
    f"""
    <style>
    .custom-header {{
        font-size: 20px;  /* Decrease the font size */
        font-weight: bold;
        text-align: center; /* Center the header */
        margin-bottom: 15px; /* Reduce spacing below */
    }}
    </style>
    <div class="custom-header">Problem {problem['id']}: {problem['title']}</div>
    """,
    unsafe_allow_html=True
)
  
    
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
        st.write("#### Code Editor")
        
        # Initialize code executor if needed
        if 'code_executor' not in st.session_state:
            st.session_state.code_executor = CodeExecutor()
        
        # Initialize code template if needed
        if f'code_{problem["id"]}' not in st.session_state:
            st.session_state[f'code_{problem["id"]}'] = """# Your code here
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Write your solution below
"""
        
        # Code editor
        code = st_ace(
            value=st.session_state[f'code_{problem["id"]}'],
            placeholder="Write your solution here...",
            language="python",
            theme="monokai",
            key=f"editor_{problem['id']}",
            height=400
        )
        # code = st.text_area("Write your solution here...", st.session_state[f'code_{problem["id"]}'], height=400)
        st.session_state[f'code_{problem["id"]}'] = code
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Code", key=f"run_{problem['id']}"):
                with st.spinner("Executing code..."):
                    try:
                        stdout, stderr, locals_dict = st.session_state.code_executor.execute(code)
                        
                        if stdout:
                            st.write("### Output:")
                            st.code(stdout)
                        
                        if '_plot_path' in locals_dict:
                            st.write("### Plot Output:")
                            st.image(locals_dict['_plot_path'])
                            os.remove(locals_dict['_plot_path'])
                        
                        if locals_dict:
                            st.write("### Variables:")
                            for var_name, var_value in locals_dict.items():
                                if not var_name.startswith('_'):
                                    if isinstance(var_value, (pd.DataFrame, pd.Series)):
                                        st.write(f"**{var_name}:**")
                                        st.dataframe(var_value)
                                    elif isinstance(var_value, (np.ndarray, list, dict, set)):
                                        st.write(f"**{var_name}:**")
                                        st.write(var_value)
                        
                        if stderr:
                            st.error(f"Errors:\n{stderr}")
                            
                            # Get Gemini AI suggestion for error
                            suggestion = get_gemini_suggestion(stderr)
                            st.write("### Gemini AI Suggestion:")
                            st.info(suggestion)
                    except Exception as e:
                        st.error(f"Error executing code: {str(e)}")
                        
        with col2:
            # ✅ Initialize the session state variable BEFORE using it in a widget
            solution_key = f"solution_name_{problem['id']}"
            if solution_key not in st.session_state:
                st.session_state[solution_key] = f"solution_{len(get_problem_solutions(problem_path)) + 1}.py"

            # ✅ Use the session state variable inside the text input
            solution_name = st.text_input(
                "Save solution as:",
                value=st.session_state[solution_key],  # Set value without modifying session state after widget creation
                key=solution_key  # Uses the same session state key
            )

            if st.button("Save Solution", key=f"save_{problem['id']}"):
                try:
                    save_file_content(
                        os.path.join(problem_path, solution_name),  # Pass directly from the widget
                        code
                    )
                    st.session_state.user_progress.mark_problem_complete(problem['id'])
                    st.success("Solution saved successfully!")
                except Exception as e:
                    st.error(f"Error saving solution: {str(e)}")

    # Solutions Tab
    with tabs[2]:
        render_solutions_tab(problem_path)

def render_daily_challenge():
    "Render the daily challenge"
    st.markdown(
    """
    <style>
    .custom-header {
        font-size: 20px;     /* Adjust the font size */
        font-weight: bold;   /* Make it bold */
        
        margin-bottom: 1px; /* Add space below */
    }
    </style>
    <h2 class="custom-header">Daily Challenge</h2>
    """,
    unsafe_allow_html=True
)
    
    today = date.today()
    problems = get_problem_metadata()
    
    if problems:
        problem_index = today.toordinal() % len(problems)
        problem = problems[problem_index]
        
        st.write(f"##### Problem {problem['id']}: {problem['title']}")
        st.write(f"**Difficulty:** {problem['difficulty'].capitalize()}")
        st.write(f"**Category:** {problem['category']}")
        
        if st.button("Start Challenge", key="start_daily_challenge"):
            st.session_state["current_problem"] = problem
            st.session_state["page"] = "problem_solver"
    else:
        st.warning("No problems available for daily challenge.")

def render_user_profile():
    """Render user profile and statistics"""

    st.write("### Your Profile")
    
    col1, col2, col3 = st.columns(3)
    
    st.markdown(
    """
    <style>
    /* Reduce the font size of metric labels */
    div[data-testid="stMetricLabel"] {
        font-size: 12px !important; /* Adjust label size */
        font-weight: normal;
    }

    /* Reduce the font size of metric values */
    div[data-testid="stMetricValue"] {
        font-size: 16px !important; /* Adjust value size */
        font-weight: bold;
    }

    /* Reduce the font size of delta values (optional) */
    div[data-testid="stMetricDelta"] {
        font-size: 10px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

    # Displaying the metrics in columns
    with col1:
        total_problems = len(get_problem_directories())
        completed = len(st.session_state.user_progress.data["completed_problems"])
        completion_rate = (completed / total_problems * 100) if total_problems > 0 else 0
        st.metric("Completion Rate", f"{completion_rate:.1f}%")

    with col2:
        st.metric("Problems Solved", completed)

    with col3:
        st.metric("Current Streak", f"{st.session_state.user_progress.data['current_streak']} days")
   
    st.markdown(
    """
    <style>
    .progress-calendar-container {
        width: 100%;
        display: flex;
        justify-content: center;
    }
    .progress-calendar {
        width: 300px; /* Fixed table width */
        border-collapse: collapse;
        table-layout: fixed; /* Equal cell width */
        border-spacing: 0px;
        text-align: center;
    }
    .progress-calendar th, .progress-calendar td {
        width: 40px; /* Equal width for all cells */
        height: 40px; /* Fixed height */
        text-align: center;
        border: 2px solid #ddd;
        font-size: 16px;
        font-weight: bold;
        white-space: nowrap; /* Prevents text wrapping */
    }
    .progress-calendar th {
        background-color: #f0f0f0;
    }
    .progress-calendar td {
        background: #fff;
    }
    .completed-day {
        background-color: #4CAF50 !important;
        color: white;
        border-radius: 5px;
    }
    .empty-day {
        background: transparent !important;
        border: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

    st.write("#### 🗓 Progress Calendar")

    today = date.today()
    cal = calendar.monthcalendar(today.year, today.month)

    # Start building the table HTML
    table_html = "<div class='progress-calendar-container'><table class='progress-calendar'>"

    # Weekday headers
    table_html += "<tr>" + "".join(f"<th>{day}</th>" for day in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]) + "</tr>"

    # Rows for each week
    for week in cal:
        table_html += "<tr>"
        for day in week:
            if day == 0:
                table_html += "<td class='empty-day'></td>"  # Empty cell for non-days
            else:
                date_str = f"{today.year}-{today.month:02d}-{day:02d}"
                if date_str in st.session_state.user_progress.data["daily_progress"]:
                    table_html += f"<td class='completed-day'>{day} ✅</td>"  # Mark completed days
                else:
                    table_html += f"<td>{day}</td>"  # Regular day
        table_html += "</tr>"

    table_html += "</table></div>"

    # Render the table
    st.markdown(table_html, unsafe_allow_html=True)

    
    st.write("#### Problem History")
    if completed > 0:
        problems = get_problem_metadata()
        completed_problems = [p for p in problems 
                            if p["id"] in st.session_state.user_progress.data["completed_problems"]]
        
        for problem in completed_problems:
            with st.expander(f"Problem {problem['id']}: {problem['title']}"):
                st.write(f"**Category:** {problem['category']}")
                st.write(f"**Difficulty:** {problem['difficulty'].capitalize()}")
                
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
    st.write("#### Submit a New Problem")
    
    with st.form("problem_submission"):
        st.write("#### Problem Details")
        
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
        
        st.write("#### Problem Content")
        
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
                problem_dir = f"{problem_number}_{problem_title.replace(' ', '_')}"
                problem_path = os.path.join(PROBLEMS_DIR, problem_dir)
                os.makedirs(problem_path, exist_ok=True)
                
                with open(os.path.join(problem_path, 'learn.md'), 'w') as f:
                    f.write(description)
                
                with open(os.path.join(problem_path, 'solution.py'), 'w') as f:
                    f.write(sample_solution)
                
                st.success("Problem submitted successfully!")
                
            except Exception as e:
                st.error(f"Error submitting problem: {str(e)}")

def main():

    setup_page()
   
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "reset_password" in st.session_state and st.session_state["reset_password"]:
        reset_password_page()
        return
    if not st.session_state["authenticated"]:
        login_page()
        return
    
    
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
   
    
    # Sidebar navigation
    with st.sidebar:
        st.title(f"Welcome, {st.session_state['username']}")
        if st.button("Logout"):
            st.session_state["authenticated"] = False
            st.experimental_rerun()
        st.title("Navigation")
        current_nav = st.radio(
            "Go to",
            ["Home", "Problem Explorer", "Daily Challenge", "Profile", "Submit Problem"],
            key="navigation",
            index=["Home", "Problem Explorer", "Daily Challenge", "Profile", "Submit Problem"].index(st.session_state["nav_selection"])
        )
        
        if current_nav != st.session_state["nav_selection"]:
            st.session_state["nav_selection"] = current_nav
            st.session_state["page"] = current_nav.lower().replace(" ", "_")
    
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


                            