import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse


# --- 1. Guard‑rail fix: Move this AFTER page setup ---
# This was preventing navigation to edit.py every time the page loaded
if st.session_state.get('target_user') and st.session_state.get('target_file'):
    # Only comment this line out while debugging; it may send you into a loop otherwise.
    # st.switch_page("pages/edit.py")
    pass  # Remove or conditionally keep this.

# --- 1. Database Setup ---
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


engine = init_db()


# --- 2. Permission Helper ---
def get_all_permissions():
    """Fetches all saved permissions from the database to sync with session state."""
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


# --- 5. Display Logic ---
if df.empty:
    st.warning("No data found in the database.")
else:
    # Email | Filename | Rows | Edit Button | Delete Button
    col1, col2, col3, col4, col5 = st.columns([3, 3, 1, 1, 1])
    col1.markdown("**User Email**")
    col2.markdown("**Filename**")
    col3.markdown("**Rows**")
    col4.markdown("**Edit**")
    col5.markdown("**Delete**")

    st.divider()

    # Data rows
    for idx, row in df.iterrows():
        fname = row['filename']
        user_email = row['uploaded_by']
        perm_id = f"{str(user_email).strip()}_{str(fname).strip()}"
        

        current_status = st.session_state.permissions_map.get(perm_id, "NO")

        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 3, 1, 1, 1])

            c1.write(user_email)
            c2.write(fname or "Unknown")
            c3.write(f"{int(row['records']):,}")

            # --- Edit Button Logic ---
            with c4:
               if st.button("Edit", key=f"edit_{idx}"):
        # Normalize the string: remove spaces and make uppercase
        # We also handle potential None/Null values with 'str()'
                  
                     
                 if str(current_status).strip().upper() == "YES":
        # CRITICAL: Set these BEFORE switching
                  st.session_state["target_user"] = user_email 
                  st.session_state["target_file"] = fname
                 
                 st.switch_page("pages/file_edit.py")
                  

            # --- Delete Button Logic ---
            with c5:
                if st.button("Delete", key=f"del_{idx}"):
                    try:
                        with engine.begin() as conn:
                            # Delete all records with this file and user
                            delete_data = text("DELETE FROM data WHERE uploaded_by = :u AND filename = :f")
                            conn.execute(delete_data, {"u": user_email, "f": fname})

                            # Optionally, clean permission if you want
                            # delete_perm = text("DELETE FROM file_permissions WHERE perm_id = :pid")
                            # conn.execute(delete_perm, {"pid": perm_id})

                        st.success(f"File '{fname}' deleted from database.")
                        # Clear cached history so list updates
                        load_file_history.clear()
                    except Exception as e:
                        st.error(f"Failed to delete file: {e}")

    st.divider()
