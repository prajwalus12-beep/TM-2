import streamlit as st
import datetime
import pandas as pd
import io
from database.queries import get_all_projects

def render_projects_page():
    col_title, col_export = st.columns([7, 1.5])
    with col_title: st.subheader("Projects", divider="blue")
    
    export_placeholder = col_export.empty()
    projs = get_all_projects()
    
    if projs.empty:
        st.info("No projects found.")
        return

    if 'priority' in projs.columns:
        def _clean_pri(p):
            s = str(p)
            if s == "nan" or s == "None": return ""
            if s.endswith(".0"): return s[:-2]
            return s
        projs['priority'] = projs['priority'].apply(_clean_pri)

    with st.container(border=True):
        col_search, col_pri, col_emp, col_stat, col_clear = st.columns([2.5, 1.5, 2, 1.5, 1])
        with col_search:
            search_query = st.text_input("🔍 Search Project Name or Project Code", key="proj_search")
        with col_pri:
            def _sort_pri(x):
                try: return float(x)
                except ValueError: return float('inf')
            raw_pri = [p for p in projs['priority'].dropna().unique() if p.strip()]
            priorities = ["All"] + sorted(raw_pri, key=_sort_pri)
            pri_filter = st.selectbox("Priority", priorities, key="proj_pri")
        with col_emp:
            emps = ["All"] + sorted([str(e) for e in projs['lead_engineer'].dropna().unique() if str(e).strip()])
            emp_filter = st.selectbox("Lead Engineer", emps, key="proj_lead")
        with col_stat:
            statuses = ["All"] + sorted([str(s) for s in projs['status'].dropna().unique() if str(s).strip()])
            stat_filter = st.selectbox("Status", statuses, key="proj_stat")
            
        def clear_filters():
            st.session_state.proj_search = ""
            st.session_state.proj_pri = "All"
            st.session_state.proj_lead = "All"
            st.session_state.proj_stat = "All"
            st.session_state.proj_page_num = 1
            
        with col_clear:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("Clear", on_click=clear_filters, use_container_width=True)
    
    filtered = projs.copy()
    if search_query:
        q = search_query.lower()
        mask = filtered['project_code'].astype(str).str.lower().str.contains(q) | \
               filtered['project_name'].astype(str).str.lower().str.contains(q)
        filtered = filtered[mask]
    if pri_filter != "All":
        filtered = filtered[filtered['priority'].astype(str) == pri_filter]
    if emp_filter != "All":
        filtered = filtered[filtered['lead_engineer'].astype(str) == emp_filter]
    if stat_filter != "All":
        filtered = filtered[filtered['status'].astype(str) == stat_filter]

    # Numeric sorting for Job No
    filtered['job_no_numeric'] = pd.to_numeric(filtered['project_code'], errors='coerce')
    filtered = filtered.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False])
    
    if not filtered.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            export_df = filtered.drop(columns=['job_no_numeric'], errors='ignore')
            export_df = export_df.rename(columns={
                'project_code': 'Project Code',
                'priority': 'Job Priority',
                'project_name': 'Project',
                'status': 'Status',
                'lead_engineer': 'Lead engineer',
                'trello_link': 'Trello'
            })
            export_df = export_df[['Project Code', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello']]
            export_df.to_excel(writer, index=False)
        export_placeholder.download_button("📥 Export Excel", buffer.getvalue(), f"projects_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")

    st.write(f"### 🏗️ Project List ({len(filtered)} projects)")
    if not filtered.empty:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><div style="flex: 1;">Project Code</div><div style="flex: 1;">Priority</div><div style="flex: 3;">Project Name</div><div style="flex: 1.5;">Status</div><div style="flex: 2;">Lead Engineer</div><div style="flex: 2;">Trello Link</div></div>', unsafe_allow_html=True)
        
        # Pagination
        rows_per_page = 15
        total_pages = max(1, (len(filtered) - 1) // rows_per_page + 1)
        if "proj_page_num" not in st.session_state: st.session_state.proj_page_num = 1
        st.session_state.proj_page_num = max(1, min(st.session_state.proj_page_num, total_pages))
        
        start_idx = (st.session_state.proj_page_num - 1) * rows_per_page
        subset = filtered.iloc[start_idx:start_idx + rows_per_page]
        
        for _, row in subset.iterrows():
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            c1, c_pri, c2, c3, c_lead, c_trello = st.columns([1, 1, 3, 1.5, 2, 2])
            c1.markdown(f'<div class="table-cell"><b>{row["project_code"]}</b></div>', unsafe_allow_html=True)
            
            pri_str = str(row.get("priority", ""))
            c_pri.markdown(f'<div class="table-cell">{pri_str}</div>', unsafe_allow_html=True)
            
            p_name = row["project_name"]
            disp = (p_name[:50] + '..') if len(p_name) > 50 else p_name
            c2.markdown(f'<div class="table-cell" title="{p_name}">{disp}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="table-cell">{row.get("status", "") or ""}</div>', unsafe_allow_html=True)
            
            lead_str = str(row.get("lead_engineer", ""))
            if lead_str == "nan" or lead_str == "None": lead_str = ""
            c_lead.markdown(f'<div class="table-cell">{lead_str}</div>', unsafe_allow_html=True)
            
            tlink = str(row.get("trello_link", ""))
            if tlink and tlink != "nan" and tlink != "None":
                c_trello.markdown(f'<div class="table-cell"><a href="{tlink}" target="_blank" style="text-decoration: none;">🔗 Link</a></div>', unsafe_allow_html=True)
            else:
                c_trello.markdown(f'<div class="table-cell"></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if total_pages > 1:
            num_btns = min(5, total_pages)
            st.write("") # Add a little vertical spacing
            # Allocate ratio 1 for buttons, 10 for left spacer, to keep them reasonably sized
            cols = st.columns([10] + [0.8] * (num_btns + 2) + [0.1])
            
            p_prev = cols[1]
            page_btns = cols[2:2+num_btns]
            p_next = cols[2+num_btns]
            
            if p_prev.button("◀", key="p_pg_prev", disabled=(st.session_state.proj_page_num == 1), use_container_width=True):
                st.session_state.proj_page_num -= 1
                st.rerun()
            
            page_window = max(1, min(st.session_state.proj_page_num - num_btns//2, total_pages - num_btns + 1))
            
            for i in range(num_btns):
                pg_idx = page_window + i
                if page_btns[i].button(str(pg_idx), key=f"p_pg_{pg_idx}", type="primary" if st.session_state.proj_page_num == pg_idx else "secondary", use_container_width=True):
                    st.session_state.proj_page_num = pg_idx
                    st.rerun()
                    
            if p_next.button("▶", key="p_pg_next", disabled=(st.session_state.proj_page_num == total_pages), use_container_width=True):
                st.session_state.proj_page_num += 1
                st.rerun()
                
    else: st.info("No matching projects found.")
