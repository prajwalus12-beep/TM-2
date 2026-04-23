import streamlit as st
import datetime
import pandas as pd
import io
import openpyxl
from database.queries import get_timesheets, get_all_employees, get_all_projects, delete_timesheet_entry
from components.dialogs import entry_form_dialog, edit_form_dialog
from utils.date_helpers import get_curr_cycle_dates

def render_timesheet_page(user):
    hdr_col, btn_col1, btn_col2 = st.columns([7, 1.5, 1.5])
    with hdr_col:
        st.subheader("Timesheet Entries", divider="blue")
        st.caption("Review and manage time logs")

    emps = get_all_employees()
    current_emp_id = user.get("employee_id")
    emp_labels = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in emps.iterrows()}

    current_emp_name_label = next((k for k, v in emp_labels.items() if v == current_emp_id), "All")
    is_admin = user.get("role") == "admin"
    default_emp_filter = "All" if is_admin else current_emp_name_label

    # Handle reset flag BEFORE widgets are instantiated
    if st.session_state.pop('_reset_filters', False):
        st.session_state.date_range_preset = "This Week"
        st.session_state.filter_emp = default_emp_filter
        st.session_state.filter_proj = "All"

    # Initialize filters
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime.date.today() - datetime.timedelta(days=30)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.date.today()
    if 'date_range_preset' not in st.session_state:
        st.session_state.date_range_preset = "This Week"
    if 'filter_emp' not in st.session_state:
        st.session_state.filter_emp = default_emp_filter
    if 'filter_proj' not in st.session_state:
        st.session_state.filter_proj = "All"

    with st.container(border=True):
        # Dynamic ratios to minimize space when Custom Range is not active
        date_range_preset = st.session_state.get('date_range_preset', 'This Week')
        if date_range_preset == "Custom Range":
            ratios = [1.5, 2.7, 2.3, 2.3, 1.2]
        else:
            ratios = [2.5, 0.1, 3.0, 3.0, 1.4]
            
        col_preset, col_custom, col_emp, col_proj, col_clear = st.columns(ratios)
        
        with col_preset:
            date_range_option = st.selectbox("Date Range", ["This Week", "Last Week", "Current 4 Week Cycle", "Previous 4 Week Cycle", "Custom Range"], key="date_range_preset")
            today = datetime.date.today()
            start_of_this_week = today - datetime.timedelta(days=today.weekday())
            
            if date_range_option == "This Week":
                calc_start, calc_end = start_of_this_week, start_of_this_week + datetime.timedelta(days=6)
            elif date_range_option == "Last Week":
                calc_start, calc_end = start_of_this_week - datetime.timedelta(days=7), start_of_this_week - datetime.timedelta(days=1)
            elif date_range_option == "Current 4 Week Cycle":
                calc_start, calc_end = get_curr_cycle_dates(today)
            elif date_range_option == "Previous 4 Week Cycle":
                curr_start, _ = get_curr_cycle_dates(today)
                calc_start, calc_end = curr_start - datetime.timedelta(days=28), curr_start - datetime.timedelta(days=1)

        with col_custom:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if date_range_option == "Custom Range":
                sub1, sub2 = st.columns(2)
                start_date = sub1.date_input("Start", key="start_date")
                end_date = sub2.date_input("End", key="end_date")
                if end_date < start_date:
                    st.error("⚠️ End date can't be smaller than start date")
                    st.stop()
            else:
                start_date, end_date = calc_start, calc_end

        with col_emp:
            if is_admin:
                emp_options = ["All"] + list(emp_labels.keys())
                selected_emp_name = st.selectbox("Employee", emp_options, key="filter_emp")
            else:
                emp_options = [current_emp_name_label]
                selected_emp_name = st.selectbox("Employee", emp_options, disabled=True, key="filter_emp")
            
            selected_emp_id = emp_labels.get(selected_emp_name) if selected_emp_name != "All" else None

        with col_proj:
            all_projs = get_all_projects()
            all_projs['job_no_numeric'] = pd.to_numeric(all_projs['project_code'], errors='coerce')
            all_projs = all_projs.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False])
            
            proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_code'] for _, r in all_projs.iterrows()}
            selected_proj_name = st.selectbox("Project", ["All"] + list(proj_options.keys()), key="filter_proj")
            selected_proj_code = proj_options[selected_proj_name] if selected_proj_name != "All" else None
        
        with col_clear:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if st.button("🧹 Clear", use_container_width=True, key="clear_main_filters"):
                st.session_state._reset_filters = True
                st.rerun()

    # Integrated Date Range Display under the filter box
    st.caption(f"Showing records from :blue[**{start_date.strftime('%d-%m-%Y')}**] to :blue[**{end_date.strftime('%d-%m-%Y')}**]")

    data = get_timesheets(start_date, end_date, selected_emp_id, selected_proj_code)

    with btn_col1:
        st.write("")
        if user["role"] != "admin":
            if st.button("➕ Add Entry", type="primary", use_container_width=True):
                entry_form_dialog(user, emp_labels, current_emp_id)
    
    with btn_col2:
        st.write("")
        if not data.empty:
            export_df = data.copy().rename(columns={
                'project_code': 'Project_Code', 
                'emp_name': 'Emp_Name', 
                'project_name': 'Project_Name', 
                'date': 'Date', 
                'hours': 'Hours', 
                'phase': 'Phase'
            })
            export_df['Emp_Code'] = data['emp_id']
            export_df['Date'] = pd.to_datetime(export_df['Date']).dt.strftime('%d-%m-%Y')
            phase_map = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployement", "6": "Support"}
            export_df['Phase'] = export_df['Phase'].astype(str).map(phase_map).fillna(export_df['Phase'])
            
            # Convert columns to numeric to avoid Excel "Number Stored as Text" warnings
            export_df['Emp_Code'] = pd.to_numeric(export_df['Emp_Code'], errors='coerce')
            export_df['Project_Code'] = pd.to_numeric(export_df['Project_Code'], errors='coerce')
            
            # Sort by Employee Code then Date to match screenshot
            export_df = export_df.sort_values(by=['Emp_Code', 'Date'])
            
            # Select columns in requested order
            output_df = export_df[['Emp_Code', 'Emp_Name', 'Hours', 'Project_Code', 'Project_Name', 'Phase', 'Date']]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                output_df.to_excel(writer, index=False, sheet_name='Timesheets')
                
                # Remove default pandas header styling (bold, borders)
                worksheet = writer.sheets['Timesheets']
                for cell in worksheet[1]:
                    if cell.font:
                        cell.font = openpyxl.styles.Font(bold=False)
                    if cell.border:
                        cell.border = openpyxl.styles.Border()
            
            st.download_button(
                label="📥 Export Excel", 
                data=buffer.getvalue(), 
                file_name=f"timesheet_export_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True,
                type="primary"
            )
    # Pagination & Table
    rows_per_page = 10
    if not data.empty:
        total_pages = (len(data) - 1) // rows_per_page + 1
        if "page_num" not in st.session_state: st.session_state.page_num = 1
        st.session_state.page_num = max(1, min(st.session_state.page_num, total_pages))
        
        start_idx = (st.session_state.page_num - 1) * rows_per_page
        subset = data.iloc[start_idx:start_idx + rows_per_page]

        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header">'
                    '<div style="flex: 1.5;">Date</div>'
                    '<div style="flex: 1;">Emp Code</div>'
                    '<div style="flex: 2;">Emp Name</div>'
                    '<div style="flex: 1;">Project Code</div>'
                    '<div style="flex: 3;">Project name</div>'
                    '<div style="flex: 1.5;">Status</div>'
                    '<div style="flex: 1.2;">Phases</div>'
                    '<div style="flex: 0.8;">Hours</div>'
                    '<div style="flex: 1.5;">Action</div>'
                    '</div>', unsafe_allow_html=True)

        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)

        phase_labels = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployement", "6": "Support"}
        for _, row in subset.iterrows():
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            c_date, c_empcode, c_empname, c_projcode, c_projname, c_status, c_phase, c_hour, c_action = st.columns([1.5, 1, 2, 1, 3, 1.5, 1.2, 0.8, 1.5])
            r_date = row['date']
            if isinstance(r_date, str): r_date = datetime.datetime.strptime(r_date, '%Y-%m-%d').date()
            c_date.markdown(f'<div class="table-cell date-cell"><b>{r_date.strftime("%d-%m-%Y")}</b></div>', unsafe_allow_html=True)
            c_empcode.markdown(f'<div class="table-cell">{row["emp_id"]}</div>', unsafe_allow_html=True)
            c_empname.markdown(f'<div class="table-cell" title="{row["emp_name"]}">{row["emp_name"]}</div>', unsafe_allow_html=True)
            c_projcode.markdown(f'<div class="table-cell">{row["project_code"] if row["project_code"] else "-"}</div>', unsafe_allow_html=True)
            c_projname.markdown(f'<div class="table-cell" title="{row["project_name"]}">{row["project_name"]}</div>', unsafe_allow_html=True)
            c_status.markdown(f'<div class="table-cell">{row["project_status"]}</div>', unsafe_allow_html=True)
            
            p_val = str(row.get("phase", "1"))
            p_text = phase_labels.get(p_val, p_val)
            c_phase.markdown(f'<div class="table-cell">{p_text}</div>', unsafe_allow_html=True)
            c_hour.markdown(f'<div class="table-cell">{row["hours"]:.2f}</div>', unsafe_allow_html=True)
            
            with c_action:
                if start_of_week <= r_date <= end_of_week:
                    ce, cd = st.columns(2)
                    if ce.button("✏️", key=f"edit_{row['id']}"): edit_form_dialog(row.to_dict(), emp_labels, current_emp_id, user["role"])
                    if cd.button("🗑️", key=f"del_{row['id']}"):
                        delete_timesheet_entry(row['id'])
                        st.rerun()
                else: st.markdown('<div style="text-align: center; color: #94a3b8;">🔒</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pagination Controls — aligned under the Action column
        # Table cols: [1.5, 2, 3, 2, 1.5, 1, 1.5] — action col starts at ratio 12 of 13.5
        p_left, p_prev, p1, p2, p3, p4, p5, p_next = st.columns([12, 0.6, 0.3, 0.3, 0.3, 0.3, 0.3, 0.3])
        if p_prev.button("◀", key="pg_prev", disabled=(st.session_state.page_num == 1)):
            st.session_state.page_num -= 1
            st.rerun()
        page_btns = [p1, p2, p3, p4, p5]
        for i in range(min(5, total_pages)):
            if page_btns[i].button(str(i+1), key=f"pg_{i+1}", type="primary" if st.session_state.page_num == i+1 else "secondary"):
                st.session_state.page_num = i+1
                st.rerun()
        if p_next.button("▶", key="pg_next", disabled=(st.session_state.page_num == total_pages)):
            st.session_state.page_num += 1
            st.rerun()
    else: st.info("no result")
