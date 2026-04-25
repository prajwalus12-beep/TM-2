import streamlit as st
from database.queries import init_db
from services.auth_service import check_login
from components.sidebar import render_sidebar
from pages.login_page import render_login_page
from pages.timesheet_page import render_timesheet_page
from pages.projects_page import render_projects_page
from pages.employees_page import render_employees_page
from pages.reports_page import render_reports_page
from pages.import_page import render_import_page
from pages.project_update_page_v2 import render_project_update_page_v2
from config.constants import PAGE_CONFIG

# 1. Page Config
st.set_page_config(**PAGE_CONFIG)

# 2. Global Styling
with open("assets/css/style.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Initialize Database
if "db_initialized" not in st.session_state:
    success, msg = init_db()
    if success: st.session_state["db_initialized"] = True
    else: st.error(msg)

# 4. Authentication
user = check_login()

if not user:
    # Hide sidebar when not logged in
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none; }
            [data-testid="collapsedControl"] { display: none; }
        </style>
    """, unsafe_allow_html=True)
    render_login_page()
else:
    # Ensure sidebar toggle button is visible when logged in (overriding login page CSS)
    st.markdown("""
        <style>
            [data-testid="collapsedControl"],
            button[kind="headerNoPadding"] { 
                display: flex !important; 
                visibility: visible !important;
                opacity: 1 !important;
                z-index: 999999 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 5. Routing
    if "page" not in st.session_state:
        st.session_state["page"] = "Timesheet Entries"

    # Sidebar Navigation
    render_sidebar(user)

    # Page Content
    page = st.session_state["page"]
    if page == "Timesheet Entries": render_timesheet_page(user)
    elif page == "Projects": render_projects_page()
    elif page == "Employees": render_employees_page(user)
    elif page == "Reports": render_reports_page(user)
    elif page == "Import Data": render_import_page()
    elif page == "Project Update": render_project_update_page_v2()
