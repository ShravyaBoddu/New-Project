import streamlit as st
import urllib.parse
import re
from sqlalchemy import create_engine, text
import streamlit as st

# --- DATABASE SETUP (Same as login.py) ---
DB_USER = "project"
DB_PASSWORD = "project123" 
DB_HOST = "192.168.5.8"
DB_PORT = "3306"
DB_NAME = "Newproj"
USER_TABLE = "login"

password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email)

def is_valid_password(password):
    if len(password) < 5:
        return False, "Password must be at least 5 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one capital letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+=\-_/]', password):
        return False, "Password must contain at least one special character."
    return True, ""

def save_new_user(email, password):
    try:
        with engine.connect() as conn:
            query = text(f"INSERT INTO {USER_TABLE} (email, password) VALUES (:email, :password)")
            conn.execute(query, {"email": email, "password": password})
            conn.commit()
            return True
    except Exception as e:
        st.error(f"❌ Error: Account creation failed (User might already exist).")
        return False

st.set_page_config(page_title="Create New User", layout="centered")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

st.title("Create New User")
st.markdown("---")

# Email input
email = st.text_input("Enter email", placeholder="example@email.com")

# Password inputs
password = st.text_input("Enter Password", type="password")

col1, col2 = st.columns([1, 1])

with col1:
    submit_clicked = st.button("Submit", use_container_width=True)

with col2:
    Back_clicked = st.button("Back", use_container_width=True)

@st.dialog("Account created Successfully")
def show_success_dialog():
    st.write("Your account has been created. You can now log in with your new account.")
    if st.button("Go to Login"):
        st.switch_page("login.py")
if submit_clicked:
            if not email or not password:
                st.warning("Please fill both fields.")
            elif not is_valid_email(email):
                st.error("Please enter a valid email address (e.g., name@example.com).")
            else:
                is_pass_valid, error_msg = is_valid_password(password)
                if not is_pass_valid:
                    st.error(error_msg)
                else:
                    if save_new_user(email, password):
                        show_success_dialog()
if Back_clicked:
    try:
        st.switch_page("login.py")
    except Exception:
        st.error("login.py not found in the directory.")
