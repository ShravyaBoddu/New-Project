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

# --- 2. Robust Session Handling ---
# This checks if the user is logged in. If not, it shows a message 
# instead of a red error screen.
if 'user_email' not in st.session_state:
    st.warning("Please log in through the home page to access your account.")
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

# --- 3. Cached Data Fetching ---
@st.cache_data(ttl=600) 
def fetch_user_data(email):
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    uploaded_by as email, 
                    filename, 
                    COUNT(*) as total_rows
                FROM data 
                WHERE uploaded_by = :email
                GROUP BY filename, uploaded_by
            """)
            df = pd.read_sql(query, con=conn, params={"email": email})
        return df
    except Exception as e:
        # Don't crash the app, just show the error
        st.error(f"❌ Database connection lost. Please try again.")
        return pd.DataFrame()

# --- 4. Display Logic ---
df = fetch_user_data(current_user_email)

if df.empty:
    st.info("No upload history found for this account.")
else:
    total_files = len(df)
    total_rows = df['total_rows'].sum()
    
    m1, m2 = st.columns(2)
    m1.metric("Files Uploaded", total_files)
    m2.metric("Total Rows Processed", total_rows)

    st.divider()
    
    # Clean display
    st.dataframe(df, use_container_width=True, hide_index=True)