"""
utils/helpers.py - General utility helpers
"""
from __future__ import annotations
import pandas as pd
import base64
import os
from datetime import datetime, date
from config import MONTHS, MONTH_NUM_TO_NAME


def get_image_base64(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def safe_int(v):
    return int(v) if pd.notna(v) and v is not None else 0

def safe_float(v):
    return float(v) if pd.notna(v) and v is not None else 0.0

def safe_bool(v):
    return bool(v)

def get_current_month_name() -> str:
    return datetime.now().strftime("%B")


def get_current_year() -> int:
    return datetime.now().year


def get_current_month_num() -> int:
    return datetime.now().month


def month_name_to_num(name: str) -> int:
    return MONTHS.index(name) + 1 if name in MONTHS else 1


def num_to_month_name(num: int) -> str:
    return MONTH_NUM_TO_NAME.get(num, "Unknown")


def build_academic_year_list(start_year: int = 2020) -> list[str]:
    end_year = max(get_current_year(), 2030)
    years = []
    for y in range(start_year, end_year + 1):
        years.append(f"{y}-{str(y+1)[-2:]}")
    return list(reversed(years))


def format_currency(amount: float) -> str:
    if amount is None:
        return "—"
    return f"₹{amount:,.0f}"


def format_impact_factor(val) -> str:
    if val is None:
        return "—"
    try:
        return f"{float(val):.3f}"
    except Exception:
        return str(val)


def truncate(text: str, length: int = 60) -> str:
    if not text:
        return ""
    return text if len(text) <= length else text[:length] + "…"


def get_years_list(start: int = 2018) -> list[int]:
    end_year = max(get_current_year(), 2030)
    return list(range(end_year, start - 1, -1))


def role_display(role: str) -> str:
    mapping = {
        "faculty": "👨‍🏫 Faculty",
        "hod": "🏢 Head of Department",
        "rd_coordinator": "🔬 R&D Coordinator",
        "admin": "⚙️ Administrator",
    }
    return mapping.get(role, role.title())


def status_badge_color(status: str) -> str:
    colors = {
        "Published": "#2ECC71",
        "Granted": "#2ECC71",
        "Accepted": "#3498DB",
        "Funded": "#3498DB",
        "Under Review": "#F39C12",
        "Submitted": "#95A5A6",
        "Filed": "#9B59B6",
        "Rejected": "#E74C3C",
        "Draft": "#BDC3C7",
    }
    return colors.get(status, "#95A5A6")
