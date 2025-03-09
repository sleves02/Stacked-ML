import streamlit as st
import os
import hashlib
import json
from authlib.integrations.requests_client import OAuth2Session

# Constants
USER_CREDENTIALS_FILE = "users.json"

# Function to hash passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Function to load users
def load_users():
    if os.path.exists(USER_CREDENTIALS_FILE):
        with open(USER_CREDENTIALS_FILE, "r") as f:
            return json.load(f)
    return {}

# Function to save users
def save_users(users):
    with open(USER_CREDENTIALS_FILE, "w") as f:
        json.dump(users, f)

# Function to authenticate users
def authenticate(username, password):
    users = load_users()
    if username in users and users[username] == hash_password(password):
        return True
    return False

# Function to register new users
def register(username, password):
    users = load_users()
    if username in users:
        return False, "Username already exists."
    users[username] = hash_password(password)
    save_users(users)
    return True, "Registration successful!"

# Function for password reset
def reset_password(username, new_password):
    users = load_users()
    if username not in users:
        return False, "Username not found."
    users[username] = hash_password(new_password)
    save_users(users)
    return True, "Password reset successful!"



# Login Page
def login_page():
    
    # Apply local CSS for styling
    st.markdown("""
        <style>
        .stTabs [role="tablist"] {
        display: flex;
        justify-content: center; /* Center the tabs */
    }
        /* Center the login container */
                /* Center the login container */
        .login-container {
            width: 40%;  /* Reduced width */
            margin: auto;
            padding: 5px; /* Slightly increased padding for better look */
            background: white;
            border-radius: 10px;
            box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
            margin-bottom: 1px;
        }

        /* Adjust input fields */
        .stTextInput > div {
            width: 80% !important;  /* Reduce width of input fields */
            max-width: 300px;  /* Slightly reduce max width */
            margin: auto;
            margin-bottom: 1px;
        }

        /* Center labels and reduce font size */
        label, .stMarkdown {
            display: block;
            text-align: center;
            font-size: 12px; /* Decreased text size */
            margin-bottom: 1px !important; /* Reduce space below label */
        }

        /* Center buttons */
        .stButton > button {
            width: 80% !important;
            max-width: 200px;
            margin: 5px auto;
            display: block;
        }

        </style>
    """, unsafe_allow_html=True)

    
    
    st.title("Login")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        st.markdown("Username")
        username = st.text_input("", key="login_username")  # Empty label to use custom styling
        st.markdown("Password")
        password = st.text_input("", type="password", key="login_password")

        col1, col2, col3 = st.columns([1, 2, 1])  # Center-align the button
        with col2:
            if st.button("Login"):
                if authenticate(username, password):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username
                    st.success("Login successful! Redirecting...")
                    st.experimental_rerun()
                else:
                    st.error("Invalid username or password.")
                    
        

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Forgot Password?"):
                st.session_state["reset_password"] = True
                st.experimental_rerun()

    with tab2:
        st.markdown("New Username")
        new_username = st.text_input("", key="register_username")
        st.markdown("New Password")
        new_password = st.text_input("", type="password", key="register_password")

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Register"):
                success, message = register(new_username, new_password)
                if success:
                    st.success(message)
                else:
                    st.error(message)

    st.markdown('</div>', unsafe_allow_html=True)

    
# Password Reset Page
def reset_password_page():
    st.title("Reset Password")
    username = st.text_input("Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Reset Password"):
        success, message = reset_password(username, new_password)
        if success:
            st.success(message)
            del st.session_state["reset_password"]
            st.experimental_rerun()
        else:
            st.error(message)

def load_css():
    with open("styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Main App
# Main App
def main():
    # Load CSS first
    

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    
    if "reset_password" in st.session_state and st.session_state["reset_password"]:
        reset_password_page()
        return
    
    if not st.session_state["authenticated"]:
        login_page()
        return
    
    st.sidebar.title(f"Welcome, {st.session_state['username']}")
    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.experimental_rerun()
    
    st.title("Problem Solving Platform")
    st.write("Your problem-solving interface remains here...")



if __name__ == "__main__":
    main()
