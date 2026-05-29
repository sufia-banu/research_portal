"""
utils/validators.py - Input validation helpers
"""
from __future__ import annotations
import re


def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def validate_password(password: str) -> tuple[bool, str]:
    if len(password) < 8:
        return False, "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one digit."
    return True, "OK"


def validate_research_entry(data: dict) -> tuple[bool, str]:
    if not data.get("title", "").strip():
        return False, "Title is required."
    if not data.get("research_type"):
        return False, "Research type is required."
    if not data.get("status"):
        return False, "Status is required."
    if data.get("impact_factor") is not None:
        try:
            val = float(data["impact_factor"])
            if val < 0:
                return False, "Impact factor must be a positive number."
        except (ValueError, TypeError):
            return False, "Impact factor must be a valid number."
    return True, "OK"


def sanitize_text(text: str) -> str:
    """Basic sanitization — strip and collapse whitespace."""
    return " ".join(text.strip().split()) if text else ""
