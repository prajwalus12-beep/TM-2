import streamlit as st
from services.auth_service import logout_user
from components.dialogs import update_password_dialog

def render_navbar(user):
    col_brand, col_nav, col_user = st.columns([1.5, 7.5, 1])
    
    with col_brand:
        st.markdown("### ⏱️ TimeTrack")
        
    with col_nav:
        nav_cols = st.columns(5)
        pages = ["Timesheet Entries", "Projects"]
        if user["role"] == "admin":
            pages.extend(["Employees", "Reports", "Import Data"])
            
        for i, page_name in enumerate(pages):
            btn_label = page_name.replace(" Entries", "")
            if nav_cols[i].button(btn_label, use_container_width=True, 
                                 type="primary" if st.session_state["page"] == page_name else "secondary",
                                 key=f"nav_{page_name}"):
                st.session_state["page"] = page_name
                st.rerun()
                 
    with col_user:
        with st.popover("👤", use_container_width=True):
            st.markdown(f"**{user['username'].title()}**")
            if st.button("Update Password", use_container_width=True):
                update_password_dialog(user["username"])
            if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
                logout_user()
    st.markdown("---")
