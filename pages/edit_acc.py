import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

st.set_page_config(page_title="Edit Record Data", layout="wide")

# --- 1. Database Setup ---
@st.cache_resource
def get_engine():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = get_engine()

# --- 2. Safety Check (THE TROUBLE AREA) ---
# Check if the keys exist AND are not None
target_user = st.session_state.get("target_user")
target_file = st.session_state.get("target_file")

if not target_user or not target_file:
    st.error(" No file selection detected in session memory.")
    
    if st.button("Return to File History"):
        st.switch_page("pages/file_hist.py")
    st.stop()

# --- 3. Navigation ---
nav_col, back_col, logout_col = st.columns([5, 1, 1])
with back_col:
    if st.button("⬅️ Back"):
        st.session_state.pop("editor_df", None)
        st.switch_page("pages/file_hist.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.title("📝 Edit Record Data")
st.info(f"📁 **File:** {target_file} | 👤 **Owner:** {target_user}")

# --- 4. Data Loading ---
if "editor_df" not in st.session_state:
    try:
        with engine.connect() as conn:
            query = text("SELECT * FROM `data` WHERE uploaded_by = :u AND filename = :f")
            df = pd.read_sql(query, con=conn, params={"u": target_user, "f": target_file})
            
            if df.empty:
                st.warning("The database returned no rows for this file.")
                st.session_state.editor_df = df
            else:
                st.session_state.editor_df = df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

# --- 5. The Editor ---
# We use a container to keep things tidy
with st.container():
    edited_df = st.data_editor(
        st.session_state.editor_df,
        use_container_width=True,
        num_rows="dynamic",
        key="editor_instance"
    )

# --- 6. Save Logic ---
if st.button("💾 Save Changes", type="primary"):
    try:
        final_df = edited_df.copy()
        final_df["uploaded_by"] = target_user
        final_df["filename"] = target_file

        # Clean up auto-increment columns if they exist
        if "id" in final_df.columns:
            final_df = final_df.drop(columns=["id"])

        with engine.begin() as conn:
            # Delete old version
            conn.execute(
                text("DELETE FROM `data` WHERE uploaded_by = :u AND filename = :f"),
                {"u": target_user, "f": target_file}
            )
            # Insert new version
            final_df.to_sql("data", con=conn, if_exists="append", index=False)
        
        st.session_state.editor_df = edited_df
        st.toast("Database updated successfully!", icon="✅")
    except Exception as e:
        st.error(f"Error saving data: {e}")