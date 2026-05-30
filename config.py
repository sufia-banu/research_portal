"""
config.py - Application-wide configuration constants
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Supabase ──────────────────────────────────────────────
SUPABASE_URL             = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY        = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_ROLE_KEY= os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# ── API Keys ──────────────────────────────────────────────
SERPAPI_KEY              = os.getenv("SERPAPI_KEY", "")

# ── App Meta ──────────────────────────────────────────────
APP_NAME         = os.getenv("APP_NAME", "Research Information Collection Portal")
INSTITUTION_NAME = os.getenv("INSTITUTION_NAME", "HKBK College of Engineering")
APP_VERSION      = "1.0.0"

# ── Roles ─────────────────────────────────────────────────
ROLES = {
    "faculty":        "Faculty",
    "hod":            "HoD",
    "rd_coordinator": "R&D Coordinator",
    "iqac":           "IQAC",
    "principal":      "Principal",
    "admin":          "Admin",
}

ROLE_HIERARCHY = {
    "faculty": 1, "hod": 2, "rd_coordinator": 3, "iqac": 4, "principal": 5, "admin": 6,
}

# ── Departments (fallback if DB unavailable) ───────────────
# Only engineering departments — mirrors departments_seed.sql
ENGINEERING_DEPARTMENTS = [
    "Artificial Intelligence and Machine Learning",
    "Chemistry",
    "Computer Science and Engineering",
    "Electronics and Communication Engineering",
    "Humanities",
    "Information Science and Engineering",
    "Mathematics",
    "Mechanical Engineering",
    "Physics",
]

# ── Research Types ────────────────────────────────────────
RESEARCH_TYPES = ["Journal", "Conference", "Book", "Patent", "Research Proposal", "FDP", "Consultancy", "Project"]

# ── Indexing Options ──────────────────────────────────────
INDEXING_OPTIONS = [
    "Scopus", "SCI", "UGC", "Web of Science",
    "IEEE", "Springer", "Elsevier", "Other",
]

# ── Status Options ────────────────────────────────────────
PUBLICATION_STATUSES  = ["Submitted", "Under Review", "Accepted", "Published", "Rejected"]
PATENT_STATUSES       = ["Filed", "Under Review", "Published", "Granted", "Rejected"]
PROPOSAL_STATUSES     = ["Draft", "Submitted", "Under Review", "Approved", "Rejected", "Funded"]
FDP_STATUSES          = ["Registered", "Completed", "Ongoing"]
CONSULTANCY_STATUSES = ["Proposed", "Ongoing", "Completed", "Cancelled"]
PROJECT_STATUSES      = ["Draft", "Submitted", "Ongoing", "Completed", "Rejected"]

# ── Months ────────────────────────────────────────────────
MONTHS = [
    "January","February","March","April","May","June",
    "July","August","September","October","November","December",
]
MONTH_MAP          = {m: i+1  for i, m in enumerate(MONTHS)}
MONTH_NUM_TO_NAME  = {i+1: m  for i, m in enumerate(MONTHS)}

# ── Chart Color Palette ───────────────────────────────────
CHART_COLORS = [
    "#2E86AB", "#F18F01", "#2ECC71", "#E74C3C",
    "#9B59B6", "#1ABC9C", "#F39C12", "#3498DB",
    "#E91E63", "#00BCD4",
]

COLORS = {
    "primary":  "#2E86AB",
    "secondary":"#1E3A5F",
    "accent":   "#F18F01",
    "success":  "#2ECC71",
    "warning":  "#F39C12",
    "danger":   "#E74C3C",
}

# ── NBA ───────────────────────────────────────────────────
NBA_RESEARCH_CRITERION = "Criterion 5 — Faculty Contributions"
