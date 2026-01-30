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

# --- VALIDATION FUNCTIONS ---
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

# --- RESET PASSWORD FUNCTION ---
def reset_password(email, new_password):
    """Reset password for existing user"""
    try:
        with engine.connect() as conn:
            # Validate new password first
            is_valid, msg = is_valid_password(new_password)
            if not is_valid:
                return False, msg
            
            # Update password in database
            query = text(f"UPDATE {USER_TABLE} SET password = :new_password WHERE email = :email")
            result = conn.execute(query, {"new_password": new_password, "email": email})
            conn.commit()
            
            if result.rowcount > 0:
                return True, "✅ Password reset successfully! You can now login."
            else:
                return False, "❌ Email not found. Please create an account first."
                
    except Exception as e:
        return False, f"❌ Database error: {e}"

# --- PAGE CONFIG ---
st.set_page_config(page_title="Reset Password", layout="centered")

# --- SESSION STATE ---
if 'reset_success' not in st.session_state:
    st.session_state.reset_success = False

# --- MAIN UI ---
st.title("Reset Password")
st.markdown("---")

# Email input
email = st.text_input("Enter your registered email", placeholder="example@email.com")

# Password inputs
new_password = st.text_input("New Password", type="password")
confirm_password = st.text_input(" Confirm New Password", type="password")



# Buttons
col1, col2 = st.columns([1, 1])

with col1:
    reset_clicked = st.button("Reset Password", use_container_width=True)

with col2:
    back_clicked = st.button("Back", use_container_width=True)

# --- RESET LOGIC ---
if reset_clicked:
    if not email or not new_password or not confirm_password:
        st.error("Please fill all fields.")
    elif not is_valid_email(email):
        st.error("Please enter a valid email address!")
    elif new_password != confirm_password:
        st.error("Passwords do not match!")
    else:
        success, message = reset_password(email, new_password)
        if success:
            st.success(message)
            st.session_state.reset_success = True
            st.success("Password Reset Complete")
           
        else:
            st.error(message)

# --- CANCEL BUTTON LOGIC ---
if back_clicked:
    st.switch_page("login.py")



    


