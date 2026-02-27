import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
import urllib.parse
import io
from sqlalchemy import text

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

st.set_page_config(page_title="HeidiSQL Data Manager", layout="wide", initial_sidebar_state="collapsed")

def get_user_role(email):
    with engine.connect() as conn:
        q = text("SELECT role FROM login WHERE email = :email")
        row = conn.execute(q, {"email": email}).fetchone()
        return row[0] if row else "user"

# --- Security Check ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    if "user" in st.query_params:
        st.session_state.user_email = st.query_params["user"]
    else:
        st.switch_page("login.py")

st.query_params["user"] = st.session_state.user_email
current_user = st.session_state.get('user_email', 'unknown')
user_role = get_user_role(current_user)
is_superadmin = (user_role == "admin")

if st.session_state.get("admin_view") == "editor":
    st.switch_page("pages/edit.py")

# --- CSS STYLING ---
st.markdown("""
<style>
    /* Main Background */
    [data-testid="stAppViewContainer"] { background-color: #f8f9fc; }

    /* Header Buttons: ALL Light Blue Background + Black Border */
    div[data-testid="stButton"] button {
        # background-color: #6495ED !important; /* Light Blue */
        border: 1px solid black !important;   /* Black Border */
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
        color: black !important;              /* Dark text for better contrast */
    }

    /* Save Changes Button: White Background + Black Border */
    div[data-testid="stButton"] button:has(div p:contains("Save Changes to Database")) {
        background-color: white !important;
        border: 2px solid black !important;
       
        border-radius: 8px;
    }

    /* Download Excel Button: White Background + Black Border */
    div[data-testid="stDownloadButton"] button {
        background-color: white !important;
        border: 1px solid black !important;
        border-radius: 8px;
        color: black !important;
    }

    /* Search Button (Primary Blue) */
    .stFormSubmitButton > button {
        background-color: #4169E1 !important;
        color: white !important;
        # border: 1px solid black!important;
        height: 3em;
        width: 100%;
        border-radius: 8px;
    }

    /* Keep Borders and Colors consistent on Hover */
    div[data-testid="stButton"] button:hover, 
    div[data-testid="stDownloadButton"] button:hover {
        border: 2px solid black !important;
        background-color: #B0C4DE !important;
    }

    /* Metrics & Inputs */
    [data-testid="stMetricValue"] { color: #4169E1 !important; font-weight: 800; }
    div[data-baseweb="base-input"] { border: 1px solid #cbd5e1 !important; border-radius: 8px !important; }

    /* Hide UI Elements */
    [data-testid="collapsedControl"] { display: none; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- Header Row ---
_, col_btns = st.columns([8, 5])

with col_btns:
    if is_superadmin:
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("📁File History"):
                st.switch_page("pages/file_hist.py")
        with b2:
            if st.button("👤User Info"):
                st.switch_page("pages/user_info.py")
        with b3:
            if st.button("Logout ⏻", key="logout_main"):
                st.session_state.clear()
                st.switch_page("login.py")
    else:
        b1, b2 = st.columns(2)
        with b1:
            if st.button("📜Account History"):
                st.switch_page("pages/acc.py")
        with b2:
            if st.button("Logout ⏻", key="logout_main"):
                st.session_state.clear()
                st.switch_page("login.py")

st.divider()

st.title("📊 Data Portal")
if is_superadmin:
    st.info(f"Logged in as Superadmin: {current_user}")
else:
    st.info(f"👤 Logged in as: {current_user}")

st.markdown("---")

# --- Section 1: Upload ---
with st.expander("⬆️ Upload New Data"):
    if not st.session_state.get('upload_done', False):
        uploaded_file = st.file_uploader("Upload .xlsx or .csv file", type=["xlsx", "csv"])
        if uploaded_file:
            df_upload = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
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
                query = text(f"SELECT * FROM {TABLE_NAME}")
                params = {}
            else:
                query = text(f"SELECT * FROM {TABLE_NAME} WHERE uploaded_by = :user")
                params = {"user": current_user}
            df_db = pd.read_sql(query, con=conn, params=params)

        if f_name:
            df_db = df_db[df_db['Name'].astype(str).str.contains(f_name, case=False, na=False)]
        if f_mobile:
            df_db = df_db[df_db['Mobile'].astype(str).str.contains(f_mobile, case=False, na=False)]
        if f_email:
            df_db = df_db[df_db['Email'].astype(str).str.contains(f_email, case=False, na=False)]
        if f_city:
            df_db = df_db[df_db['City'].astype(str).str.contains(f_city, case=False, na=False)]
        if f_status != "All":
            df_db = df_db[df_db['Status'] == f_status]
        if is_superadmin and f_uploaded_by:
            df_db = df_db[df_db['uploaded_by'].astype(str).str.contains(f_uploaded_by, case=False, na=False)]

        st.session_state.filtered_df = df_db
    except Exception as e:
        st.error(f"Error fetching data: {e}")

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
        st.subheader("📝 Edit Mode")
        edited_df = st.data_editor(df_display, use_container_width=True, height=400, num_rows="dynamic", key="admin_editor")

        if st.button("💾 Save Changes to Database"):
            try:
                edited_df.to_sql(TABLE_NAME, con=engine, if_exists="replace", index=False)
                st.success("Data saved successfully in database!")
                st.session_state.filtered_df = edited_df
                st.rerun()
            except Exception as e:
                st.error(f"Update failed: {e}")
    else:
        st.dataframe(df_display, use_container_width=True, height=500)

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #6c757d; font-size: 14px; padding: 20px 0;'>
        <p>© 2026 RIGHT SIDE BUSINESS SOLUTIONS PRIVATE LIMITED</p>
    </div>
    """,
    unsafe_allow_html=True
)
