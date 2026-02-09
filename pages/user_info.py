import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text as sql_text
import urllib.parse

# Configure page config FIRST
st.set_page_config(page_title="User Information", layout="wide")

# --- Database Setup ---
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

# --- Navigation Header ---
header_container = st.container()
with header_container:
    col1, col2, col3 = st.columns([5, 1, 1])
    with col2:
        if st.button("⬅️ Back", key="back_btn", use_container_width=True):
            st.switch_page("pages/app.py")
    with col3:
        if st.button("Logout", key="logout_btn", use_container_width=True):
            st.session_state.clear()
            st.switch_page("login.py")

st.title("👥 User Information")

# --- Data Fetching Logic ---
def fetch_all_users():
    try:
        with engine.connect() as conn:
            # We use a LEFT JOIN so we see users even if they haven't uploaded files yet
            query = sql_text("""
                SELECT 
                    l.name AS Name, 
                    l.email AS Email, 
                    l.password AS Password, 
                    GROUP_CONCAT(DISTINCT d.filename SEPARATOR ', ') as Files
                FROM login AS l
                LEFT JOIN data AS d ON l.email = d.uploaded_by
                GROUP BY l.email, l.name, l.password
                ORDER BY l.name ASC
            """)
            return pd.read_sql(query, con=conn)
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

# Load initial data
df = fetch_all_users()

# --- Search Section ---
st.subheader("Search & Filter")
with st.form("search_form"):
    c1, c2 = st.columns(2)
    with c1: 
        f_name = st.text_input("Filter by Name")
    with c2: 
        f_email = st.text_input("Filter by Email")
    
    submit_button = st.form_submit_button("Search")

# --- Filtering Logic ---
display_df = df.copy()

if submit_button:
    if f_name:
        display_df = display_df[display_df['Name'].str.contains(f_name, case=False, na=False)]
    if f_email:
        display_df = display_df[display_df['Email'].str.contains(f_email, case=False, na=False)]

# --- UI Display ---
st.divider()

if display_df.empty:
    st.warning("⚠️ No user records match your criteria.")
else:
    # Display Metrics
    total_unique = display_df['Email'].nunique()
    st.metric(label="Users Found", value=total_unique)

    # Enhanced dataframe display
    st.dataframe(
        display_df, 
        use_container_width=True,
        hide_index=True,
        column_config={
            "Name": st.column_config.TextColumn("👤 Name", width="medium"),
            "Email": st.column_config.TextColumn("📧 Email", width="medium"),
            "Password": st.column_config.TextColumn("🔒 Password", width="small"),
            "Files": st.column_config.TextColumn("📁 Uploaded Files", width="large")
        }
    )

st.markdown("---")