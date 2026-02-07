import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# Database Setup
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Navigation Header
nav_col, home_col, logout_col = st.columns([5, 1, 1])
with home_col:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")

st.title("👥 User Upload Registry")

try:
    with engine.connect() as conn:
        query = text("SELECT uploaded_by, filename, COUNT(*) as records FROM data GROUP BY uploaded_by, filename")
        df = pd.read_sql(query, con=conn)
    
    if df.empty:
        st.warning("No data found in the database.")
    else:
        # Table UI
        h1, h2, h3, h4 = st.columns([2, 2, 1, 1])
        h1.write("**User Email**")
        h2.write("**Filename**")
        h3.write("**Total Rows**")
        h4.write("**Action**")
        st.divider()

        for idx, row in df.iterrows():
            c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
            c1.text(row['uploaded_by'])
            c2.text(row['filename'] or "Unknown")
            c3.write(row['records'])
            
            # Clicking this sets the variables and switches page
            if c4.button("Edit Data", key=f"btn_{idx}"):
                st.session_state.target_user = row['uploaded_by']
                st.session_state.target_file = row['filename']
                st.switch_page("pages/edit.py") # Ensure this matches your filename

except Exception as e:
    st.error(f"Error: {e}")