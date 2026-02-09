import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Persistent Database Connection ---
@st.cache_resource
def get_engine():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = get_engine()

# --- 2. Permission Helper (FETCH FROM DB) ---
def get_file_permission(email, filename):
    """Checks the database for the specific permission status."""
    perm_id = f"{email}_{filename}"
    try:
        with engine.connect() as conn:
            query = text("SELECT permission_status FROM file_permissions WHERE perm_id = :id")
            result = conn.execute(query, {"id": perm_id}).fetchone()
            return result[0] if result else "NO"
    except Exception:
        return "NO"

# --- 3. Robust Session Handling ---
if 'user_email' not in st.session_state:
    st.warning("Please log in to access your account.")
    if st.button("Go to Login"):
        st.switch_page("login.py")
    st.stop()

current_user_email = st.session_state['user_email']

# --- Navigation Header ---
nav_col, home_col, logout_col = st.columns([5, 1, 1])
with home_col:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.header("👤 My Account")
st.write(f"Logged in as: **{current_user_email}**")

# --- 4. Cached Data Fetching ---
@st.cache_data(ttl=60) # Reduced TTL to see permission changes faster
def fetch_user_data(email):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT filename, COUNT(*) as total_rows
                FROM data 
                WHERE uploaded_by = :email
                GROUP BY filename
            """)
            df = pd.read_sql(query, con=conn, params={"email": email})
        return df
    except Exception as e:
        st.error(f"❌ Database error: {e}")
        return pd.DataFrame()

# --- 5. Display Logic ---
df = fetch_user_data(current_user_email)

if df.empty:
    st.info("No upload history found for this account.")
else:
    c1, c2 = st.columns(2)
    c1.metric("Files Uploaded", len(df))
    c2.metric("Total Rows", df['total_rows'].sum())
    
    st.divider()
    
    # Header
    h1, h2, h3, h4 = st.columns([3, 2, 1, 1])
    h1.subheader("Filename")
    h2.subheader("Rows")
    h3.subheader("Status")
    h4.subheader("Action")

    for idx, row in df.iterrows():
        fname = row['filename']
        # FETCH PERMISSION FOR THIS SPECIFIC FILE
        allowed = get_file_permission(current_user_email, fname)
        
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
            
            col1.write(fname)
            col2.write(str(row['total_rows']))
            
            # Show Status Indicator
            if allowed == "YES":
                col3.success("Granted")
            else:
                col3.error("Not Granted")
            
            # Edit Button Logic
            if col4.button("Edit", key=f"edit_{idx}"):
                if allowed == "YES":
                    st.session_state['target_file'] = fname
                    st.session_state['target_user'] = current_user_email
                    st.switch_page("pages/edit.py")
                else:
                    st.error("Access Denied: Admin has not granted permission.")

    st.divider()