"""
components/styles.py - Premium Light-theme Enterprise SaaS CSS
"""
import streamlit as st

GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --primary: #2563EB;
    --primary-hover: #1D4ED8;
    --primary-light: #EFF6FF;
    --secondary: #0F172A;
    --accent: #14B8A6;
    --bg-color: #F1F5F9;
    --card-bg: #FFFFFF;
    --border: #CBD5E1;
    --text-primary: #111827;
    --text-secondary: #475569;
    --text-muted: #64748B;
    --success: #22C55E;
    --success-light: #DCFCE7;
    --warning: #F59E0B;
    --warning-light: #FEF3C7;
    --danger: #EF4444;
    --danger-light: #FEE2E2;
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    --input-bg: #FFFFFF;
    --input-border: #CBD5E1;
}

/* ── Reset & Base ───────────────────────────────────────── */
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    color: var(--text-primary) !important;
}
#MainMenu, footer, header, .stDeployButton { visibility: hidden; display: none !important; }

/* Hide Streamlit auto-generated multi-page sidebar nav (we use custom nav) */
[data-testid="stSidebarNav"] { display: none !important; }
[data-testid="stSidebarNavItems"] { display: none !important; }
[data-testid="stSidebarNavSeparator"] { display: none !important; }

/* ── App Background ─────────────────────────────────────── */
.stApp { background: var(--bg-color); min-height: 100vh; }
.block-container {
    padding-top: 1rem !important;
    padding-bottom: 1.5rem !important;
    max-width: 1400px !important;   /* wider = more room for 5-6 metric cards */
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0F172A !important;
    border-right: none !important;
    box-shadow: var(--shadow-lg) !important;
}
/* Reduce default Streamlit sidebar top padding and component spacing */
[data-testid="stSidebarHeader"] { padding: 0 !important; margin: 0 !important; }
[data-testid="stSidebar"] > div:first-child {
    padding-top: 0rem !important;
}
[data-testid="stSidebar"] .element-container { margin-bottom: 0px !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] { margin-bottom: 0px !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { margin-bottom: 0px !important; }
/* Every element inside sidebar */
[data-testid="stSidebar"] * { color: #CBD5E1 !important; }
[data-testid="stSidebar"] hr { border-color: #1E293B !important; opacity: 1 !important; }

/* Radio nav labels */
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stRadio p,
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    color: #CBD5E1 !important;
}
/* Radio container spacing */
[data-testid="stSidebar"] .stRadio > div { gap: 2px !important; }
/* Each radio option as a nav item */
[data-testid="stSidebar"] .stRadio label {
    display: flex !important;
    align-items: center !important;
    padding: 6px 12px !important;
    border-radius: 8px !important;
    transition: background 0.15s ease !important;
    cursor: pointer !important;
    width: 100% !important;
}
[data-testid="stSidebar"] .stRadio label:hover { background: #1E293B !important; }
/* Selected radio item highlight */
[data-testid="stSidebar"] .stRadio label[data-selected="true"],
[data-testid="stSidebar"] [aria-checked="true"] + span,
[data-testid="stSidebar"] input[type="radio"]:checked ~ div {
    color: #FFFFFF !important;
}
/* Radio circle — hide it for cleaner look */
[data-testid="stSidebar"] .stRadio [data-testid="stWidgetLabel"] { display: none !important; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] svg { fill: #475569 !important; }

/* ── Sidebar Logo ───────────────────────────────────────── */
.sidebar-logo-centered {
    text-align: center;
    padding: 0px 10px 10px;
    margin-top: -10px;
    margin-bottom: 5px;
}
.sidebar-logo-centered img {
    max-width: 80px;
    height: auto;
    margin: 0 auto;
    display: block;
    filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));
}
.sidebar-logo-centered h2 { 
    font-size: 1.05rem; 
    font-weight: 800; 
    color: #FFFFFF !important; 
    margin-top: 10px; 
    margin-bottom: 0;
    line-height: 1.1;
}
.sidebar-logo-centered p { 
    font-size: 0.65rem; 
    color: #94A3B8 !important; 
    margin-top: 4px; 
    margin-bottom: 0;
    font-weight: 600; 
    letter-spacing: 0.05em; 
    text-transform: uppercase;
}

/* ── Sidebar User Card ──────────────────────────────────── */
.sidebar-user {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 12px;
    background: #1E293B;
    border-radius: 12px; margin: 10px 12px 10px;
    border: 1px solid #334155;
}
.sidebar-user-left {
    display: flex; align-items: center; gap: 10px; overflow: hidden;
}
.sidebar-avatar {
    width: 36px; height: 36px; border-radius: 10px;
    background: var(--primary);
    display: flex; align-items: center; justify-content: center;
    font-size: 1rem; font-weight: 700; color: #FFFFFF !important; flex-shrink: 0;
    overflow: hidden;
}
.sidebar-avatar-img {
    width: 36px; height: 36px; border-radius: 10px;
    object-fit: cover; flex-shrink: 0;
    border: 2px solid #334155;
}
.sidebar-user-info { display: flex; flex-direction: column; gap: 1px; overflow: hidden; }
.sidebar-user-info strong { font-size: 0.85rem; color: #FFFFFF !important; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.sidebar-user-info span  { font-size: 0.70rem; color: #60A5FA !important; font-weight: 600; }
.sidebar-user-info small { font-size: 0.65rem; color: #94A3B8 !important; }
.sidebar-user-chevron { color: #64748B; font-size: 0.8rem; }

/* ── Page Header ────────────────────────────────────────── */
.page-header {
    background: transparent;
    border: none;
    padding: 0 0 10px 0;
    margin-bottom: 12px;
    box-shadow: none;
}
.page-title { 
    font-size: 2.4rem; 
    font-weight: 800; 
    margin: 0; 
    color: var(--text-primary); 
    letter-spacing: -0.04em; 
}
.page-subtitle { 
    font-size: 1.1rem; 
    color: var(--text-secondary); 
    margin-top: 4px; 
    font-weight: 500; 
}

/* ── Section Header ─────────────────────────────────────── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    font-size: 1.15rem; font-weight: 700; color: var(--text-primary);
    margin: 20px 0 10px; letter-spacing: -0.01em;
}

/* ── Metric Card — fully responsive ─────────────────────── */
.metric-card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: clamp(10px, 2vw, 20px) clamp(10px, 1.8vw, 18px);
    display: flex;
    align-items: center;
    gap: clamp(8px, 1.2vw, 16px);
    transition: all 0.2s ease;
    box-shadow: var(--shadow-sm);
    min-height: 80px;
    overflow: hidden;           /* prevent card overflow */
    width: 100%;
    min-width: 140px;           /* prevent card from collapsing entirely */
    box-sizing: border-box;
}
.metric-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); border-color: #94A3B8; }

/* Icon circle — shrinks gracefully on narrow columns */
.card-icon {
    font-size: clamp(1rem, 2.5vw, 1.8rem);
    flex-shrink: 0;
    width:  clamp(36px, 5vw, 52px);
    height: clamp(36px, 5vw, 52px);
    display: flex; align-items: center; justify-content: center;
    background: var(--bg-color); border-radius: 12px;
}
/* Hide icon entirely on very narrow screens so text always fits */
@media (max-width: 860px) {
    .card-icon { display: none !important; }
}
.card-content {
    flex: 1;
    min-width: 0;          /* allow flex child to shrink below content width */
    overflow: hidden;
}
.card-title {
    font-size: clamp(0.58rem, 1vw, 0.74rem);
    font-weight: 700;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
    white-space: normal;
    word-break: keep-all; /* STRICTLY avoid breaking words in the middle */
    overflow-wrap: normal;
}
.card-value {
    font-size: clamp(1.3rem, 3vw, 2rem);
    font-weight: 800;
    color: var(--text-primary);
    line-height: 1;
    white-space: nowrap;       /* numbers/percentages never wrap */
}
.card-delta { font-size: 0.78rem; color: var(--success); margin-top: 4px; font-weight: 600; white-space: nowrap; }

/* ── Type Badges ────────────────────────────────────────── */
.type-badge { padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600; white-space: nowrap; }
.type-publication       { background: #EFF6FF; color: #2563EB; }
.type-patent            { background: #FEF3C7; color: #B45309; }
.type-research-proposal { background: #F3E8FF; color: #7E22CE; }

/* ── Research Table ─────────────────────────────────────── */
.research-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 12px; }
.research-table th {
    background: var(--bg-color); color: var(--text-secondary);
    font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em;
    padding: 12px 16px; border-bottom: 2px solid var(--border);
    border-top: 1px solid var(--border); text-align: left; white-space: nowrap; font-weight: 700;
}
.research-table th:first-child { border-left: 1px solid var(--border); border-top-left-radius: 10px; }
.research-table th:last-child  { border-right: 1px solid var(--border); border-top-right-radius: 10px; }
.research-table td {
    padding: 14px 16px; border-bottom: 1px solid var(--border);
    color: var(--text-primary); font-size: 0.88rem; vertical-align: middle;
    background: var(--card-bg);
}
.research-table td:first-child { border-left: 1px solid var(--border); }
.research-table td:last-child  { border-right: 1px solid var(--border); }
.research-table tr:hover td { background: #FAFBFC; }
.research-table tr:last-child td:first-child { border-bottom-left-radius: 10px; }
.research-table tr:last-child td:last-child  { border-bottom-right-radius: 10px; }

/* ── Buttons ────────────────────────────────────────────── */
.stButton > button {
    background: var(--primary) !important;
    color: #FFFFFF !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.93rem !important; padding: 11px 24px !important;
    min-height: 46px; transition: all 0.2s ease !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover { background: var(--primary-hover) !important; box-shadow: var(--shadow-md) !important; }
.stButton > button[kind="secondary"] {
    background: #FFFFFF !important; border: 1px solid var(--border) !important;
    color: var(--text-primary) !important;
}
.stButton > button[kind="secondary"]:hover { background: var(--bg-color) !important; border-color: #94A3B8 !important; }

/* ── Custom Sidebar Navigation Styling ────────────────────── */
.sidebar-header {
    font-size: 0.85rem;
    font-weight: 800;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 20px 12px 8px 12px;
}

[data-testid="stSidebar"] button[kind="secondary"] {
    background: transparent !important;
    border: none !important;
    color: #CBD5E1 !important;
    justify-content: flex-start !important;
    padding: 8px 12px !important;
    margin-bottom: 2px !important;
    border-radius: 8px !important;
    min-height: 40px !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] button[kind="secondary"] > div {
    display: flex !important;
    justify-content: flex-start !important;
    width: 100% !important;
}
[data-testid="stSidebar"] button[kind="secondary"] p {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] button[kind="secondary"]:hover {
    background: #1E293B !important;
    color: #FFFFFF !important;
}

/* Active Nav Item */
.nav-item-active {
    background: #4F46E5;
    color: #FFFFFF;
    padding: 10px 14px;
    border-radius: 8px;
    font-weight: 700;
    font-size: 1.1rem;
    margin: 0 12px 4px 12px;
    display: flex;
    align-items: center;
    box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
    cursor: default;
}

/* ── Sidebar Sign Out Button ────────────────────────────── */
[data-testid="stSidebar"] button[kind="primary"] {
    background: transparent !important;
    border: 1px solid #334155 !important;
    color: #EF4444 !important;
    justify-content: center !important;
    margin: 10px 12px 20px !important;
    width: calc(100% - 24px) !important;
}
[data-testid="stSidebar"] button[kind="primary"]:hover {
    background: rgba(239, 68, 68, 0.1) !important;
    border-color: #EF4444 !important;
}

/* ── Research Summary Widget ───────────────────────────── */
.sidebar-summary {
    background: #1E293B;
    border-radius: 12px;
    padding: 16px;
    margin: 20px 12px 10px;
    border: 1px solid #334155;
}
.summary-title {
    font-size: 0.72rem;
    color: #94A3B8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 12px;
}
.summary-content {
    display: flex;
    gap: 12px;
    align-items: center;
}
.summary-circle {
    position: relative;
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: conic-gradient(#4F46E5 var(--pct), #334155 0);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.summary-circle::after {
    content: "";
    position: absolute;
    width: 44px;
    height: 44px;
    background: #1E293B;
    border-radius: 50%;
}
.summary-circle span {
    position: relative;
    z-index: 1;
    font-size: 0.75rem;
    font-weight: 700;
    color: #FFFFFF;
}
.summary-stats {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.summary-stat-row {
    display: flex;
    justify-content: space-between;
    font-size: 0.70rem;
    color: #94A3B8;
}
.summary-stat-val {
    font-weight: 700;
    color: #FFFFFF;
}

/* ── Tabs ────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid var(--border) !important;
    gap: 28px; padding-bottom: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important; color: var(--text-muted) !important;
    border-radius: 0 !important; font-weight: 600; font-size: 0.95rem;
    padding: 14px 4px; transition: color 0.2s; border-bottom: 3px solid transparent;
}
.stTabs [aria-selected="true"] {
    color: var(--primary) !important;
    border-bottom: 3px solid var(--primary) !important;
    background: transparent !important; box-shadow: none !important;
}

/* ── Inputs & Labels ─────────────────────────────────────── */
.stTextInput label, .stTextArea label, .stNumberInput label,
.stSelectbox label, .stMultiSelect label, .stDateInput label,
.stFileUploader label {
    color: var(--text-primary) !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: var(--input-bg) !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
    font-size: 0.93rem !important;
    padding: 12px 14px !important;
    min-height: 48px !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.2s ease !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12) !important;
}
::placeholder { color: #94A3B8 !important; opacity: 1 !important; }

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div {
    background: var(--input-bg) !important;
    border: 1px solid var(--input-border) !important;
    border-radius: 8px !important;
    min-height: 48px !important;
    box-shadow: var(--shadow-sm) !important;
}
.stSelectbox [data-baseweb="select"] span {
    color: var(--text-primary) !important;
    font-size: 0.93rem !important;
}

/* ── Checkbox ─────────────────────────────────────────────── */
.stCheckbox label { color: var(--text-primary) !important; font-size: 0.93rem !important; font-weight: 500; }

/* ── Expanders ───────────────────────────────────────────── */
[data-testid="stExpander"] summary {
    background: var(--card-bg) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text-primary) !important;
    font-weight: 600 !important; font-size: 0.95rem !important;
    box-shadow: var(--shadow-sm);
}
[data-testid="stExpander"] summary:hover { background: var(--bg-color) !important; }
[data-testid="stExpander"] summary p { color: var(--text-primary) !important; }

/* ── Markdown Text ───────────────────────────────────────── */
.stMarkdown p,
[data-testid="stMarkdownContainer"] p {
    color: var(--text-primary) !important;
    font-size: 0.93rem;
    line-height: 1.7;
}

/* ── Dataframes ─────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border-radius: 12px; overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
}

/* ── Info / Warning / Success Banners ───────────────────── */
.info-banner    { background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 10px; padding: 14px 18px; color: #1D4ED8; font-size: 0.9rem; font-weight: 500; margin-bottom: 16px; }
.warning-banner { background: var(--warning-light); border: 1px solid #FDE68A; border-radius: 10px; padding: 14px 18px; color: #B45309; font-size: 0.9rem; font-weight: 500; margin-bottom: 16px; }
.success-banner { background: var(--success-light); border: 1px solid #BBF7D0; border-radius: 10px; padding: 14px 18px; color: #166534; font-size: 0.9rem; font-weight: 500; margin-bottom: 16px; }

/* ── Reminder Card ──────────────────────────────────────── */
.reminder-card {
    display: flex; gap: 16px; align-items: flex-start;
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 12px; padding: 16px 20px; margin-bottom: 12px;
    box-shadow: var(--shadow-sm); transition: transform 0.2s;
}
.reminder-card:hover { transform: translateY(-2px); box-shadow: var(--shadow-md); }
.reminder-icon { font-size: 1.5rem; flex-shrink: 0; }
.reminder-msg  { font-size: 0.93rem; color: var(--text-primary); margin-bottom: 6px; font-weight: 600; }
.reminder-meta { font-size: 0.78rem; color: var(--text-muted); }

/* ── User Card ───────────────────────────────────────────── */
.user-card {
    display: flex; gap: 16px; align-items: center;
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 14px; padding: 16px 20px; margin-bottom: 8px;
    box-shadow: var(--shadow-sm); transition: all 0.2s;
}
.user-card:hover { border-color: var(--primary); box-shadow: var(--shadow-md); }
.user-avatar {
    width: 48px; height: 48px; border-radius: 12px;
    background: var(--primary-light);
    display: flex; align-items: center; justify-content: center;
    font-size: 1.2rem; font-weight: 700; color: var(--primary); flex-shrink: 0;
}
.user-info { display: flex; flex-direction: column; gap: 3px; }
.user-info strong { font-size: 0.97rem; color: var(--text-primary); font-weight: 700; }
.user-role   { font-size: 0.78rem; color: var(--primary); font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.user-dept   { font-size: 0.83rem; color: var(--text-secondary); }
.user-status { font-size: 0.78rem; color: var(--success); font-weight: 600; }

/* ── Download Buttons ────────────────────────────────────── */
.stDownloadButton > button {
    background: var(--success-light) !important;
    border: 1px solid #BBF7D0 !important;
    color: #166534 !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover { background: #DCFCE7 !important; border-color: #86EFAC !important; }

/* ── Progress ────────────────────────────────────────────── */
.stProgress > div > div { background: var(--primary) !important; border-radius: 6px; }

/* ── Plotly Charts ───────────────────────────────────────── */
.stPlotlyChart {
    border-radius: 16px; overflow: hidden;
    background: var(--card-bg);
    border: 1px solid var(--border);
    box-shadow: var(--shadow-sm);
    padding: 8px;
}

/* ── Caption ─────────────────────────────────────────────── */
.stCaption { color: var(--text-muted) !important; font-size: 0.82rem !important; }

/* ── NBA Report Header ───────────────────────────────────── */
.nba-report-header {
    background: var(--card-bg); border: 1px solid var(--border);
    border-radius: 16px; padding: 32px; text-align: center; margin-bottom: 24px;
    box-shadow: var(--shadow-sm);
}
.nba-report-header h2 { font-size: 1.5rem; font-weight: 800; color: var(--text-primary); margin: 0; }
.nba-report-header p  { font-size: 0.95rem; color: var(--text-secondary); margin: 8px 0 0; }

/* ── Rank Row ────────────────────────────────────────────── */
.rank-row {
    display: flex; align-items: center; gap: 16px;
    padding: 12px 18px; border-radius: 12px;
    background: var(--card-bg); border: 1px solid var(--border);
    margin-bottom: 8px; transition: all 0.2s;
}
.rank-row:hover { background: var(--bg-color); border-color: #94A3B8; }
.rank-num {
    width: 32px; height: 32px; border-radius: 8px;
    background: var(--primary-light);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem; font-weight: 700; color: var(--primary); flex-shrink: 0;
}
.rank-name  { flex: 1; font-size: 0.95rem; color: var(--text-primary); font-weight: 600; }
.rank-count { font-size: 1.25rem; font-weight: 800; color: var(--primary); min-width: 40px; text-align: right; }

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg-color); }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 8px; }
::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* ── Sidebar Toggle ──────────────────────────────────────── */
[data-testid="collapsedControl"] {
    color: var(--text-primary) !important;
    background: var(--card-bg) !important;
    border-radius: 50% !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
}
/* ── Streamlit Column Fix for Metric Cards ───────────────── */
/* Streamlit columns can clip content — remove overflow restriction */
[data-testid="column"] {
    overflow: visible !important;
    min-width: 140px !important;    /* enforce a minimum width so text doesn't squeeze */
}
/* Make the horizontal metric row not clip overflow and wrap on small screens */
[data-testid="stHorizontalBlock"] {
    overflow: visible !important;
    align-items: stretch !important;  /* equal-height cards */
    gap: 16px !important;
    flex-wrap: wrap !important;       /* ✨ Allow cards to wrap ✨ */
}
/* Each metric card wrapper column stretches to fill, but enforces a minimum width */
[data-testid="stHorizontalBlock"] > [data-testid="column"] {
    display: flex !important;
    flex-direction: column !important;
    flex: 1 1 160px !important;       /* grow, shrink, but minimum 160px */
    min-width: 160px !important;
}

</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def inject_auth_only_css():
    st.markdown("""
    <style>
    [data-testid="stSidebar"] { display: none !important; }

    .auth-hero {
        padding: 48px 40px;
        min-height: 480px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border-radius: 24px;
        border: 1px solid #BFDBFE;
        box-shadow: 0 4px 24px rgba(37, 99, 235, 0.08);
    }
    .hero-stats { display: flex; gap: 20px; margin-top: 28px; flex-wrap: wrap; }
    .stat-item {
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.8);
        padding: 18px 22px;
        border-radius: 14px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        flex: 1; min-width: 130px;
    }
    .stat-item strong { display: block; color: #2563EB; font-size: 1.1rem; font-weight: 800; margin-bottom: 4px; }
    .stat-item span   { color: #475569; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
    </style>
    """, unsafe_allow_html=True)
