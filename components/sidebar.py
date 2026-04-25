import streamlit as st
from services.auth_service import logout_user
from components.dialogs import update_password_dialog


def render_sidebar(user):
    """Render sidebar navigation with styled radio items and bottom user card."""

    # --- Sidebar custom CSS ---
    st.sidebar.markdown("""
    <style>
    /* Brand header */
    .sidebar-brand {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 18px 8px 20px 8px;
    }
    .sidebar-brand-icon {
        width: 44px; height: 44px;
        background: #2563EB;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 22px; color: white; flex-shrink: 0;
    }
    .sidebar-brand-text {
        font-size: 22px; font-weight: 700; color: var(--text-color);
    }

    /* Style radio buttons as nav items */
    [data-testid="stSidebar"] .stRadio {
        padding: 0 !important;
        margin-left: -1.5rem !important;
        margin-right: -1.5rem !important;
    }
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0px !important;
        padding: 0 !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label {
        display: flex !important;
        align-items: center !important;
        padding: 12px 1.5rem !important;
        margin: 0 !important;
        border-radius: 0 10px 10px 0 !important;
        cursor: pointer !important;
        font-size: 15px !important;
        font-weight: 500 !important;
        color: var(--text-color) !important;
        opacity: 0.9;
        background: transparent !important;
        border: none !important;
        transition: background 0.15s !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label > div[data-testid="stMarkdownContainer"] p {
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label > div {
        width: 100% !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(128, 128, 128, 0.1) !important;
    }
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"],
    [data-testid="stSidebar"] .stRadio > div > label:has(input:checked) {
        background: rgba(37, 99, 235, 0.1) !important;
        color: #2563EB !important;
        font-weight: 600 !important;
        opacity: 1;
        border-left: 3px solid #2563EB !important;
    }
    /* Hide radio circle */
    [data-testid="stSidebar"] .stRadio > div > label > div:first-child {
        display: none !important;
    }
    /* Hide radio label header */
    [data-testid="stSidebar"] .stRadio > label {
        display: none !important;
    }

    /* User card */
    .user-card-container {
        background: rgba(128, 128, 128, 0.05);
        border-radius: 12px;
        padding: 14px 12px;
        margin: 8px 0 10px 0;
        display: flex; align-items: center; gap: 12px;
    }
    .user-avatar {
        width: 40px; height: 40px;
        background: #2563EB;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        color: white; font-weight: 700; font-size: 14px;
        flex-shrink: 0;
    }
    .user-info { line-height: 1.3; }
    .user-name { font-weight: 600; font-size: 14px; color: var(--text-color); }
    .user-role { font-size: 12px; color: var(--text-color); opacity: 0.7; }

    /* Style the popover for profile card */
    [data-testid="stSidebar"] [data-testid="stPopover"] > button {
        background: rgba(128, 128, 128, 0.05) !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0 !important;
        width: 100% !important;
    }
    [data-testid="stSidebar"] [data-testid="stPopover"] > button:hover {
        background: rgba(128, 128, 128, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        # --- Brand ---
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-icon">🕐</div>
            <div class="sidebar-brand-text">Timesheet</div>
        </div>
        """, unsafe_allow_html=True)

        # --- Navigation Menu using radio ---
        if user["role"] == "admin":
            options = ["📋  Timesheet", "🏢  Project", "📝  Project Update", "👥  Employee", "📊  Report", "📥  Import"]
        else:
            options = ["📋  Timesheet", "🏢  Project", "📝  Project Update"]

        page_map = {
            "📋  Timesheet": "Timesheet Entries",
            "🏢  Project": "Projects",
            "📝  Project Update": "Project Update",
            "👥  Employee": "Employees",
            "📊  Report": "Reports",
            "📥  Import": "Import Data",
        }
        reverse_map = {v: k for k, v in page_map.items()}

        current_page = st.session_state.get("page", "Timesheet Entries")
        default_idx = options.index(reverse_map.get(current_page, options[0])) if reverse_map.get(current_page) in options else 0

        selected = st.radio(
            "Navigation",
            options,
            index=default_idx,
            key="sidebar_nav_radio",
            label_visibility="collapsed",
        )

        # Update page on selection change
        new_page = page_map.get(selected, "Timesheet Entries")
        if new_page != current_page:
            st.session_state["page"] = new_page
            st.rerun()

        # --- Spacer ---
        st.markdown("<div style='min-height: 40px;'></div>", unsafe_allow_html=True)

        # --- User card with popover for Password/Logout ---
        username = user["username"]
        initials = username[:2].upper()
        role_label = "System Admin" if user["role"] == "admin" else "Employee"
        display_name = username.title()

        with st.popover(f"""**{display_name}**  \n{role_label}""", use_container_width=True):
            if st.button("⚙️  Change Password", use_container_width=True, key="sidebar_update_pwd"):
                update_password_dialog(user["username"])
            if st.button("🚪  Logout", use_container_width=True, key="sidebar_logout", type="secondary"):
                logout_user()
