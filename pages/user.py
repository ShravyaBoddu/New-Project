import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# Database Setup - Cache the engine to prevent recreation on every rerun
@st.cache_resource
def init_db():
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
    password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
    return create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

engine = init_db()

# Configure page layout at the TOP before any content
st.set_page_config(page_title="File Upload History", layout="wide")

# Navigation Header - Use containers for stable layout
nav_col, home_col, logout_col = st.columns([5, 1, 1])
with home_col:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")


st.title("📁 File Upload History")

# Load data with caching
@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_file_history():
    try:
        with engine.connect() as conn:
            query = text("SELECT uploaded_by, filename, COUNT(*) as records FROM data GROUP BY uploaded_by, filename")
            return pd.read_sql(query, con=conn)
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

df = load_file_history()

if df.empty:
    st.warning("No data found in the database.")
else:
    # Header row with consistent layout
    col1, col2, col3, col4, col5 = st.columns([3, 3, 1, 1, 2])
    with col1:
        st.markdown("**User Email**")
    with col2:
        st.markdown("**Filename**")
    with col3:
        st.markdown("**Total Rows**")
    with col4:
        st.markdown("**Edit**")
    with col5:
        st.markdown("**Delete**")

    st.divider()

    # Data rows with consistent layout
    for idx, row in df.iterrows():
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3, 3, 1, 1, 2])
            
            with c1:
                st.write(row['uploaded_by'])
            with c2:
                st.write(row['filename'] or "Unknown")
            with c3:
                st.write(f"{int(row['records']):,}")
            
            with c4:
                if st.button("Edit", key=f"edit_{idx}_{row['filename']}", use_container_width=True):
                    st.session_state.target_user = row['uploaded_by']
                    st.session_state.target_file = row['filename']
                    st.switch_page("pages/edit.py")
            
            with c5:
                if st.button(" Delete", key=f"delete_{idx}_{row['filename']}", use_container_width=True):
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
                                
                                st.cache_data.clear()  # Clear cache after delete
                                st.rerun()
                            else:
                                st.warning("No records found to delete.")
                    except Exception as e:
                        st.error(f"Error deleting file: {str(e)}")
    
    st.divider()
