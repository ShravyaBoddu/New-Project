import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- Database Setup ---
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# 1. Safety Check: Ensure we have data to edit
if "target_user" not in st.session_state or "target_file" not in st.session_state:
    st.warning("No file selected for editing. Please return to the registry.")
    if st.button("Return to Registry"):
        st.switch_page("pages/login.py")
    st.stop()

user = st.session_state.target_user
file = st.session_state.target_file

# 2. Top Navigation Bar
nav_col, back_col, logout_col = st.columns([5, 1, 1])
with back_col:
    if st.button("⬅️ Back"):
        # Clear the cached data when leaving so the next file loads fresh
        if "editor_df" in st.session_state:
            del st.session_state.editor_df
        st.switch_page("pages/user.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.title(" Edit Record Data")
st.info(f"📁 **File:** {file} | 👤 **Owner:** {user}")

# --- 3. PERSISTENT DATA LOADING ---
# This block ensures we only fetch from the DB ONCE. 
# After that, we use the version stored in the browser's session memory.
if "editor_df" not in st.session_state:
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM data WHERE uploaded_by = :u AND filename = :f")
            # Load from DB and store in Session State
            st.session_state.editor_df = pd.read_sql(query, con=conn, params={"u": user, "f": file})
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# 4. The Editor
# We point the editor to the Session State dataframe.
edited_df = st.data_editor(
    st.session_state.editor_df, 
    use_container_width=True, 
    num_rows="dynamic",
    key="data_editor_key"
)
if 'show_success' not in st.session_state:
    st.session_state.show_success = False

# 5. Save Logic
if st.button("💾 Save Changes"):
    try:
        # Update our session state with the newest edits before saving
        final_df = edited_df.copy()
        final_df['uploaded_by'] = user
        final_df['filename'] = file

        with engine.begin() as conn:
            # Delete old entries
            conn.execute(
                text("DELETE FROM data WHERE uploaded_by = :u AND filename = :f"), 
                {"u": user, "f": file}
            )
            # Insert updated entries
            final_df.to_sql("data", con=conn, if_exists="append", index=False)
        
        # Update the session state so the UI reflects the saved state
        st.session_state.editor_df = edited_df
        st.session_state.show_success = True
        st.rerun()

    except Exception as e:
        st.error(f" Error saving data: {e}")
if st.session_state.show_success:
    st.success("Changes saved successfully to the database!")
    # Optionally reset the flag after showing it, or use time.sleep
    st.session_state.show_success = False

