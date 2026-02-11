import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Database Connection ---
@st.cache_resource
def get_engine():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = get_engine()

# --- 2. Database Functions ---
def check_admin_permission(email):
    """Checks the permission status for the user email."""
    try:
        with engine.connect() as conn:
            query = text("SELECT permission_status FROM file_permissions WHERE perm_id = :id")
            result = conn.execute(query, {"id": email}).fetchone()
            return result[0] if result else "NO"
    except Exception:
        return "NO"

def delete_file_record(email, filename):
    """Deletes all records of a file for the specific user."""
    try:
        with engine.begin() as conn:
            query = text("DELETE FROM data WHERE uploaded_by = :email AND filename = :filename")
            conn.execute(query, {"email": email, "filename": filename})
        st.success(f"Successfully deleted {filename}")
        # Clear cache to force a fresh data fetch
        st.cache_data.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Delete failed: {e}")

# --- 3. Session Handling ---
if 'user_email' not in st.session_state:
    st.switch_page("login.py")
    st.stop()

current_user_email = st.session_state['user_email']

# --- Navigation ---
col_head, col_back, col_logout = st.columns([5, 1, 1])
with col_back:
    if st.button("⬅️ Back"): st.switch_page("pages/app.py")
with col_logout:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.header("👤 My Account")
st.info(f"Logged in as: **{current_user_email}**")

# --- 4. Fetch Data ---
@st.cache_data(ttl=2)
def fetch_user_data(email):
    with engine.connect() as conn:
        query = text("SELECT filename, COUNT(*) as total_rows FROM data WHERE uploaded_by = :email GROUP BY filename")
        return pd.read_sql(query, con=conn, params={"email": email})

df = fetch_user_data(current_user_email)
allowed_status = check_admin_permission(current_user_email)

# --- 5. UI Layout ---
if df.empty:
    st.warning("No files found.")
else:
    # Header Row
    st.divider()
    h1, h2, h3, h4, h5 = st.columns([3, 1.5, 1.5, 1, 1.5])
    h1.write("**Filename**")
    h2.write("**Total Rows**")
    h3.write("**Access**")
    h4.write("**Edit**")
    h5.write("**Delete**")
    st.divider()

    for idx, row in df.iterrows():
        fname = row['filename']
        
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1.5, 1, 1.5])
            
            c1.write(fname)
            c2.write(str(row['total_rows']))
            
            # PERMISSION & EDIT LOGIC
            if allowed_status == "YES":
                c3.success("Granted")
                if c4.button("Edit", key=f"edit_{idx}", help="Edit this file"):
                    st.session_state['editing_file'] = fname
                    st.switch_page("pages/edit_acc.py")
            else:
                c3.error("Locked")
                c4.button("🔒", key=f"edit_locked_{idx}", disabled=True)

            # DELETE LOGIC (using a Popover for safe confirmation)
            with c5:
                with st.popover("🗑️ Delete"):
                    st.write("Are you sure?")
                    if st.button("Confirm", key=f"confirm_del_{idx}"):
                        delete_file_record(current_user_email, fname)

st.divider()