import streamlit as st
import pandas as  pd 
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Database Setup ---
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

# --- 2. Database Helper Functions for Permissions ---
def update_db_permission(perm_id, status):
    """Saves the YES/NO choice to the database."""
    with engine.begin() as conn:
        query = text("""
            INSERT INTO file_permissions (perm_id, permission_status) 
            VALUES (:id, :status) 
            ON DUPLICATE KEY UPDATE permission_status = :status
        """)
        conn.execute(query, {"id": perm_id, "status": status})

def get_all_permissions():
    """Fetches all saved permissions from the database."""
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT perm_id, permission_status FROM file_permissions"))
            return {row[0]: row[1] for row in res.fetchall()}
    except Exception:
        return {}

# Initialize session state with database values
if "permissions_map" not in st.session_state:
    st.session_state.permissions_map = get_all_permissions()

st.set_page_config(page_title="File Upload History", layout="wide")

# --- 3. Navigation ---
nav_col, home_col, logout_col = st.columns([5, 1, 1])
with home_col:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with logout_col:
    if st.button("Logout"):
        # Now we CAN safely clear everything because permissions are in the DB!
        st.session_state.clear()
        st.switch_page("login.py")

st.title("📁 File Upload History")

# --- 4. Data Loading ---
@st.cache_data(ttl=300)
def load_file_history():
    try:
        with engine.connect() as conn:
            query = text("SELECT uploaded_by, filename, COUNT(*) as records FROM data GROUP BY uploaded_by, filename")
            return pd.read_sql(query, con=conn)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_file_history()

if df.empty:
    st.warning("No data found in the database.")
else:
    # Header row
    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 2])
    col1.markdown("**User Email**")
    col2.markdown("**Filename**")
    col3.markdown("**Rows**")
    col4.markdown("**Edit**")
    col5.markdown("**Delete**")
    col6.markdown("**Grant Permission**")

    st.divider()

    # Data rows
    for idx, row in df.iterrows():
        fname = row['filename']
        user_email = row['uploaded_by']
        perm_id = f"{user_email}_{fname}"
        
        # Get current status from session state (synced with DB)
        # Default to "NO" if not found in DB
        current_status = st.session_state.permissions_map.get(perm_id, "NO")

        with st.container():
            c1, c2, c3, c4, c5, c6 = st.columns([2, 2, 1, 1, 1, 2])
            
            c1.write(user_email)
            c2.write(fname or "Unknown")
            c3.write(f"{int(row['records']):,}")
            
            with c4:
                if st.button("Edit", key=f"edit_{idx}"):
                    if current_status == "YES":
                        st.session_state.target_user = user_email
                        st.session_state.target_file = fname
                        st.switch_page("pages/edit.py")
                    else:
                        st.error("Access Denied")

            with c5:
                if st.button("Delete", key=f"del_{idx}"):
                    st.toast(f"Delete requested for {fname}")

            with c6:
                perm_col1, perm_col2 = st.columns(2)
                
                if perm_col1.button("✅ Yes", key=f"yes_{idx}", use_container_width=True):
                    st.session_state.permissions_map[perm_id] = "YES"
                    update_db_permission(perm_id, "YES") # PERMANENT SAVE
                    st.rerun()
                    
                if perm_col2.button("No", key=f"no_{idx}", use_container_width=True):
                    st.session_state.permissions_map[perm_id] = "NO"
                    update_db_permission(perm_id, "NO") # PERMANENT SAVE
                    st.rerun()
                
                status_color = "green" if current_status == "YES" else "red"
                st.markdown(f"Status: :{status_color}[**{current_status}**]")

    st.divider()