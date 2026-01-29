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
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{password_encoded}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

st.set_page_config(page_title="HeidiSQL Data Manager", layout="wide")

# --- Custom CSS for Fixed Top-Right Logout Button ---
st.markdown("""
<style>
.logout-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
}
.logout-btn {
    background-color: #dc3545;
    color: white;
    border: 2px solid black;
    border-radius: 5px;
    padding: 8px 20px;
    font-weight: bold;
    cursor: pointer;
    font-size: 14px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}
.logout-btn:hover {
    background-color: #bb2d3b;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
}
</style>
""", unsafe_allow_html=True)

# --- SINGLE Logout Button (Fixed Top Right) ---
col1, col2, col3 = st.columns([8, 1, 1])
with col3:
    if st.button("🚪 Logout", key="logout_main"):
        st.session_state.logged_in = False
        st.success("Logged out successfully!")
        st.switch_page("login.py")

# --- Page Title ---
st.title("📊 Data Portal")
st.markdown("---")




# --- Initialize Session State ---
if 'upload_done' not in st.session_state:
    st.session_state.upload_done = False

# --- Section 1: Upload ---
with st.expander("⬆️ Upload New Data"):
    if not st.session_state.upload_done:
        uploaded_file = st.file_uploader(
            "Upload .xlsx or .csv file",
            type=["xlsx", "csv"]
        )

        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                df_upload = pd.read_csv(uploaded_file)
            else:
                df_upload = pd.read_excel(uploaded_file)

            if st.button("Upload Data"):
                df_upload.to_sql(
                    TABLE_NAME,
                    con=engine,
                    if_exists="replace",
                    index=False
                )
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
        f_status = st.selectbox("Status", ["All", "Active", "Inactive"])

    submit_button = st.form_submit_button("Search")

# --- Section 3: Logic & Results ---
if submit_button:
    try:
        df_db = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", con=engine)

        if f_name:
            df_db = df_db[df_db['Name'].astype(str).str.contains(f_name, case=False, na=False)]
        if f_mobile:
            df_db = df_db[df_db['Mobile'].astype(str).str.contains(f_mobile, case=False, na=False)]
        if f_email:
            df_db = df_db[df_db['Email'].astype(str).str.contains(f_email, case=False, na=False)]
        if f_address:
            df_db = df_db[df_db['Address'].astype(str).str.contains(f_address, case=False, na=False)]
        if f_city:
            df_db = df_db[df_db['City'].astype(str).str.contains(f_city, case=False, na=False)]
        if f_state:
            df_db = df_db[df_db['State'].astype(str).str.contains(f_state, case=False, na=False)]
        if f_country:
            df_db = df_db[df_db['Country'].astype(str).str.contains(f_country, case=False, na=False)]
        if f_pincode:
            df_db = df_db[df_db['pincode'].astype(str).str.contains(f_pincode, case=False, na=False)]
        if f_status != "All":
            df_db = df_db[df_db['Status'] == f_status]

        act1, act2, act3 = st.columns([1, 2, 5])

        with act1:
            if not df_db.empty:
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                    df_db.to_excel(writer, index=False, sheet_name="Results")
                buffer.seek(0)

                st.download_button(
                    "📥 Download Excel",
                    data=buffer,
                    file_name="results.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

        with act2:
            st.metric("Records Found", len(df_db))

        st.dataframe(df_db, use_container_width=True, height=600)

    except Exception as e:
        st.error(f"Error: {e}")
