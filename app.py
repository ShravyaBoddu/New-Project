import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import io

# --- Database Setup ---
DB_USER = "project"
DB_PASSWORD = "project123" 
DB_HOST = "192.168.5.8"
DB_PORT = "3306"
DB_NAME = "Newproj"
TABLE_NAME = "data"

password_encoded = urllib.parse.quote_plus(DB_PASSWORD)
engine = create_engine(f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

st.set_page_config(page_title="HeidiSQL Data Manager", layout="wide")
st.title("📊 Data Portal")

# --- Initialize Session State ---
if 'upload_done' not in st.session_state:
    st.session_state.upload_done = False

# --- Section 1: Upload ---
with st.expander("⬆️ Upload New Excel Data"):
    if not st.session_state.upload_done:
        uploaded_file = st.file_uploader("Upload .xlsx file", type=["xlsx"])
        if uploaded_file:
            df_upload = pd.read_excel(uploaded_file)
            if st.button("Upload Data"):
                df_upload.to_sql(TABLE_NAME, con=engine, if_exists='replace', index=False)
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
        f_pincode = st.text_input("Pincode")
    with c5:
        f_status = st.selectbox("Status", options=["All", "Active", "Inactive"])
    
    # Submit button for the form
    submit_button = st.form_submit_button(label=" Search")

# --- Section 3: Logic & Results ---
if submit_button or 'last_df' in st.session_state:
    try:
        # Fetch and Filter logic
        df_db = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", con=engine)
        
        if f_name: df_db = df_db[df_db['Name'].astype(str).str.contains(f_name, case=False, na=False)]
        if f_mobile: df_db = df_db[df_db['Mobile'].astype(str).str.contains(f_mobile, case=False, na=False)]
        if f_email: df_db = df_db[df_db['Email'].astype(str).str.contains(f_email, case=False, na=False)]
        if f_address: df_db = df_db[df_db['Address'].astype(str).str.contains(f_address, case=False, na=False)]
        if f_city: df_db = df_db[df_db['City'].astype(str).str.contains(f_city, case=False, na=False)]
        if f_state: df_db = df_db[df_db['State'].astype(str).str.contains(f_state, case=False, na=False)]
        if f_country: df_db = df_db[df_db['Country'].astype(str).str.contains(f_country, case=False, na=False)]
        if f_pincode: df_db = df_db[df_db['pincode'].astype(str).str.contains(f_pincode, case=False, na=False)]
        if f_status != "All":
            df_db = df_db[df_db['Status'].astype(str).str.contains(f_status, case=False, na=False)]

        # --- ACTION ROW (Beside Submit Area) ---
        # We create columns here to show the download button and the count side-by-side
        act1, act2, act3 = st.columns([1, 2, 5])
        
        with act1:
            if not df_db.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_db.to_excel(writer, index=False, sheet_name='Results')
                buffer.seek(0)
                
                st.download_button(
                    label="📥 Download Excel",
                    data=buffer,
                    file_name="results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with act2:
            st.metric("Records Found", len(df_db))

        # Display Table
        st.dataframe(df_db, use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")