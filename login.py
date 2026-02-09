import streamlit as st
import urllib.parse
import re
from sqlalchemy import create_engine, text as sql_text # Renamed to avoid conflicts

# --- DATABASE SETUP ---
DB_USER = "project"
DB_PASSWORD = "project123" 
DB_HOST = "192.168.5.8"
DB_PORT = "3306"
DB_NAME = "Newproj"
USER_TABLE = "login"

password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# --- VALIDATION FUNCTIONS ---
def is_valid_input(user_input):
    pattern = r'^([a-zA-Z][a-zA-Z\s]*|[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})$'
    return bool(re.match(pattern, user_input))

# --- AUTHENTICATION FUNCTIONS ---
def authenticate(identifier, user_password):
    try:
        with engine.connect() as conn:
            # ✅ Fixed: Changed 'text' to 'sql_text' to avoid string conflict
            query = sql_text(f"SELECT * FROM {USER_TABLE} WHERE (email = :identifier OR name = :identifier) AND password = :password")
            result = conn.execute(query, {
                "identifier": identifier,
                "password": user_password
            }).fetchone()
            return result
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return None

# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- UI LOGIC ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Login", page_icon="🔐", layout="centered")
    
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col2:
        st.title("🔐 User Login")
        # ✅ Fixed: Renamed variable from 'text' to 'user_id'
        user_id = st.text_input("Name or Email", key="login_user")
        user_pass = st.text_input("Password", type="password", key="login_pass")
        
        btn_col1, btn_col2, _ = st.columns([1, 1, 2])
        
        with btn_col1:
            login_clicked = st.button("Log In", use_container_width=True)
        with btn_col2:
            signup_clicked = st.button("SignUp", use_container_width=True)
        
        if st.button("Forgot Password?"):
            st.switch_page("pages/reset.py")

        # Logic for Log In
        if login_clicked:
            if not user_id or not user_pass:
                st.warning("Please enter both credentials.")
            elif authenticate(user_id, user_pass):
                st.session_state.logged_in = True
                st.session_state.user_email = user_id
                st.success("Login Successful!")
                st.switch_page("pages/app.py")
            else:
                st.error("Invalid credentials.")
        
        # Logic for Sign Up
        if signup_clicked:
            st.switch_page("pages/signup.py")