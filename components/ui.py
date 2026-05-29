"""
components/ui.py - Reusable Streamlit UI components (upgraded)
"""
from __future__ import annotations
import streamlit as st
from utils.helpers import status_badge_color, truncate, role_display


# ════════════════════════════════════════════════════════════
# METRIC CARD
# ════════════════════════════════════════════════════════════

def metric_card(title: str, value, icon: str = "📊",
                color: str = "#2563EB", delta: str = None):
    delta_html = (f'<p class="card-delta">▲ {delta}</p>' if delta else "")
    st.markdown(f"""
<div class="metric-card" style="border-top:4px solid {color}; flex-direction:column; justify-content:center; text-align:center;">
  <p class="card-title" style="width:100%;">{title}</p>
  <div class="card-icon">{icon}</div>
  <p class="card-value" style="white-space:nowrap;">{value}</p>
  {delta_html}
</div>
""", unsafe_allow_html=True)



# ════════════════════════════════════════════════════════════
# STATUS BADGE (inline HTML)
# ════════════════════════════════════════════════════════════

def status_badge(status: str) -> str:
    color = status_badge_color(status)
    return (f'<span style="background:{color};color:#fff;padding:2px 10px;'
            f'border-radius:12px;font-size:0.74rem;font-weight:700;'
            f'white-space:nowrap;">{status}</span>')


# ════════════════════════════════════════════════════════════
# PAGE HEADER
# ════════════════════════════════════════════════════════════

def page_header(title: str, subtitle: str = "", icon: str = ""):
    sub_html = f'<p class="page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(f"""
<div class="page-header">
<h1 class="page-title">{icon} {title}</h1>
        {sub_html}
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SECTION HEADER
# ════════════════════════════════════════════════════════════

