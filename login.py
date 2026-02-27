import streamlit as st
import urllib.parse
import re
from sqlalchemy import create_engine, text as sql_text

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
        user_id = st.text_input("Email ", key="login_user")
        user_pass = st.text_input("Password", type="password", key="login_pass")
        
        btn_col1, btn_col2, _ = st.columns([1, 3, 2])
        
        with btn_col1:
            login_clicked = st.button("Log In", key="login_btn", use_container_width=True)
        
        with btn_col2:
            forgot_clicked = st.button("Forgot Password?", key="forgot_btn", use_container_width=False)
        
        # Fixed: Proper if-condition for forgot password button
        if forgot_clicked:
            st.switch_page("pages/reset.py")
        
        # Logic for Log In
        if login_clicked:
            if not user_id or not user_pass:
                st.warning("⚠️ Please enter both credentials.")
            elif not is_valid_input(user_id):
                st.error("❌ Invalid email/username format.")
            elif authenticate(user_id, user_pass):
                st.session_state.logged_in = True
                st.session_state.user_email = user_id
                st.success("✅ Login Successful!")
                st.switch_page("pages/app.py")
            else:
                st.error("❌ Invalid credentials.")
st.markdown("""
<style>
    /* Style for BOTH buttons */
    div[data-testid="stButton"] button {
        background-color: transparent !important;
        color: black !important;
        border: 1px solid black !important;
        border-radius: 8px !important;
        box-shadow: none !important;
        transition: none !important;
    }

    

</style>
""", unsafe_allow_html=True)

# Footer (moved outside conditional for always-visible display)
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; font-size: 14px; padding: 20px 0;'>
        <p>© 2026 RIGHT SIDE BUSINESS SOLUTIONS PRIVATE LIMITED</p>
    </div>
    """,
    unsafe_allow_html=True
)
