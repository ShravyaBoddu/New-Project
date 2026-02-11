import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- 1. Database Connection ---
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(
        f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

engine = init_db()

st.set_page_config(page_title="Edit File Records", layout="wide")

col1, col2, col3 = st.columns([5, 1, 1])

with col2:
    if st.button("Back"):
        st.switch_page("pages/acc.py")

with col3:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

# --- 2. Check session values ---
if "target_file" not in st.session_state or "target_user" not in st.session_state:
    st.error("No file selected for editing.")
    if st.button("Go Back"):
        st.switch_page("pages/acc.py")
    st.stop()

target_file = st.session_state["target_file"]
target_user = st.session_state["target_user"]

st.title(f"✏️ Editing: {target_file}")
st.caption(f"Uploaded by: {target_user}")

# --- 3. Fetch data ---
def get_file_data(filename, user):
    query = text("""
        SELECT *
        FROM data
        WHERE uploaded_by = :u
        AND filename = :f
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"u": user, "f": filename})

df_to_edit = get_file_data(target_file, target_user)

if df_to_edit.empty:
    st.warning("No records found for this file.")
    st.stop()

st.info("Edit the cells and click **Save Changes**")

# (Optional but recommended)
# prevent editing file owner and filename
read_only_cols = ["uploaded_by", "filename"]

edited_df = st.data_editor(
    df_to_edit,
    use_container_width=True,
    hide_index=True,
    disabled=read_only_cols
)

# --- 4. Save logic ---
col_save, _ = st.columns([1, 5])

with col_save:
    if st.button("💾 Save Changes", type="primary"):

        try:
            with engine.begin() as conn:

                delete_query = text("""
                    DELETE FROM data
                    WHERE uploaded_by = :u
                    AND filename = :f
                """)

                conn.execute(delete_query, {
                    "u": target_user,
                    "f": target_file
                })

                edited_df.to_sql(
                    "data",
                    con=conn,
                    if_exists="append",
                    index=False
                )

            st.success("Database updated successfully!")

        except Exception as e:
            st.error(f"Error saving changes: {e}")
