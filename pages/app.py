import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import io
from sqlalchemy import text

DB_USER = "project"
DB_PASSWORD = "project123"
DB_HOST = "192.168.5.8"
DB_PORT = "3306"
DB_NAME = "Newproj"
TABLE_NAME = "data"

SUPERADMIN_EMAIL = "admin@example.com"
SUPERADMIN_PASS = "Admin@123" 

# --- Database Setup ---
password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

st.set_page_config(page_title="HeidiSQL Data Manager", layout="wide")

# --- Security Check ---
# Assuming 'user_email' is stored in session_state during login.py
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    if "user" in st.query_params:
        st.session_state.user_email = st.query_params["user"]
    else:
        st.switch_page("login.py")

# Ensure URL always has the user email for refresh-persistence
st.query_params["user"] = st.session_state.user_email
    

current_user = st.session_state.get('user_email', 'unknown')
is_superadmin = (current_user == SUPERADMIN_EMAIL)
if st.session_state.get("admin_view") == "editor":
    st.switch_page("pages/edit.py")

# --- Logout Styling & Logic ---
st.markdown("""
<style>
.logout-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
.logout-btn { background-color: #dc3545; color: white; border-radius: 8px; padding: 10px 24px; font-weight: bold; cursor: pointer; border: none; }
</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>
.user_info-container { position: fixed; top: 20px; right: 20px; z-index: 1000; }
.user_info-btn { background-color: #dc3545; color: white; border-radius: 10px; padding: 10px 24px; font-weight: bold; cursor: pointer; border: 10px solid black; }
</style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([8, 1, 1])
with col3:
    if st.button("Logout!", key="logout_main"):
        st.session_state.clear()
        st.switch_page("login.py")

with col2:
    if is_superadmin:
     if st.button("User Information"):
        st.switch_page("pages/user.py")

st.title("📊 Data Portal")
if is_superadmin:
    st.info(f"Logged in as Superadmin: {current_user}")
else:
    st.info(f"👤 Logged in as: {current_user}")

st.markdown("---")

# --- Section 1: Upload (With Ownership Tagging) ---
with st.expander("⬆️ Upload New Data"):
    if not st.session_state.get('upload_done', False):
        uploaded_file = st.file_uploader("Upload .xlsx or .csv file", type=["xlsx", "csv"])

        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
            
            # ATTACH OWNERSHIP: This ensures only this user can see this data later
            df_upload['uploaded_by'] = current_user
            df_upload['filename'] = uploaded_file.name

            if st.button("Upload Data"):
                df_upload.to_sql(TABLE_NAME, con=engine, if_exists="append", index=False)
                st.session_state.upload_done = True
                st.success("Data Uploaded Successfully!")
                st.rerun()
    else:
        st.info("✅ Data is currently loaded.")
        if st.button("Upload a different file"):
            st.session_state.upload_done = False
            st.rerun()

st.divider()

# --- Section 2: Search & Filter ---
st.subheader("🔍 Search & Filter")
with st.form("search_form"):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: 
        f_name = st.text_input("Name")
        f_mobile = st.text_input("Mobile")
    with c2: 
        f_email = st.text_input("Email")
        f_address = st.text_input("Address")
    with c3: 
        f_city = st.text_input("City")
        f_state = st.text_input("State")
    with c4: 
        f_country = st.text_input("Country")
        f_pincode = st.text_input("PinCode")
    with c5: 
        f_status = st.selectbox("Status", ["All", "Active", "Inactive"])
        if is_superadmin:
            f_uploaded_by = st.text_input("Uploaded By")
    submit_button = st.form_submit_button("Search")


if submit_button or st.session_state.get('filtered_df') is not None:
    try:
      with engine.connect() as conn:
        
        if is_superadmin:
                # Query for Superadmin (All data)
                query = text(f"SELECT * FROM {TABLE_NAME}")
                params = {}
        else:
                # Query for Regular User (Filtered by owner)
                query = text(f"SELECT * FROM {TABLE_NAME} WHERE uploaded_by = :user")
                params = {"user": current_user}
        df_db = pd.read_sql(query, con=conn, params=params)
        
        if f_name: df_db = df_db[df_db['Name'].astype(str).str.contains(f_name, case=False, na=False)]
        if f_mobile: df_db = df_db[df_db['Mobile'].astype(str).str.contains(f_mobile, case=False, na=False)]
        if f_email: df_db = df_db[df_db['Address'].astype(str).str.contains(f_email, case=False, na=False)]
        if f_address: df_db = df_db[df_db['Email'].astype(str).str.contains(f_address, case=False, na=False)]
        if f_city: df_db = df_db[df_db['City'].astype(str).str.contains(f_city, case=False, na=False)]
        if f_state: df_db = df_db[df_db['State'].astype(str).str.contains(f_state, case=False, na=False)]
        if f_country: df_db = df_db[df_db['Country'].astype(str).str.contains(f_country, case=False, na=False)]
        if f_pincode: df_db = df_db[df_db['pincode'].astype(str).str.contains(f_pincode, case=False, na=False)]
        if f_status != "All": df_db = df_db[df_db['Status'] == f_status]
        if is_superadmin:
          if  f_uploaded_by: df_db = df_db[df_db['uploaded_by'].astype(str).str.contains(f_uploaded_by, case=False, na=False)]

        st.session_state.filtered_df = df_db

    except Exception as e:
        st.error(f"Error fetching data: {e}")

# --- Display Logic ---
if st.session_state.get('filtered_df') is not None:
    df_res = st.session_state.filtered_df
    
    act1, act2, act3, act4 = st.columns([1.5, 1.5, 2, 4])
    with act1:
        if not df_res.empty:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                df_res.to_excel(writer, index=False)
            st.download_button("📥 Download Excel", data=buffer.getvalue(), file_name="results.xlsx")
    
    with act2:
        st.metric("Total Records", len(df_res))

    with act3:
        display_limit = st.selectbox("Show rows:", options=["100", "500", "All"], index=0)

    df_display = df_res if display_limit == "All" else df_res.head(int(display_limit))
    if is_superadmin:
        st.subheader("📝 Edit Mode ")
        
        edited_df = st.data_editor(
            df_display, 
            use_container_width=True, 
            height=400,
            num_rows="dynamic", 
            key="admin_editor"
        )
        if 'data_saved' not in st.session_state:
          st.session_state.data_saved = False

        if st.button("💾 Save Changes to Database"):
            try:
                
                edited_df.to_sql(TABLE_NAME, con=engine, if_exists="replace", index=False)
                st.session_state.data_saved = True
                st.session_state.filtered_df = edited_df
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")
        if st.session_state.data_saved:
           st.success("Data saved successfully in database!")
           st.session_state.data_saved = False 
    else:
        
        st.dataframe(df_display, use_container_width=True, height=500)