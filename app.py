"""
app.py - Main entry point for the Research Information Collection Portal
Run with: streamlit run app.py
"""
import streamlit as st

# ── Page config MUST be first ──────────────────────────────
st.set_page_config(
    page_title="Research Information Collection Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports after page config
from components.styles import inject_css
from services.auth_service import (
    is_authenticated, get_current_profile, get_current_role,
    sign_out, has_pending_verification,
)
from pages.auth_page import render_auth_page
from pages.faculty_dashboard import render_faculty_dashboard
from pages.hod_dashboard import render_hod_dashboard
from pages.rd_dashboard import render_rd_dashboard
from pages.admin_dashboard import render_admin_dashboard
from pages.nba_module import render_nba_module
from pages.profile_management import render_profile_management
from components.ui import sidebar_user_widget, sidebar_summary_widget
from services.storage_service import init_storage
from utils.helpers import get_image_base64
from config import APP_NAME, INSTITUTION_NAME


# ════════════════════════════════════════════════════════════
# SIDEBAR NAV
# ════════════════════════════════════════════════════════════

def _build_sidebar(role: str) -> str:
    profile = get_current_profile()

    # ── Sidebar Logo (Institutional Branding) ──────────────
    logo_base64 = get_image_base64("assets/hkbk_official_logo.png")
    logo_html = (f'<img src="data:image/png;base64,{logo_base64}">'
                 if logo_base64 else '')
    
    st.sidebar.markdown(f"""
    <div class="sidebar-logo-centered">
        {logo_html}
        <h2>{APP_NAME}</h2>
        <p>{INSTITUTION_NAME}</p>
    </div>
    """, unsafe_allow_html=True)

    if profile:
        sidebar_user_widget(profile)

    NAV = {
        "faculty": [
            {"header": "DASHBOARD"},
            {"label": "Overview", "icon": "📊", "key": "faculty_home"},
            {"header": "PUBLICATIONS"},
            {"label": "Journals", "icon": "📓", "key": "faculty_journals"},
            {"label": "Conferences", "icon": "🎙️", "key": "faculty_conferences"},
            {"label": "Patents", "icon": "💡", "key": "faculty_patents"},
            {"header": "RESEARCH ACTIVITIES"},
            {"label": "Research Proposals", "icon": "📋", "key": "faculty_proposals"},
            {"label": "FDPs", "icon": "🎓", "key": "faculty_fdp"},
            {"label": "Consultancy", "icon": "🤝", "key": "faculty_consultancy"},
            {"label": "Projects", "icon": "🔬", "key": "faculty_projects"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"label": "Analytics", "icon": "📈", "key": "analytics"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
        "hod": [
            {"header": "DASHBOARD"},
            {"label": "Department Overview", "icon": "🏢", "key": "hod_home"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
        "rd_coordinator": [
            {"header": "DASHBOARD"},
            {"label": "R&D Overview", "icon": "🔬", "key": "rd_home"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
        "admin": [
            {"header": "DASHBOARD"},
            {"label": "Admin Center", "icon": "⚙️", "key": "admin_home"},
            {"label": "R&D Overview", "icon": "🔬", "key": "rd_home"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
        "iqac": [
            {"header": "DASHBOARD"},
            {"label": "IQAC Overview", "icon": "📊", "key": "rd_home"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
        "principal": [
            {"header": "DASHBOARD"},
            {"label": "Institution Overview", "icon": "🏛️", "key": "rd_home"},
            {"header": "REPORTS"},
            {"label": "NBA Reports", "icon": "🏅", "key": "nba"},
            {"header": "ACCOUNT"},
            {"label": "My Profile", "icon": "👤", "key": "profile"},
            {"label": "Settings", "icon": "⚙️", "key": "settings"},
        ],
    }

    if "current_page" not in st.session_state:
        st.session_state.current_page = f"faculty_home" if role == "faculty" else f"{role}_home"

    items = NAV.get(role, [])
    
    st.sidebar.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
    
    for item in items:
        if "header" in item:
            st.sidebar.markdown(f'<div class="sidebar-header">{item["header"]}</div>', unsafe_allow_html=True)
        else:
            is_active = (st.session_state.current_page == item["key"])
            if is_active:
                st.sidebar.markdown(f'<div class="nav-item-active"><span style="width:24px;text-align:center;">{item["icon"]}</span> <span>{item["label"]}</span></div>', unsafe_allow_html=True)
            else:
                if st.sidebar.button(f"{item['icon']}  {item['label']}", key=f"nav_{item['key']}", use_container_width=True):
                    st.session_state.current_page = item["key"]
                    st.rerun()

    selected_page = st.session_state.current_page

    st.sidebar.markdown('<hr style="margin: 10px 0; border: none; border-top: 1px solid #1E293B;">', unsafe_allow_html=True)
    if st.sidebar.button("🚪 Sign Out", type="primary", use_container_width=True):
        sign_out()

    st.sidebar.markdown("""
    <p style="font-size:0.65rem;color:#64748B;text-align:center;margin-top:12px;">
    Research Portal v1.0
    </p>""", unsafe_allow_html=True)

    return selected_page


# ════════════════════════════════════════════════════════════
# ROUTE
# ════════════════════════════════════════════════════════════

def _route(page_key: str, role: str):
    if page_key == "faculty_home":
        render_faculty_dashboard()
    elif page_key in ("faculty_journals", "faculty_conferences", "faculty_patents",
                      "faculty_proposals", "faculty_fdp", "faculty_consultancy", "faculty_projects"):
        type_map = {
            "faculty_journals":      "Journal",
            "faculty_conferences":   "Conference",
            "faculty_patents":       "Patent",
            "faculty_proposals":     "Research Proposal",
            "faculty_fdp":           "FDP",
            "faculty_consultancy":   "Consultancy",
            "faculty_projects":      "Project",
        }
        from pages.faculty_dashboard import render_faculty_category
        render_faculty_category(type_map[page_key])
    elif page_key == "hod_home":
        render_hod_dashboard()
    elif page_key == "rd_home":
        render_rd_dashboard()
    elif page_key == "admin_home":
        render_admin_dashboard()
    elif page_key == "nba":
        render_nba_module()
    elif page_key == "profile":
        render_profile_management()
    else:
        default_map = {
            "faculty": render_faculty_dashboard,
            "hod": render_hod_dashboard,
            "rd_coordinator": render_rd_dashboard,
            "iqac": render_rd_dashboard,
            "principal": render_rd_dashboard,
            "admin": render_admin_dashboard,
        }
        default_map.get(role, render_faculty_dashboard)()


# ════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════

def main():
    inject_css()
    init_storage()

    # Email verification pending — show auth page (no sidebar)
    if has_pending_verification():
        render_auth_page()
        return

    if not is_authenticated():
        render_auth_page()
        return

    profile = get_current_profile()
    if not profile:
        st.error("Profile not found")
        if st.button("Sign Out"):
            sign_out()
        st.stop()

    role = get_current_role()
    VALID_ROLES = ["faculty", "hod", "rd_coordinator", "iqac", "principal", "admin"]
    if role not in VALID_ROLES:
        st.error(f"Invalid role: {role}")
        if st.button("Sign Out"):
            sign_out()
        st.stop()

    selected_page = _build_sidebar(role)
    _route(selected_page, role)


if __name__ == "__main__":
    main()
