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

st.title("📁 File Upload History")

try:
    with engine.connect() as conn:
        query = text("SELECT uploaded_by, filename, COUNT(*) as records FROM data GROUP BY uploaded_by, filename")
        df = pd.read_sql(query, con=conn)
    
    if df.empty:
        st.warning("No data found in the database.")
    else:
        # Table UI
        h1, h2, h3, h4,h5 = st.columns([3, 3, 1, 1,2])
        h1.write("**User Email**")
        h2.write("**Filename**")
        h3.write("**Total Rows**")
        h4.write("**Edit**")
        h5.write("**Delete**")

        st.divider()

        for idx, row in df.iterrows():
            c1, c2, c3, c4,c5 = st.columns([3, 3, 1, 1,2])
            c1.text(row['uploaded_by'])
            c2.text(row['filename'] or "Unknown")
            c3.write(row['records'])
            
            
            if c4.button("Edit", key=f"edit_{idx}"):
                st.session_state.target_user = row['uploaded_by']
                st.session_state.target_file = row['filename']
                st.switch_page("pages/edit.py")
            
            
            if c5.button("Delete", key=f"delete_{idx}_{row['filename']}"):
                try:
                    with engine.connect() as conn:
                        
                        delete_query = text("""
                            DELETE FROM data 
                            WHERE filename = :filename AND uploaded_by = :uploaded_by
                        """)
                        result = conn.execute(delete_query, {
                            "filename": row['filename'], 
                            "uploaded_by": row['uploaded_by']  
                        })
                        conn.commit()
                        
                        if result.rowcount > 0:
                            st.success(f"✅ Deleted {result.rowcount} records from {row['filename']}!")
                            st.rerun()  
                        else:
                            st.warning("No records found to delete.")
                            
                except Exception as e:
                    st.error(f"Error deleting file: {str(e)}")


except Exception as e:
    st.error(f"Error loading data: {str(e)}")
