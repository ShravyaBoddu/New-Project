import streamlit as st
import urllib.parse
import re  # Added for regex validation
from sqlalchemy import create_engine, text

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
def is_valid_email(email):
    # Standard email regex pattern
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def is_valid_password(password):
    # Rules: 5+ chars, 1 capital, 1 number, 1 special char
    if len(password) < 5:
        return False, "Password must be at least 5 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one capital letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+=\-_/]', password):
        return False, "Password must contain at least one special character."
    return True, ""

# --- AUTHENTICATION FUNCTIONS ---
def authenticate(email, password):
    try:
        with engine.connect() as conn:
            query = text(f"SELECT * FROM {USER_TABLE} WHERE email = :email AND password = :password")
            result = conn.execute(query, {"email": email, "password": password}).fetchone()
            return result
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return None



# --- SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# --- UI LOGIC ---
if not st.session_state.logged_in:
    st.set_page_config(page_title="Login", page_icon="🔐",layout="centered")
    
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col2:
        st.title("🔐 User Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        btn_col1, btn_col2, _ = st.columns([1, 1, 2])
        
        with btn_col1:
            login_clicked = st.button("Log In", use_container_width=True)
        with btn_col2:
            signup_clicked = st.button("SignUp", use_container_width=True)
        
        if st.button("Forgot Password?"):
         st.switch_page("pages/reset.py")

        # Logic for Log In
        if login_clicked:
            
            if authenticate(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.switch_page("pages/app.py")
            else:
                st.error("Invalid credentials.")
        
        # Logic for Sign Up with Validations
        if signup_clicked:
            st.switch_page("pages/signup.py")

