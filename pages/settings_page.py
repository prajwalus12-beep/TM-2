import streamlit as st
import pandas as pd
from database.queries import get_all_users, update_project_update_access

def render_settings_page():
    """Render the administrative settings page for access control."""
    st.subheader("System Settings", divider="blue")
    
    st.write("### Module Access Control")
    st.caption("Manage which employees have access to the Project Update module.")

    # Fetch all users with their current project update access
    users_df = get_all_users()
    
    if users_df.empty:
        st.info("No users found to manage.")
        return

    # Filter out admin (admin always has access, no need to toggle)
    manageable_users = users_df[users_df['username'] != 'admin'].copy()
    
    if manageable_users.empty:
        st.info("No non-admin users found to manage.")
        return

    # Display users in a clean list with toggles
    st.markdown("""
    <style>
    .settings-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: rgba(128, 128, 128, 0.05);
        border-radius: 8px;
        margin-bottom: 8px;
    }
    .user-details {
        display: flex;
        flex-direction: column;
    }
    .user-name {
        font-weight: 600;
        font-size: 15px;
    }
    .user-username {
        font-size: 13px;
        opacity: 0.7;
    }
    </style>
    """, unsafe_allow_html=True)

    changes_made = False
    
    for idx, row in manageable_users.iterrows():
        col1, col2 = st.columns([4, 1])
        
        with col1:
            st.markdown(f"""
            <div class="user-details">
                <div class="user-name">{row['employee_name']}</div>
                <div class="user-username">@{row['username']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            current_access = bool(row['project_update_access'])
            # Using key with employee_id to ensure state management is correct
            new_access = st.toggle(
                "Access", 
                value=current_access, 
                key=f"access_{row['employee_id']}",
                label_visibility="collapsed"
            )
            
            if new_access != current_access:
                success, msg = update_project_update_access(row['employee_id'], new_access)
                if success:
                    st.toast(f"✅ Access updated for {row['employee_name']}", icon="🔒")
                    changes_made = True
                else:
                    st.error(f"Error: {msg}")

    if changes_made:
        # Note: In a real app we might want to force a refresh of the user's session if they are logged in.
        # For now, this updates the DB immediately.
        pass

    st.divider()
    st.info("💡 **Tip:** Administrators always have full access to all modules and cannot be restricted.")
