import streamlit as st
import random
import time
from database.queries import get_all_users
from services.auth_service import login_user, create_session_token


def _new_captcha():
    """Generate a new CAPTCHA code and store in session state."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(random.choices(chars, k=6))
    st.session_state.captcha_code = code


def _render_captcha_text(code: str):
    """Render the CAPTCHA code as styled HTML text."""
    # Generate random colors for each character
    colored_chars = ""
    for ch in code:
        r = random.randint(30, 150)
        g = random.randint(30, 150)
        b = random.randint(30, 150)
        rotation = random.randint(-12, 12)
        size = random.randint(28, 36)
        colored_chars += (
            f'<span style="color:rgb({r},{g},{b}); '
            f'display:inline-block; transform:rotate({rotation}deg); '
            f'font-size:{size}px; font-weight:bold; '
            f'margin:0 2px;">{ch}</span>'
        )

    captcha_html = f"""
    <div style="
        background: linear-gradient(135deg, #e8e8e8 25%, #f5f5f5 50%, #e0e0e0 75%);
        border: 2px solid #bbb;
        border-radius: 8px;
        padding: 14px 20px;
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
        letter-spacing: 10px;
        user-select: none;
        position: relative;
        overflow: hidden;
    ">
        <div style="
            position: absolute; top: 50%; left: 0; right: 0;
            border-top: 2px solid rgba(150,150,150,0.4);
            transform: rotate(-3deg);
        "></div>
        <div style="
            position: absolute; top: 35%; left: 0; right: 0;
            border-top: 1px dashed rgba(120,120,120,0.3);
            transform: rotate(2deg);
        "></div>
        {colored_chars}
    </div>
    """
    st.markdown(captcha_html, unsafe_allow_html=True)


def render_login_page():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>Timesheet Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Login to manage time entries</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            all_users = get_all_users()
            username_list = ["Select Username"] + (all_users['username'].tolist() if not all_users.empty else ["admin"])

            def on_user_change():
                if "login_password" in st.session_state:
                    st.session_state["login_password"] = ""

            def format_username(uname):
                if uname == "Select Username":
                    return uname
                return uname.title()

            username = st.selectbox(
                "Username", 
                username_list, 
                format_func=format_username,
                on_change=on_user_change
            )

            # --- Text CAPTCHA ---
            if "captcha_code" not in st.session_state:
                _new_captcha()

            cap_col1, cap_col2 = st.columns([4, 1])
            with cap_col1:
                _render_captcha_text(st.session_state.captcha_code)
            with cap_col2:
                if st.button("🔄", help="Refresh Captcha", key="refresh_captcha"):
                    _new_captcha()
                    st.rerun()

            captcha_input = st.text_input("Enter Captcha", placeholder="6-digit code")

            with st.form("login_form", border=False):
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    if username == "Select Username":
                        st.error("Please select a username.")
                    elif captcha_input.upper() != st.session_state.captcha_code:
                        st.error("Invalid Captcha.")
                        _new_captcha()
                        time.sleep(2)
                        st.rerun()
                    else:
                        res = login_user(username, password)
                        if "error" in res:
                            _new_captcha()
                            err_placeholder = st.empty()
                            err_placeholder.error(res["error"])
                            time.sleep(8)
                            err_placeholder.empty()
                            st.rerun()
                        else:
                            st.session_state["logged_in"] = True
                            st.session_state["user"] = res
                            # Persist session token for browser refresh
                            token = create_session_token(res)
                            if token:
                                st.query_params["session"] = token
                            if "captcha_code" in st.session_state:
                                del st.session_state["captcha_code"]
                            st.success("Login Successful!")
                            time.sleep(1)
                            st.rerun()
