import streamlit as st
import urllib.parse
import re
from sqlalchemy import create_engine, text

# --- DATABASE SETUP ---
DB_USER = "project"
DB_PASSWORD = "project123" 
DB_HOST = "192.168.5.8"
DB_PORT = "3306"
DB_NAME = "Newproj"
USER_TABLE = "login"

password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)


def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_password(password):
    if len(password) < 5:
        return False, "Password must be at least 5 characters long."
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one capital letter."
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number."
    if not re.search(r'[!@#$%^&*(),.?":{}|<>+=\\-_/]', password):
        return False, "Password must contain at least one special character."
    return True, ""


# ---------- UPDATED (role added) ----------
def save_new_user(name, email, password, role):
    try:
        with engine.connect() as conn:
            query = text(f"""
                INSERT INTO {USER_TABLE} (name, email, password, role)
                VALUES (:name, :email, :password, :role)
            """)

            conn.execute(query, {
                "name": name,
                "email": email,
                "password": password,
                "role": role
            })

            conn.commit()
            return True
    except Exception:
        st.error("❌ Account creation failed. The email might already be registered.")
        return False


# --- UI CONFIGURATION ---
st.set_page_config(page_title="Create New User", layout="centered")

st.title("Create New User")
st.markdown("---")

name = st.text_input("Enter Name", placeholder="John Doe")
email = st.text_input("Enter Email", placeholder="example@email.com")
password = st.text_input("Enter Password", type="password")

# ---------- UPDATED (role selector) ----------
role = st.radio("Select Account Type", ["User", "Admin"])


col1, col2 = st.columns([1, 1])

with col1:
    submit_clicked = st.button("Submit", use_container_width=True)

with col2:
    back_clicked = st.button("Back", use_container_width=True)


@st.dialog("Account Created Successfully")
def show_success_dialog():
    st.write("Your account has been created. You can now log in with your new account.")
    if st.button("OK"):
        st.switch_page("pages/user_info.py")


@st.dialog("Admin Created Successfully")
def show_admin_dialog():
    st.write("Admin account has been created. You can now log in with your new account.")
    if st.button("OK"):
        st.switch_page("pages/user_info.py")


# ---------- LOGIC ----------
if submit_clicked:
    if not name or not email or not password:
        st.warning("Please fill in all three fields.")

    elif not is_valid_email(email):
        st.error("Please enter a valid email address.")

    else:
        is_pass_valid, error_msg = is_valid_password(password)

        if not is_pass_valid:
            st.error(error_msg)

        else:
            db_role = "admin" if role == "Admin" else "user"

            if save_new_user(name, email, password, db_role):
                if db_role == "admin":
                    show_admin_dialog()
                else:
                    show_success_dialog()


if back_clicked:
    try:
        st.switch_page("pages/user_info.py")
    except Exception:
        st.error("not found in the directory.")
