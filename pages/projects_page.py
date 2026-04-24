import streamlit as st
import datetime
import pandas as pd
import io
from database.queries import get_all_projects, save_project_update, get_reported_updates, normalize_code, get_all_employees

@st.dialog("Export Project Data")
def export_dialog(df_all, df_updated):
    st.write("Choose the export type for your project records:")
    st.write("")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 All Records")
        st.caption(f"Includes all {len(df_all)} projects in the current filtered view.")
        buffer_all = io.BytesIO()
        df_all_export = df_all.copy()
        df_all_export.to_csv(buffer_all, index=False)
        st.download_button(
            label="Download Full CSV",
            data=buffer_all.getvalue(),
            file_name=f"projects_all_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="export_all_btn",
            type="primary"
        )
        
    with col2:
        st.markdown("### 📝 Changes Only")
        st.caption(f"Includes only the {len(df_updated)} projects with recent modifications.")
        buffer_upd = io.BytesIO()
        df_updated_export = df_updated.copy()
        df_updated_export.to_csv(buffer_upd, index=False)
        st.download_button(
            label="Download Updates",
            data=buffer_upd.getvalue(),
            file_name=f"projects_updated_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv",
            mime="text/csv",
            use_container_width=True,
            disabled=len(df_updated) == 0,
            key="export_upd_btn",
            type="secondary"
        )

