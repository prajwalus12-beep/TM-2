import streamlit as st
import datetime
import pandas as pd
import io
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from database.queries import get_all_projects, save_project_update, get_reported_updates, normalize_code, get_all_employees

STATUS_OPTIONS = ["Not started", "In progress", "Complete", "On hold", "Cancelled"]
STATUS_COLOR_MAP = {
    "In progress": "#2563eb",
    "Complete": "#16a34a",
    "On hold": "#f59e0b",
    "Cancelled": "#dc2626",
}
EDITABLE_COLUMNS = [
    "project_name", "lead_engineer", "priority", "start_date", "end_date",
    "status", "phase", "trello_link", "prototype_link"
]


def _normalize_compare_value(value):
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, (datetime.date, datetime.datetime, pd.Timestamp)):
        return value.strftime("%Y-%m-%d")
    text = str(value).strip()
    if text in {"None", "nan", "NaT"}:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    if len(text) >= 10 and text[4] == "-" and text[7] == "-":
        return text[:10]
    return text


def _normalize_for_save(column, value):
    normalized = _normalize_compare_value(value)
    if not normalized:
        return None if column != "project_name" else ""
    if column == "lead_engineer" and normalized == "None":
        return None
    return normalized


def _collect_project_edits(current_df, original_df):
    original_lookup = original_df.set_index("project_code", drop=False)
    edits = {}

    for _, row in current_df.iterrows():
        project_code = str(row["project_code"])
        if project_code not in original_lookup.index:
            continue

        original_row = original_lookup.loc[project_code]
        updates = {}
        for col in EDITABLE_COLUMNS:
            current_value = _normalize_compare_value(row.get(col))
            original_value = _normalize_compare_value(original_row.get(col))
            if current_value != original_value:
                updates[col] = _normalize_for_save(col, row.get(col))

        if updates:
            edits[project_code] = updates

    return edits

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
        
        with btn_col2:
            if st.button(
                "💾 Save",
                type="secondary",
                use_container_width=True,
                disabled=not st.session_state.get("current_project_edits"),
                help="Save changes to the database"
            ):
                st.session_state.trigger_save = True

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
            st.session_state.saved_project_updates = {}
            st.session_state.current_project_edits = {}
            
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
            
        for col in ["start_date", "end_date"]:
            display_df[col] = pd.to_datetime(display_df[col], errors='coerce').dt.strftime('%Y-%m-%d').fillna("")

        saved_project_updates = st.session_state.get("saved_project_updates", {})
        grid_df = display_df[column_order].reset_index(drop=True).copy()
        grid_df["__db_updated_cols"] = grid_df["project_code"].apply(
            lambda code: ",".join(sorted(reported_updates.get(normalize_code(code), set())))
        )
        grid_df["__saved_updated_cols"] = grid_df["project_code"].apply(
            lambda code: ",".join(sorted(saved_project_updates.get(str(code), set())))
        )
        for col in EDITABLE_COLUMNS:
            grid_df[f"__orig__{col}"] = grid_df[col]

        cell_style = JsCode(
            """
            function(params) {
                const field = params.colDef.field;
                const normalize = (value) => {
                    if (value === null || value === undefined) return "";
                    let text = String(value).trim();
                    if (text === "None" || text === "nan" || text === "NaT") return "";
                    if (text.endsWith(".0")) text = text.slice(0, -2);
                    if (/^\\d{4}-\\d{2}-\\d{2}T/.test(text)) text = text.slice(0, 10);
                    return text;
                };
                const flaggedCols = (params.data.__db_updated_cols || "").split(",").filter(Boolean);
                const savedCols = (params.data.__saved_updated_cols || "").split(",").filter(Boolean);
                const originalValue = normalize(params.data["__orig__" + field]);
                const currentValue = normalize(params.value);
                const isChanged = originalValue !== currentValue;
                const isFlagged = flaggedCols.includes(field) || savedCols.includes(field);

                if (isChanged || isFlagged) {
                    return {
                        color: "#b91c1c",
                        backgroundColor: "#fee2e2",
                        fontWeight: "700"
                    };
                }

                if (field === "status") {
                    const colorMap = {
                        "In progress": "#2563eb",
                        "Complete": "#16a34a",
                        "On hold": "#f59e0b",
                        "Cancelled": "#dc2626"
                    };
                    if (colorMap[currentValue]) {
                        return { color: colorMap[currentValue], fontWeight: "700" };
                    }
                }

                return null;
            }
            """
        )

        gb = GridOptionsBuilder.from_dataframe(grid_df)
        gb.configure_default_column(editable=False, sortable=True, filter=True, resizable=True)
        gb.configure_column("project_code", header_name="JOB NO", editable=False, pinned="left", cellStyle=cell_style)
        gb.configure_column("project_name", header_name="PROJECT NAME", editable=True, cellStyle=cell_style)
        gb.configure_column(
            "lead_engineer",
            header_name="LEAD ENGINEER",
            editable=True,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": employee_names},
            cellStyle=cell_style,
        )
        gb.configure_column("priority", header_name="PRIORITY", editable=True, cellStyle=cell_style)
        gb.configure_column("start_date", header_name="START DATE", editable=True, cellStyle=cell_style)
        gb.configure_column("end_date", header_name="END DATE", editable=True, cellStyle=cell_style)
        gb.configure_column(
            "status",
            header_name="STATUS",
            editable=True,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": STATUS_OPTIONS},
            cellStyle=cell_style,
        )
        gb.configure_column(
            "phase",
            header_name="PHASE",
            editable=True,
            cellEditor="agSelectCellEditor",
            cellEditorParams={"values": ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"]},
            cellStyle=cell_style,
        )
        gb.configure_column("trello_link", header_name="TRELLO", editable=True, cellStyle=cell_style)
        gb.configure_column("prototype_link", header_name="PROTOTYPE", editable=True, cellStyle=cell_style)
        gb.configure_grid_options(rowHeight=38, suppressRowClickSelection=True)
        for helper_col in ["__db_updated_cols", "__saved_updated_cols"] + [f"__orig__{col}" for col in EDITABLE_COLUMNS]:
            gb.configure_column(helper_col, hide=True)

        grid_response = AgGrid(
            grid_df,
            gridOptions=gb.build(),
            data_return_mode=DataReturnMode.AS_INPUT,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True,
            fit_columns_on_grid_load=True,
            height=min(650, 90 + (len(grid_df) * 38)),
            theme="streamlit",
            reload_data=False,
        )

        edited_df = pd.DataFrame(grid_response["data"])[column_order].copy()
        current_project_edits = _collect_project_edits(edited_df, display_df[column_order].reset_index(drop=True))
        st.session_state.current_project_edits = current_project_edits

        if st.session_state.get("trigger_save"):
            st.session_state.trigger_save = False
            success_count = 0
            saved_updates = st.session_state.get("saved_project_updates", {}).copy()

            for project_code, updates in current_project_edits.items():
                success, msg = save_project_update(project_code, updates)
                if success:
                    success_count += 1
                    saved_updates[project_code] = set(updates.keys())
                else:
                    st.error(f"Error saving {project_code}: {msg}")

            st.session_state.saved_project_updates = saved_updates
            st.session_state.current_project_edits = {}

            if success_count > 0:
                st.success(f"Successfully saved {success_count} project updates!")
                st.rerun()
        
        # Handle Export Dialog Trigger
        if st.session_state.get("trigger_export"):
            st.session_state.trigger_export = False
            highlighted_codes = set(current_project_edits.keys()) | set(saved_project_updates.keys()) | set(reported_codes)
            upd_df = edited_df[edited_df["project_code"].astype(str).isin({str(code) for code in highlighted_codes})]
            export_dialog(edited_df, upd_df)
                
    else:
        st.info("No matching projects found.")
