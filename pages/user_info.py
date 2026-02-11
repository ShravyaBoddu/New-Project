import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text as sql_text
import urllib.parse

# Configure page config FIRST
st.set_page_config(page_title="User Information", layout="wide")

# --- 1. Database Setup ---
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

def update_db_permission(email, status):
    try:
        with engine.begin() as conn:
            query = sql_text("""
                INSERT INTO file_permissions (perm_id, permission_status) 
                VALUES (:id, :status) 
                ON DUPLICATE KEY UPDATE permission_status = :status
            """)
            conn.execute(query, {"id": email, "status": status})
    except Exception as e:
        st.error(f"Error updating database: {e}")

def get_all_permissions():
    try:
        with engine.connect() as conn:
            res = conn.execute(sql_text("SELECT perm_id, permission_status FROM file_permissions"))
            return {row[0]: row[1] for row in res.fetchall()}
    except Exception:
        return {}

if "permissions_map" not in st.session_state:
    st.session_state.permissions_map = get_all_permissions()

# --- 2. Navigation Header ---
col_nav,col_back, col_logout = st.columns([5,1,1])
with col_back:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with col_logout:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.title("👥 User Administration")

# --- 3. Data Fetching ---
def fetch_all_users():
    try:
        with engine.connect() as conn:
            query = sql_text("SELECT name, email ,password FROM login ORDER BY name ASC")
            return pd.read_sql(query, con=conn)
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return pd.DataFrame()

df = fetch_all_users()

# --- 4. Search & Filter Section ---
st.subheader("🔍 Search & Filter")

# Corrected Form Implementation
with st.form("search_form"):
    c1, c2 = st.columns(2)
    f_name = c1.text_input("Filter by Name")
    f_email = c2.text_input("Filter by Email")
    submit_button = st.form_submit_button("Search")

# Apply filtering based on form inputs
display_df = df.copy()
if f_name:
    display_df = display_df[display_df['name'].str.contains(f_name, case=False, na=False)]
if f_email:
    display_df = display_df[display_df['email'].str.contains(f_email, case=False, na=False)]

metric_col, add_user_col = st.columns([3, 1])
metric_col.metric("Total Unique Users", len(display_df))
with add_user_col:
    if st.button("Add New User", use_container_width=True):
        st.switch_page("pages/signup.py")

st.divider()

# --- 5. UI Table Display ---
if display_df.empty:
    st.warning("⚠️ No user records found.")
else:
    # Header Row
    h1, h2, h3, h4 = st.columns([2, 3, 1.5, 2.5])
    h1.markdown("**Name**")
    h2.markdown("**Email**")
    h3.markdown("**Password**")
    h4.markdown("**Permission Status**")
    st.divider()

    for idx, row in display_df.iterrows():
        u_name = row['name']
        u_email = row['email']
        u_password = row['password']
        current_status = st.session_state.permissions_map.get(u_email, "NO")
        
        with st.container():
            c1, c2, c3, c4 = st.columns([2, 3, 1.5, 2.5])
            
            c1.text(u_name)
            c2.text(u_email)
            c3.text(u_password)
            
            # 5a. EDIT BUTTON
           
            
            # 5b. PERMISSION RADIO
            with c4:
                radio_idx = 0 if current_status == "YES" else 1
                choice = st.radio(
                    f"Label_{u_email}",
                    ["YES", "NO"],
                    index=radio_idx,
                    key=f"radio_{u_email}",
                    label_visibility="collapsed",
                    horizontal=True
                )
                
                if choice != current_status:
                    update_db_permission(u_email, choice)
                    st.session_state.permissions_map[u_email] = choice
                    st.rerun()