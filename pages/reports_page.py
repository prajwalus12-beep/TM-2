import streamlit as st
import datetime
import pandas as pd
import json
import io

from database.queries import get_all_employees, get_timesheets, get_all_projects
from utils.date_helpers import get_curr_cycle_dates

def render_reports_page(user):
    hdr_col, exp_col = st.columns([6.5, 3.5])
    with hdr_col:
        st.subheader("Timesheet Reports", divider="blue")
        st.caption("Employee timesheet summary and statistics")
    # Handle reset flag BEFORE widgets are instantiated
    if st.session_state.pop('_reset_report_filters', False):
        st.session_state.report_emp = "All Employees"
        st.session_state.report_proj = "All Projects"
        st.session_state.report_date_range_picker = "This Week"
        st.session_state.report_start_date = datetime.date.today() - datetime.timedelta(days=30)
        st.session_state.report_end_date = datetime.date.today()

    exp_btn_placeholder = exp_col.empty()

    # Initialize custom dates if not present
    if 'report_start_date' not in st.session_state:
        st.session_state.report_start_date = datetime.date.today() - datetime.timedelta(days=30)
    if 'report_end_date' not in st.session_state:
        st.session_state.report_end_date = datetime.date.today()

    range_opt = st.session_state.get('report_date_range_picker', 'This Week')
    
    with st.container(border=True):
        # Dynamic ratios to accommodate Custom Range inputs - giving more space to Clear button
        if range_opt == "Custom Range":
            ratios = [1.8, 1.8, 1.8, 3.4, 1.2]
        else:
            ratios = [2.5, 2.5, 2.5, 0.1, 1.2]
        
        c1, c2, c3, c4, c5 = st.columns(ratios)
        
        with c1:
            report_emps = get_all_employees(exclude_admin=True)
            report_emp_options = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in report_emps.iterrows()}
            sel_emp_name = st.selectbox("Employee", ["All Employees"] + list(report_emp_options.keys()), key="report_emp")
            sel_emp_id = report_emp_options[sel_emp_name] if sel_emp_name != "All Employees" else None
        
        with c2:
            all_projs = get_all_projects()
            all_projs['job_no_numeric'] = pd.to_numeric(all_projs['project_code'], errors='coerce')
            all_projs = all_projs.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False])
            
            proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_code'] for _, r in all_projs.iterrows()}
            sel_proj_name = st.selectbox("Project", ["All Projects"] + list(proj_options.keys()), key="report_proj")
            sel_proj_code = proj_options[sel_proj_name] if sel_proj_name != "All Projects" else None
            
        with c3:
            range_opt = st.selectbox("Date Range", ["This Week", "Last Week", "Current 4 Week Cycle", "Previous 4 Week Cycle", "Custom Range"], key="report_date_range_picker")
            today = datetime.date.today()
            start_week = today - datetime.timedelta(days=today.weekday())
            
            if range_opt == "This Week": r_start_calc, r_end_calc = start_week, start_week + datetime.timedelta(days=6)
            elif range_opt == "Last Week": r_start_calc, r_end_calc = start_week - datetime.timedelta(days=7), start_week - datetime.timedelta(days=1)
            elif range_opt == "Current 4 Week Cycle": r_start_calc, r_end_calc = get_curr_cycle_dates(today)
            elif range_opt == "Previous 4 Week Cycle":
                cs, _ = get_curr_cycle_dates(today)
                r_start_calc, r_end_calc = cs - datetime.timedelta(days=28), cs - datetime.timedelta(days=1)
            else:
                r_start_calc, r_end_calc = None, None
        
        with c4:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if range_opt == "Custom Range":
                sub1, sub2 = st.columns(2)
                r_start = sub1.date_input("Start", key="report_start_date")
                r_end = sub2.date_input("End", key="report_end_date")
                if r_end < r_start:
                    st.error("⚠️ End date can't be smaller than start date")
                    st.stop()
            else:
                r_start, r_end = r_start_calc, r_end_calc
        
        with c5:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if st.button("🧹 Clear", key="clear_report_filters_btn", use_container_width=True):
                st.session_state._reset_report_filters = True
                st.rerun()

    all_employees = get_all_employees(exclude_admin=True)
    if sel_emp_id: all_employees = all_employees[all_employees['employee_id'] == sel_emp_id]
    ts_data = get_timesheets(r_start, r_end, sel_emp_id, sel_proj_code)

    if not all_employees.empty:
        num_days = (r_end - r_start).days + 1
        all_dates = [r_start + datetime.timedelta(days=i) for i in range(num_days)]
        day_cols = [d.strftime("%d %a").upper() for d in all_dates]
        
        # Build pivot
        pivot_rows = []
        emp_day_hours = {}
        if not ts_data.empty:
            ts_data['date'] = pd.to_datetime(ts_data['date']).dt.date
            for _, row in ts_data.iterrows():
                eid, d, h = row['emp_id'], row['date'], float(row['hours'])
                if eid not in emp_day_hours: emp_day_hours[eid] = {}
                emp_day_hours[eid][d] = emp_day_hours[eid].get(d, 0) + h

        all_weekdays = [d for d in all_dates if d.weekday() < 5]
        for _, emp in all_employees.iterrows():
            eid, ename = emp['employee_id'], emp['employee_name']
            hours = emp_day_hours.get(eid, {})
            r_dict = {'EMP Id': eid, 'Employee Name': ename}
            wt, df = 0.0, 0
            for d, c_name in zip(all_dates, day_cols):
                h = hours.get(d, 0.0)
                if h > 0:
                    r_dict[c_name] = int(h) if float(h).is_integer() else round(h, 2)
                else:
                    r_dict[c_name] = None
                if d.weekday() < 5:
                    wt += h
                    if h > 0: df += 1
            r_dict['Total Hours'] = int(wt) if float(wt).is_integer() else round(wt, 2)
            r_dict['Status'] = '✅' if len(all_weekdays) > 0 and df == len(all_weekdays) else '❌'
            pivot_rows.append(r_dict)

        df_pivot = pd.DataFrame(pivot_rows, dtype=object)
        
        # Calculate Metrics
        total_emps = len(df_pivot)
        completed_count = len(df_pivot[df_pivot['Status'] == '✅'])
        uncompleted_count = total_emps - completed_count
        total_hours = df_pivot['Total Hours'].sum()

        st.write("### 📊 Summary")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Total Employees", total_emps)
        col_s2.metric("Completed", completed_count)
        col_s3.metric("Uncompleted", uncompleted_count)
        col_s4.metric("Total Hours (Mon-Fri)", f"{total_hours:.1f}h")
        
        st.write("### 📋 Employee Details")
        st.caption(f"Showing records from :blue[**{r_start.strftime('%d-%m-%Y')}**] to :blue[**{r_end.strftime('%d-%m-%Y')}**]")
        def style_table(styler):
            # Row style for uncompleted rows
            def row_style(row):
                if '\u274c' in str(row.get('Status', '')) or '❌' in str(row.get('Status', '')):
                    return ['background-color: #ffe4e6; color: #991b1b'] * len(row)
                return [''] * len(row)
            
            styler = styler.apply(row_style, axis=1)
            
            # Weekend styling
            weekend_cols = [c for c in day_cols if 'SAT' in c or 'SUN' in c]
            def weekend_style(val):
                if pd.notna(val) and val != 0 and str(val).strip() != '':
                    return 'background-color: #fefce8; color: #78350f; font-weight: bold'
                return ''
            
            if weekend_cols:
                styler = styler.map(weekend_style, subset=weekend_cols)
                
            return styler

        styled_df = df_pivot.style.pipe(style_table)
        st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)
        
        
        # Export buttons
        with exp_btn_placeholder.container():
            with st.popover("📥 Export Options", use_container_width=True):
                excel_export = df_pivot.copy()
                if 'Status' in excel_export.columns:
                    excel_export['Status'] = excel_export['Status'].replace({'✅': 'Complete', '❌': 'Incomplete'})
                
                sum_buffer = io.BytesIO()
                with pd.ExcelWriter(sum_buffer, engine='openpyxl') as writer:
                    if not excel_export.empty:
                        excel_export.to_excel(writer, sheet_name='Summary', index=False)
                    else:
                        pd.DataFrame().to_excel(writer, sheet_name='Summary', index=False)
                
                st.download_button(
                    "📊 Export Summary (Excel)", 
                    sum_buffer.getvalue(), 
                    f"report_summary_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True,
                    key="report_excel_summary_download_btn"
                )
                
                # Excel export for Phase Breakdown
                buffer = io.BytesIO()
                if not ts_data.empty:
                    phase_inv_map = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployment", "6": "Support"}
                    df_export = ts_data.copy()
                    df_export['Phase'] = df_export['Phase'].astype(str).map(phase_inv_map).fillna(df_export['Phase'])
                    df_export['hours'] = pd.to_numeric(df_export['hours'], errors='coerce').fillna(0)
                    df_export.rename(columns={'project_name': 'Row Labels', 'Phase': 'Column Labels', 'hours': 'Sum of Hours'}, inplace=True)
                    
                    pivot_export = pd.pivot_table(
                        df_export, 
                        values='Sum of Hours', 
                        index='Row Labels', 
                        columns='Column Labels', 
                        aggfunc='sum', 
                        margins=True, 
                        margins_name='Grand Total'
                    )
                    
                    # Flatten the pivot table layout to make it simple
                    pivot_export = pivot_export.reset_index()
                    pivot_export.columns.name = None
                    
                    # Fill NaN with empty space
                    pivot_export = pivot_export.fillna('')
                    
                    # Remove decimals if whole number
                    def _format_val(v):
                        if isinstance(v, (int, float)) and pd.notna(v):
                            return int(v) if float(v).is_integer() else round(v, 2)
                        return v
                    
                    if hasattr(pivot_export, 'map'):
                        pivot_export = pivot_export.map(_format_val)
                    else:
                        pivot_export = pivot_export.applymap(_format_val)
                    
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        pivot_export.to_excel(writer, sheet_name='Sheet1', index=False)
                        
                        # Remove all bold styling for simple format
                        worksheet = writer.sheets['Sheet1']
                        for row in worksheet.iter_rows():
                            for cell in row:
                                if cell.font and cell.font.bold:
                                    cell.font = cell.font.copy(bold=False)
                else:
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        pd.DataFrame().to_excel(writer)
                
                st.download_button(
                    "📈 Export By Phase (Excel)", 
                    buffer.getvalue(), 
                    f"report_phase_breakdown_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="report_excel_download_btn"
                )

                # JSON Export for Admin: Incomplete Timesheets
                if user["role"] == "admin":
                    incomplete_logs = []
                    
                    for _, emp in all_employees.iterrows():
                        eid, ename, slack_id = emp['employee_id'], emp['employee_name'], emp.get('slack_id', '-')
                        if eid == 'admin': continue
                        
                        emp_hours_map = emp_day_hours.get(eid, {})
                        # Identify all incomplete days (h < 8) in the selected range
                        incomplete_dates = []
                        for d in all_dates:
                            if d.weekday() >= 5: continue # Skip Weekends (Sat=5, Sun=6)
                            h = emp_hours_map.get(d, 0.0)
                            if h < 8.0:
                                incomplete_dates.append(d.strftime('%d-%m-%Y'))
                        
                        if incomplete_dates:
                            dates_str = ", ".join(incomplete_dates)
                            msg = f"Hello {ename}, you have incomplete timesheet entries for following dates: {dates_str}. Please complete your timesheet."
                            
                            incomplete_logs.append({
                                "Slack Id": slack_id,
                                "Message": msg
                            })
                    
                    if incomplete_logs:
                        st.download_button(
                            "📥 Export Incomplete Logs (JSON)", 
                            json.dumps(incomplete_logs, indent=2), 
                            f"incomplete_timesheets_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", 
                            "application/json",
                            use_container_width=True,
                            key="report_json_download_btn"
                        )
    else: st.info("No employees found.")
