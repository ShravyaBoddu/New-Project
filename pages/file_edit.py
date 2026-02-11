import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Database Connection ---
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

st.set_page_config(page_title="Edit File Records", layout="wide")
col1,col2,col3= st.columns([5,1,1])
with col2:
    if st.button("Back"):
        st.switch_page("pages/file_hist.py")
with col3:
    if st.button("Logout"):
        st.switch_page("login.py")

# --- 2. Check for Session State ---
# If someone tries to access this page directly without clicking 'Edit'
if "target_file" not in st.session_state or "target_user" not in st.session_state:
    st.error("No file selected for editing.")
    if st.button("Go Back"):
        st.switch_page("pages/file_hist.py") # Adjust to your main page filename
    st.stop()

target_file = st.session_state["target_file"]
target_user = st.session_state["target_user"]

st.title(f"✏️ Editing: {target_file}")
st.caption(f"Uploaded by: {target_user}")

# --- 3. Fetch Data for this specific file ---
def get_file_data(filename, user):
    query = text("SELECT * FROM data WHERE uploaded_by = :u AND filename = :f")
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"u": user, "f": filename})

# We don't cache this because we need to see fresh changes
df_to_edit = get_file_data(target_file, target_user)

if df_to_edit.empty:
    st.warning("No records found for this file.")
else:
    # --- 4. Streamlit Data Editor ---
    st.info("Double-click cells to edit values. Click 'Save Changes' below to update the database.")
    
    # We exclude 'id' or 'uploaded_by' from being edited if they are primary keys/metadata
    edited_df = st.data_editor(
    df_to_edit,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True,
    disabled=["uploaded_by", "filename"]
)

    # --- 5. Save Logic ---
    col1, col2 = st.columns([1, 5])
    
    with col1:
        if st.button("💾 Save Changes", type="primary"):
            try:
                with engine.begin() as conn:
                    # Strategy: Delete old records and insert new edited ones
                    # This is often cleaner for "file-based" bulk edits than individual UPDATE statements
                    delete_query = text("DELETE FROM data WHERE uploaded_by = :u AND filename = :f")
                    conn.execute(delete_query, {"u": target_user, "f": target_file})
                    
                    # Insert the edited dataframe back to SQL
                    edited_df.to_sql("data", con=conn, if_exists="append", index=False)
                    
                st.success("Database updated successfully!")
            except Exception as e:
                st.error(f"Error saving changes: {e}")

    