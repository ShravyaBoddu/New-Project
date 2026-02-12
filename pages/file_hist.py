import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Database Setup ---
@st.cache_resource
def init_db():
    # Credentials
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    # Using pymysql as the driver
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

# --- 2. Permission Helper ---
def get_all_permissions():
    """Fetches all saved permissions from the database to sync with session state."""
    try:
        with engine.connect() as conn:
            res = conn.execute(text("SELECT perm_id, permission_status FROM file_permissions"))
            # Normalizing keys to lowercase and stripped to avoid matching errors
            return {str(row[0]).strip(): str(row[1]).strip().upper() for row in res.fetchall()}
    except Exception as e:
        st.sidebar.error(f"Permission Sync Error: {e}")
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
        st.session_state.clear()
        st.switch_page("login.py")

st.title("📁 File Upload History")

# --- 4. Data Loading ---
@st.cache_data(ttl=300)
def load_file_history():
    try:
        with engine.connect() as conn:
            query = text("SELECT filename, uploaded_by, COUNT(*) as records FROM data GROUP BY uploaded_by, filename")
            return pd.read_sql(query, con=conn)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_file_history()

# --- 5. Display Logic ---
if df.empty:
    st.warning("No data found in the database.")
else:
    # Header
    h1, h2, h3, h4, h5 = st.columns([3, 3, 1, 1, 1])
    h1.markdown("**User Email**")
    h2.markdown("**Filename**")
    h3.markdown("**Rows**")
    h4.markdown("**Edit**")
    h5.markdown("**Delete**")
    st.divider()

    # Data rows
    for idx, row in df.iterrows():
        target_file = str(row['filename']).strip()
        target_user = str(row['uploaded_by']).strip()
        
        # Construct perm_id exactly as it exists in your file_permissions table
        perm_id = f"{target_user}_{target_file}"
        
        # Get status from session state (defaults to "NO")
        current_status = st.session_state.permissions_map.get(perm_id, "NO")

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 3, 1, 1, 1])

            c1.write(target_user)
            c2.write(target_file if target_file else "Unknown")
            c3.write(f"{int(row['records']):,}")

            # --- Edit Button Logic ---
            with c4:
                if st.button("Edit", key=f"edit_{idx}"):
                    st.session_state["target_file"] = target_file
                    st.session_state["target_user"] = target_user
                    st.switch_page("pages/file_edit.py")
                

            # --- Delete Button Logic ---
            with c5:
                if st.button("Delete", key=f"del_{idx}"):
                    try:
                        with engine.begin() as conn:
                            # Delete records
                            delete_data = text("DELETE FROM data WHERE uploaded_by = :u AND filename = :f")
                            conn.execute(delete_data, {"u": target_user, "f": target_file})
                        
                        st.success(f"Deleted {target_file}")
                        st.cache_data.clear()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete failed: {e}")

    st.divider()