import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
import urllib.parse

# --- Database Setup ---
DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME = "project", "project123", "192.168.5.8", "3306", "Newproj"
password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


nav_col, home_col, logout_col = st.columns([5, 1, 1])
with home_col:
    if st.button("⬅️ Back"):
        st.switch_page("pages/app.py")
with logout_col:
    if st.button("Logout"):
        st.session_state.clear()
        st.switch_page("login.py")


current_user_email = st.session_state.get('user_email')


st.title("👥 User Information")

@st.cache_data
def fetch_user_stats():
    """Fetch cached user statistics with unique user rows"""
    try:
        with engine.connect() as conn:
            
            count_query = text("SELECT COUNT(DISTINCT uploaded_by) AS total_unique_users FROM data")
            result = conn.execute(count_query).fetchone()
            total_users = result[0] if result else 0
            
           
            query = text("""
                SELECT 
                    l.email, 
                    l.password, 
                    GROUP_CONCAT(DISTINCT d.filename SEPARATOR ',') as filenames
                FROM login AS l
                JOIN data AS d ON l.email = d.uploaded_by
                GROUP BY l.email, l.password
            """)
            df = pd.read_sql(query, con=conn)
        
        return total_users, df
    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        return 0, pd.DataFrame()


total_users, df = fetch_user_stats()

if total_users == 0:
    st.warning("⚠️ No user records found in the database.")
else:
   
    st.metric(label="Total Unique Users with Data", value=total_users)
    
    st.divider()

    st.subheader("Registered User Details")
    
   
    df.columns = ['Email Address', 'Password', 'Uploaded Files']
    
    
    st.dataframe(
        df, 
        use_container_width=True,
        hide_index=True
    )