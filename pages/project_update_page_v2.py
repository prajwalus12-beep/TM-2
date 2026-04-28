"""Project Update 2 — React-based Project Attributes page."""
import streamlit as st
import pandas as pd
import io
import datetime
from database.queries import get_project_reports, save_project_updates
from components.project_update_react import project_update_component


def _generate_excel_buffer(df):
    """Generate an Excel buffer for the given DataFrame."""
    export_cols_map = {
        'project_code': 'Job No',
        'priority': 'Job Priority',
        'project_name': 'Project',
        'status': 'Status',
        'lead_engineer': 'Lead engineer',
        'trello_link': 'Trello',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'phase': 'Phase',
        'prototype_link': 'Prototype'
    }
    clean_df = df.copy()
    
    # Format 'priority' for export (e.g. 1.0 -> 1)
    if 'priority' in clean_df.columns:
        def _fmt_priority(v):
            if pd.isna(v): return v
            try:
                f_val = float(v)
                if f_val == int(f_val):
                    return int(f_val)
                return f_val
            except (ValueError, TypeError):
                return v
        clean_df['priority'] = clean_df['priority'].apply(_fmt_priority)

    clean_df = clean_df.rename(columns=export_cols_map)
    export_cols = [c for c in export_cols_map.values() if c in clean_df.columns]

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        clean_df[export_cols].to_excel(writer, index=False)
    
    return buffer.getvalue()


@st.dialog("Export Data")
def export_dialog(df):
    """Streamlit dialog to handle exporting projects."""
    st.write("Select which records you would like to export:")
    st.write("") # Spacing
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export All")
        st.caption(f"Export all {len(df)} projects")
        buffer_all = _generate_excel_buffer(df)
        st.download_button(
            "📥 Download All",
            data=buffer_all,
            file_name=f"projects_all_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col2:
        st.markdown("#### Export Updated Only")
        # Find updated records based on _updated boolean columns
        updated_cols = [c for c in df.columns if c.endswith('_updated')]
        if updated_cols:
            updated_mask = df[updated_cols].any(axis=1)
            updated_df = df[updated_mask]
        else:
            updated_df = pd.DataFrame(columns=df.columns)
            
        st.caption(f"Export only the {len(updated_df)} modified projects")
        
        # If there are no updated records, disable the button
        buffer_updated = _generate_excel_buffer(updated_df) if not updated_df.empty else b""
        st.download_button(
            "📥 Download Updated",
            data=buffer_updated,
            file_name=f"projects_updated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=updated_df.empty,
            use_container_width=True
        )


def render_project_update_page_v2():
    """Render the React-based Project Update page."""
    st.subheader("Project Update", divider="blue")

    # Fetch data from Supabase
    df = get_project_reports()

    if df.empty:
        st.info("No projects found in project_reports. Please upload via 'Import Data' → 'Update Projects'.")
        return

    # Prepare data for the React component
    # Convert DataFrame to list of dicts, handling NaN/NaT
    projects_list = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                record[col] = None
            elif hasattr(val, 'isoformat'):
                record[col] = val.isoformat() if val is not None else None
            elif isinstance(val, bool):
                record[col] = val
            else:
                # Format Priority to remove .0 from whole numbers (e.g. 1.0 -> 1)
                if col == 'priority' and val is not None:
                    try:
                        f_val = float(val)
                        if f_val == int(f_val):
                            record[col] = str(int(f_val))
                        else:
                            record[col] = str(val)
                    except (ValueError, TypeError):
                        record[col] = str(val)
                else:
                    record[col] = str(val) if val is not None else None
        projects_list.append(record)

    # Extract unique lead engineers
    lead_engineers = sorted(set(
        str(e) for e in df['lead_engineer'].dropna().unique() if str(e).strip()
    ))

    # Render the React component (height scales with content)
    result = project_update_component(
        projects=projects_list,
        lead_engineers=lead_engineers,
        key=f"pu_react_{st.session_state.get('pu_react_refresh', 0)}"
    )

    # Handle actions from the React component
    if result is not None:
        action = result.get("action")

        if action == "save":
            edits = result.get("edits", {})
            if edits:
                # Convert React edits format to the format expected by save_project_updates
                # React sends: {"project_code": {"field": "new_value", ...}}
                # save_project_updates expects: {row_idx: {"field": "new_value", ...}}
                edited_rows = {}
                for proj_code, changes in edits.items():
                    # Find row index in the DataFrame
                    matching = df[df['project_code'] == proj_code]
                    if not matching.empty:
                        row_idx = matching.index[0]
                        # Build the update payload with _updated flags
                        update = {}
                        for col, new_val in changes.items():
                            update[col] = new_val
                            flag_col = f"{col}_updated"
                            if flag_col in df.columns:
                                update[flag_col] = True
                        edited_rows[str(row_idx)] = update

                if edited_rows:
                    # Build a proper current_df for save_project_updates
                    # Reset index to use positional indexing
                    current_df = df.reset_index(drop=True)
                    
                    # Directly update via Supabase
                    from database.connection import get_supabase_client
                    supabase = get_supabase_client()
                    
                    save_count = 0
                    for proj_code, changes in edits.items():
                        update_payload = {}
                        for col, new_val in changes.items():
                            update_payload[col] = new_val
                            flag_col = f"{col}_updated"
                            if flag_col in current_df.columns:
                                update_payload[flag_col] = True
                        
                        if update_payload:
                            try:
                                supabase.table('project_reports').update(update_payload).eq('project_code', proj_code).execute()
                                save_count += 1
                            except Exception as e:
                                st.error(f"Error saving project {proj_code}: {e}")
                    
                    if save_count > 0:
                        st.success(f"✅ Successfully saved {save_count} project(s).")
                        # Refresh key to reload component with new data
                        st.session_state['pu_react_refresh'] = st.session_state.get('pu_react_refresh', 0) + 1
                        st.rerun()

        elif action == "open_export_modal":
            export_dialog(df)