def section_header(title: str, icon: str = ""):
    st.markdown(f"""
<div class="section-header">
<span>{icon}</span>
<span>{title}</span>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# BANNERS
# ════════════════════════════════════════════════════════════

def info_banner(msg: str):
    st.markdown(f'<div class="info-banner">ℹ️ {msg}</div>',
                unsafe_allow_html=True)

def warning_banner(msg: str):
    st.markdown(f'<div class="warning-banner">⚠️ {msg}</div>',
                unsafe_allow_html=True)

def success_banner(msg: str):
    st.markdown(f'<div class="success-banner">✅ {msg}</div>',
                unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# REMINDER CARD
# ════════════════════════════════════════════════════════════

def reminder_card(reminder: dict):
    date_str = (reminder.get("sent_at","")[:10]
                if reminder.get("sent_at") else "")
    role_label = (reminder.get("target_role","")
                  .replace("_"," ").title())
    st.markdown(f"""
<div class="reminder-card">
<div class="reminder-icon">🔔</div>
<div>
<p class="reminder-msg">{reminder.get("message","")}</p>
<p class="reminder-meta">Sent: {date_str} · To: {role_label}</p>
</div>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# RANKING ROW
# ════════════════════════════════════════════════════════════

def ranking_row(rank: int, name: str, count: int, dept: str = ""):
    dept_html = (f'<span style="font-size:0.72rem;color:#4A6070;margin-left:8px;">'
                 f'{dept}</span>' if dept else "")
    st.markdown(f"""
<div class="rank-row">
<div class="rank-num">{rank}</div>
<div class="rank-name">{name}{dept_html}</div>
<div class="rank-count">{count}</div>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# USER CARD
# ════════════════════════════════════════════════════════════

def user_card(profile: dict):
    active = "🟢 Active" if profile.get("is_active", True) else "🔴 Inactive"
    st.markdown(f"""
<div class="user-card">
<div class="user-avatar">{profile.get("full_name","?")[0].upper()}</div>
<div class="user-info">
<strong>{profile.get("full_name","")}</strong>
<span class="user-role">{role_display(profile.get("role",""))}</span>
<span class="user-dept">{profile.get("department","")}</span>
<span class="user-status">{active}</span>
</div>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SIDEBAR USER WIDGET
# ════════════════════════════════════════════════════════════

def sidebar_user_widget(profile: dict):
    name  = profile.get("full_name") or "User"
    role  = role_display(profile.get("role") or "")
    dept  = profile.get("department") or ""
    photo = profile.get("photo_url")
    
    avatar_html = (f'<img src="{photo}" class="sidebar-avatar-img">' if photo 
                   else f'<div class="sidebar-avatar">{name[0].upper() if name else "U"}</div>')
    
    # Truncate long strings
    dept_short = dept[:30] + "…" if len(dept) > 30 else dept
    designation = profile.get("designation") or ""
    role_info = f"{designation} · {role}" if designation else role
    
    st.sidebar.markdown(f"""
<div class="sidebar-user">
  <div class="sidebar-user-left">
    {avatar_html}
    <div class="sidebar-user-info">
      <strong>{name}</strong>
      <span>{role_info}</span>
      <small>{dept_short}</small>
    </div>
  </div>
  <div class="sidebar-user-chevron">&lt;</div>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# SIDEBAR RESEARCH SUMMARY WIDGET
# ════════════════════════════════════════════════════════════

def sidebar_summary_widget(stats: dict):
    # Map raw stats to display format
    metrics = {
        "Publications": stats.get("journals", 0) + stats.get("conferences", 0),
        "Projects": stats.get("projects", 0),
        "Patents": stats.get("patents", 0),
        "FDPs": stats.get("fdps", 0)
    }
    
    total = sum(metrics.values())
    if total == 0:
        score = 0
    else:
        # Example dynamic score logic: 100% if there are at least 15 items
        score = min(int((total / 15.0) * 100), 100)
    
    stat_html = ""
    for k, v in metrics.items():
        stat_html += f'<div class="summary-stat-row"><span>{k}</span><span class="summary-stat-val">{v}</span></div>'

    st.sidebar.markdown(f"""
<div class="sidebar-summary">
    <div class="summary-title">Research Summary</div>
    <div class="summary-content">
        <div class="summary-circle" style="--pct:{score}%;">
            <span>{score}%</span>
        </div>
        <div class="summary-stats">
            {stat_html}
        </div>
    </div>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# KPI SUMMARY ROW  (compact metric tiles)
# ════════════════════════════════════════════════════════════

def kpi_row(items: list[tuple]):
    """
    items = [(label, value, icon, color), ...]
    Creates a uniform metric card row with auto-sizing columns.
    """
    cols = st.columns(len(items))
    for col, (label, value, icon, color) in zip(cols, items):
        with col:
            metric_card(label, value, icon, color=color)


# ════════════════════════════════════════════════════════════
# EMPTY STATE
# ════════════════════════════════════════════════════════════

def empty_state(message: str, icon: str = "📭"):
    st.markdown(f"""
<div style="text-align:center;padding:48px 24px;
                background:rgba(10,20,40,0.4);border-radius:14px;
                border:1px dashed rgba(46,134,171,0.2);margin:16px 0;">
<div style="font-size:2.8rem;margin-bottom:12px;">{icon}</div>
<p style="color:#6B7D8E;font-size:0.9rem;margin:0;">{message}</p>
</div>
    """, unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════
# DEPARTMENT BADGE
# ════════════════════════════════════════════════════════════

DEPT_COLORS = {
    "CSE":  "#2E86AB", "ISE":  "#3498DB", "AIML": "#9B59B6",
    "ECE":  "#F18F01", "ME":   "#E74C3C", "CE":   "#2ECC71",
    "BS":   "#1ABC9C",
}

def dept_badge(dept_name: str, code: str = "") -> str:
    color = DEPT_COLORS.get(code, "#6B7D8E")
    return (f'<span style="background:{color}22;color:{color};'
            f'border:1px solid {color}44;padding:2px 8px;'
            f'border-radius:8px;font-size:0.72rem;font-weight:700;">'
            f'{code or dept_name[:6]}</span>')


# ════════════════════════════════════════════════════════════
# FACULTY PROFILE CARD
# ════════════════════════════════════════════════════════════

def render_faculty_profile_card(profile: dict, metrics: dict = None):
    with st.expander(f"👤 {profile.get('full_name', 'Unknown')} - {profile.get('department', 'No Dept')}"):
        c1, c2 = st.columns([1, 4])
        with c1:
            photo = profile.get("photo_url")
            if photo:
                st.image(photo, width=120)
            else:
                st.markdown("📷 *No Photo*")
            st.markdown(f"**ID:** {profile.get('employee_id') or '—'}")
        with c2:
            sc1, sc2 = st.columns(2)
            with sc1:
                st.markdown(f"**Designation:** {profile.get('designation') or '—'}")
                st.markdown(f"**Email:** {profile.get('email') or '—'}")
                st.markdown(f"**Mobile:** {profile.get('mobile_number') or '—'}")
            with sc2:
                # Professional IDs
                st.markdown("**Professional IDs:**")
                if profile.get('orcid_id'): st.markdown(f"• ORCID: `{profile.get('orcid_id')}`")
                if profile.get('scopus_id'): st.markdown(f"• Scopus: `{profile.get('scopus_id')}`")
                if profile.get('vidhwan_id'): st.markdown(f"• Vidhwan: `{profile.get('vidhwan_id')}`")
                if profile.get('google_scholar_link'): st.markdown(f"• [Google Scholar]({profile.get('google_scholar_link')})")

            st.markdown("---")
            if metrics:
                st.markdown("**Research Output Summary:**")
                mc1, mc2, mc3, mc4 = st.columns(4)
                mc1.markdown(f"📓 **Journals:** {metrics.get('Journals', 0)}")
                mc2.markdown(f"🎙️ **Conferences:** {metrics.get('Conferences', 0)}")
                mc3.markdown(f"💡 **Patents:** {metrics.get('Patents', 0)}")
                mc4.markdown(f"📋 **Proposals:** {metrics.get('Proposals', 0)}")
                st.markdown("---")

            # Research Supervision
            r_role = profile.get('research_role', 'None')
            st.markdown(f"**Research Role:** {r_role}")
            if r_role == "Research Supervisor":
                scholars = profile.get("scholars_data", [])
                if scholars:
                    st.markdown("**Scholars Supervised:**")
                    for s in scholars:
                        st.markdown(f"- **{s.get('name') or 'Unknown'}**: _{s.get('status') or 'Unknown'}_")
                else:
                    st.markdown("_No scholars recorded._")
