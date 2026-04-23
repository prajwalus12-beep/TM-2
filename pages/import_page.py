import streamlit as st
import pandas as pd
import io
from database.queries import import_employees, import_projects, import_assignments

def get_excel_download(df):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return buffer.getvalue()

def read_excel_or_csv(uploaded_file):
    """Read File depending on extension."""
    if uploaded_file.name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding='cp1252')
    else:
        return pd.read_excel(uploaded_file)

def render_import_page():
    st.subheader("Import Data", divider="blue")
    col_emp, col_proj, col_assign = st.columns(3)
    
    with col_emp:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 👥 Employees")
        uploaded_file = st.file_uploader("Upload Employees File", type=["xls", "xlsx", "csv"], key="emp_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Employees", type="primary"):
                success, msg = import_employees(df)
                st.success(msg) if success else st.error(msg)
        
        sample_emp = pd.DataFrame([["101", "John Doe", "U12345"]], columns=['a__Serial', 'Name', 'Slack ID'])
        st.download_button("📥 Sample Employee Excel", get_excel_download(sample_emp), "sample_employees.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'a__Serial', 'Name', 'Slack ID'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_proj:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🏗️ Projects")
        uploaded_file = st.file_uploader("Upload Projects File", type=["xls", "xlsx", "csv"], key="proj_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Projects", type="primary"):
                success, msg = import_projects(df)
                st.success(msg) if success else st.error(msg)
        
        sample_proj = pd.DataFrame([["P001", "High", "Website Redesign", "2024-01-01", "2024-12-31", "In progress", "Alice", "https://trello.com/b/123", "https://figma.com/file/123"]], columns=['Job No', 'Job Priority', 'Project', 'Date Start', 'Date Finish', 'Status', 'Lead engineer', 'Trello', 'Prototype'])
        st.download_button("📥 Sample Project Excel", get_excel_download(sample_proj), "sample_projects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Job No', 'Job Priority', 'Project', 'Date Start', 'Date Finish', 'Status', 'Lead engineer', 'Trello', 'Prototype'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_assign:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔗 Assignments")
        uploaded_file = st.file_uploader("Upload Assignments File", type=["xls", "xlsx", "csv"], key="assign_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Assignments", type="primary"):
                success, msg = import_assignments(df)
                st.success(msg) if success else st.error(msg)
        
        sample_assign = pd.DataFrame([["101", "P001"]], columns=['Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'])
        st.download_button("📥 Sample Assignment Excel", get_excel_download(sample_assign), "sample_assignments.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'.")
        st.markdown('</div>', unsafe_allow_html=True)