def render_projects_page():
    projs = get_all_projects()
    if projs.empty:
        st.info("No projects found.")
        return

    # Clean priority
    if 'priority' in projs.columns:
        def _clean_pri(p):
            s = str(p)
            if s == "nan" or s == "None": return ""
            if s.endswith(".0"): return s[:-2]
            return s
        projs['priority'] = projs['priority'].apply(_clean_pri)

    # 1. Get current filter state
    search_query = st.session_state.get("proj_search", "")
    min_code = st.session_state.get("proj_min", "")
    max_code = st.session_state.get("proj_max", "")
    emp_filter = st.session_state.get("proj_lead", "All Engineers")
    pri_filter = st.session_state.get("proj_pri", "")
    phase_filter = st.session_state.get("proj_phase", "All Phases")
    stat_filter = st.session_state.get("proj_stat", "All Statuses")

    # 2. Filtering Logic
    filtered = projs.copy()
    if search_query:
        q = search_query.lower()
        mask = filtered['project_name'].astype(str).str.lower().str.contains(q)
        filtered = filtered[mask]
        
    if min_code or max_code:
        filtered['job_no_num_tmp'] = pd.to_numeric(filtered['project_code'], errors='coerce')
        if min_code.strip().isdigit():
            filtered = filtered[filtered['job_no_num_tmp'] >= int(min_code)]
        if max_code.strip().isdigit():
            filtered = filtered[filtered['job_no_num_tmp'] <= int(max_code)]
        filtered = filtered.drop(columns=['job_no_num_tmp'], errors='ignore')

    if emp_filter != "All Engineers":
        filtered = filtered[filtered['lead_engineer'].astype(str) == emp_filter]
        
    if pri_filter:
        pris = [p.strip().lower() for p in pri_filter.split(",") if p.strip()]
        if pris:
            mask = filtered['priority'].astype(str).str.lower().isin(pris)
            filtered = filtered[mask]
            
    if phase_filter != "All Phases" and 'phase' in filtered.columns:
        filtered = filtered[filtered['phase'].astype(str) == phase_filter]
        
    if stat_filter != "All Statuses":
        filtered = filtered[filtered['status'].astype(str) == stat_filter]

    filtered['job_no_numeric'] = pd.to_numeric(filtered['project_code'], errors='coerce')
    filtered = filtered.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False]).drop(columns=['job_no_numeric'])

    # Get reported updates from DB for persistent highlighting across sessions
    reported_updates = get_reported_updates()
    reported_codes = set(reported_updates.keys())

    # 3. Top Header
    header_col1, header_col2 = st.columns([2, 1])
    
    with header_col1:
        st.markdown("<h2 style='margin-bottom: 0px;'>Project Attributes</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 14px; color: #666; margin-top: 5px;'>Showing {len(filtered)} of {len(projs)} projects</p>", unsafe_allow_html=True)
    
    with header_col2:
        st.write("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("📥 Export", type="primary", use_container_width=True, help="Export project data to CSV"):
                st.session_state.trigger_export = True
        
        editor_key = f"proj_editor_{st.session_state.get('editor_key_counter', 0)}"
        has_edits = False
        if editor_key in st.session_state and st.session_state[editor_key].get("edited_rows"):
            has_edits = True
            
        with btn_col2:
            if st.button("💾 Save", type="secondary", use_container_width=True, disabled=not has_edits, help="Save changes to the database"):
                st.session_state.trigger_save = True

    # Handle Save Trigger
    if st.session_state.get("trigger_save"):
        st.session_state.trigger_save = False
        edits = st.session_state[editor_key].get("edited_rows", {})
        
        # Map row IDs to project codes using the filtered dataframe's index
        # display_df uses project_code as index, so we can resolve them.
        mapping_df = filtered.copy().set_index('project_code', drop=False)
        
        success_count = 0
        for row_id, updates in edits.items():
            try:
                # If row_id is an integer index (as string), get the project code from that position
                if str(row_id).isdigit() and row_id not in mapping_df.index:
                    actual_code = mapping_df.index[int(row_id)]
                else:
                    actual_code = row_id
                
                # Convert "None" string back to None for the database
                if updates.get('lead_engineer') == "None":
                    updates['lead_engineer'] = None
                
                success, msg = save_project_update(str(actual_code), updates)
                if success: success_count += 1
                else: st.error(f"Error saving {actual_code}: {msg}")
            except Exception as e:
                st.error(f"Error resolving project for row {row_id}: {e}")
            
        if success_count > 0:
            st.success(f"Successfully saved {success_count} project updates!")
            # Add saved codes to persistent session state for highlighting
            if "saved_codes" not in st.session_state:
                st.session_state.saved_codes = set()
            for row_id in edits.keys():
                try:
                    if str(row_id).isdigit() and row_id not in mapping_df.index:
                        st.session_state.saved_codes.add(str(mapping_df.index[int(row_id)]))
                    else:
                        st.session_state.saved_codes.add(str(row_id))
                except: pass
            
            # Increment counter to refresh editor, but the red will persist via saved_codes
            st.session_state.editor_key_counter = st.session_state.get('editor_key_counter', 0) + 1
            st.rerun()

    st.write("") # spacing

    # 4. Filters UI
    with st.container(border=True):
        st.markdown("##### ♈ Filters")
        col_name, col_range, col_emp, col_pri, col_phase, col_stat, col_clear = st.columns([2, 2, 2, 1.5, 1.5, 1.5, 1])
        with col_name:
            st.text_input("PROJECT NAME", placeholder="e.g. Alpha Search...", key="proj_search")
        with col_range:
            st.markdown("<div style='font-size: 14px; margin-bottom: 4px; font-weight: 500; color: #31333F;'>PROJECT CODE RANGE</div>", unsafe_allow_html=True)
            r1, r_dash, r2 = st.columns([1, 0.2, 1])
            with r1: st.text_input("Min", placeholder="Min", label_visibility="collapsed", key="proj_min")
            with r_dash: st.markdown("<div style='text-align: center; margin-top: 5px;'>-</div>", unsafe_allow_html=True)
            with r2: st.text_input("Max", placeholder="Max", label_visibility="collapsed", key="proj_max")
        with col_emp:
            emps = ["All Engineers"] + sorted([str(e) for e in projs['lead_engineer'].dropna().unique() if str(e).strip()])
            st.selectbox("LEAD ENGINEER", emps, key="proj_lead")
        with col_pri:
            st.text_input("PRIORITY", placeholder="E.G. P1, P10", key="proj_pri")
        with col_phase:
            phases = ["All Phases"] + sorted([str(s) for s in projs['phase'].dropna().unique() if str(s).strip()] if 'phase' in projs.columns else [])
            st.selectbox("PHASE", phases, key="proj_phase")
        with col_stat:
            statuses = ["All Statuses"] + sorted([str(s) for s in projs['status'].dropna().unique() if str(s).strip()])
            st.selectbox("STATUS", statuses, key="proj_stat")
            
        def clear_filters():
            st.session_state.proj_search = ""
            st.session_state.proj_min = ""
            st.session_state.proj_max = ""
            st.session_state.proj_lead = "All Engineers"
            st.session_state.proj_pri = ""
            st.session_state.proj_phase = "All Phases"
            st.session_state.proj_stat = "All Statuses"
            st.session_state.saved_codes = set() # Clear saved highlights too
            
        with col_clear:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("Clear", on_click=clear_filters, use_container_width=True)
    
    # 5. Table
    if not filtered.empty:
        # Get all employees for lead engineer dropdown
        all_emps_df = get_all_employees(exclude_admin=True)
        employee_names = ["None"] + sorted([str(e).strip() for e in all_emps_df['employee_name'].dropna().unique() if str(e).strip()])
        
        display_df = filtered.copy().set_index('project_code', drop=False)
        display_df['lead_engineer'] = display_df['lead_engineer'].apply(lambda x: str(x).strip() if x and str(x).strip() else "None")
        
        column_order = [
            "project_code", "project_name", "lead_engineer", "priority", 
            "start_date", "end_date", "status", "phase", "trello_link", "prototype_link"
        ]
        for col in column_order:
            if col not in display_df.columns: display_df[col] = None
            
        # Convert date columns to date objects for st.data_editor compatibility
        for col in ["start_date", "end_date"]:
            display_df[col] = pd.to_datetime(display_df[col], errors='coerce').dt.date

        # Track edits AND saved updates for highlighting
        highlight_codes = set()
        if editor_key in st.session_state:
            highlight_codes.update(st.session_state[editor_key].get("edited_rows", {}).keys())
        
        # Add historically saved codes from this session
        saved_codes = st.session_state.get("saved_codes", set())
            
        def highlight_row(row):
            styles = [''] * len(row)
            p_code = normalize_code(row.name)
            
            # 1. Check for unsaved edits in session state
            unsaved_cols = set()
            if editor_key in st.session_state:
                edits_dict = st.session_state[editor_key].get("edited_rows", {})
                
                # Check directly and also check normalized keys
                if p_code in edits_dict:
                    unsaved_cols = set(edits_dict[p_code].keys())
                else:
                    for k, updates in edits_dict.items():
                        if normalize_code(k) == p_code:
                            unsaved_cols = set(updates.keys())
                            break

            # 2. Check for historically saved codes in this session
            is_saved = any(normalize_code(sc) == p_code for sc in saved_codes)
            
            # 3. Check for reported updates in DB
            db_updated_cols = reported_updates.get(p_code, set())
            
            # Highlighting style
            highlight_style = 'color: #d32f2f; background-color: #ffebee'
            
            for i, col_name in enumerate(row.index):
                # Highlight if:
                # - This cell has unsaved edits
                # - This cell has a reported update in DB
                # - The row was just saved (highlight Project Name for visibility, but NOT Job No)
                if (col_name in unsaved_cols or 
                    col_name in db_updated_cols or 
                    (is_saved and col_name != 'project_code')):
                    styles[i] = highlight_style
            
            return styles
            
        styled_df = display_df.style.apply(highlight_row, axis=1)

        edited_df = st.data_editor(
            styled_df,
            key=editor_key,
            use_container_width=True,
            num_rows="fixed",
            disabled=["project_code"],
            column_order=column_order,
            column_config={
                "project_code": st.column_config.TextColumn("JOB NO"),
                "project_name": st.column_config.TextColumn("PROJECT NAME"),
                "lead_engineer": st.column_config.SelectboxColumn("LEAD ENGINEER", options=employee_names),
                "priority": st.column_config.TextColumn("PRIORITY"),
                "start_date": st.column_config.DateColumn("START DATE", format="DD-MM-YYYY"),
                "end_date": st.column_config.DateColumn("END DATE", format="DD-MM-YYYY"),
                "status": st.column_config.SelectboxColumn("STATUS", options=["Not started", "In progress", "Complete", "On hold"]),
                "phase": st.column_config.SelectboxColumn("PHASE", options=["Analysis", "Design", "Development", "Testing", "Deployment", "Support"]),
                "trello_link": st.column_config.LinkColumn("TRELLO"),
                "prototype_link": st.column_config.LinkColumn("PROTOTYPE")
            }
        )
        
        # Handle Export Dialog Trigger
        if st.session_state.get("trigger_export"):
            st.session_state.trigger_export = False
            
            # Identify all projects that are highlighted (edited, saved, or reported)
            all_red_ids = highlight_codes | saved_codes | reported_codes
            resolved_red_codes = set()
            for rid in all_red_ids:
                if str(rid).isdigit() and rid not in edited_df.index:
                    try: resolved_red_codes.add(edited_df.index[int(rid)])
                    except: pass
                else:
                    resolved_red_codes.add(rid)
            
            upd_df = edited_df[edited_df.index.isin(resolved_red_codes)]
            export_dialog(edited_df, upd_df)
                
    else:
        st.info("No matching projects found.")
