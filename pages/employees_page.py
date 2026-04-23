import streamlit as st
from database.queries import get_all_users
from services.auth_service import decrypt_data

def render_employees_page(user):
    st.subheader("Employees", divider="blue")
    st.write("### 👥 Employee List")
    users = get_all_users()
    if not users.empty:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><div style="flex: 2;">Username</div><div style="flex: 3;">Employee Name</div><div style="flex: 3;">Slack ID</div><div style="flex: 3;">Password</div></div>', unsafe_allow_html=True)
        for _, row in users.iterrows():
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            c1, c2, c_slack, c3 = st.columns([2, 3, 3, 3])
            c1.markdown(f'<div class="table-cell">{row["username"]}</div>', unsafe_allow_html=True)
            c2.markdown(f'<div class="table-cell"><b>{row["employee_name"] if row["employee_name"] else "N/A"}</b></div>', unsafe_allow_html=True)
            c_slack.markdown(f'<div class="table-cell">{row["slack_id"] if row["slack_id"] else "-"}</div>', unsafe_allow_html=True)
            
            # Show password to admin/system administrator
            is_admin = user["role"] == "admin" or user["username"] == "admin"
            stored_pw = row["password"]
            # Attempt decryption (only works if Fernet-encrypted, not bcrypt hashed)
            pw_display = decrypt_data(stored_pw) if is_admin else "HIDDEN"
            c3.markdown(f'<div class="table-cell"><code>{pw_display}</code></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.info("No employees found.")
