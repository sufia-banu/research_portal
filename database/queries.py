"""
database/queries.py - All database CRUD operations
"""
from __future__ import annotations
from typing import Optional
from datetime import date, datetime
import streamlit as st
from database.connection import get_supabase_client, get_supabase_admin_client
from config import MONTH_MAP, ENGINEERING_DEPARTMENTS


# ════════════════════════════════════════════════════════════
# DEPARTMENTS
# ════════════════════════════════════════════════════════════

def fetch_departments() -> list[dict]:
    """Fetch departments from DB; silently falls back to engineering list."""
    try:
        client = get_supabase_client()
        res = client.table("departments").select("*").order("department_name").execute()
        depts = res.data or []
    except Exception:
        # Return fallback list as dict format (no error shown — used on registration page)
        depts = [{"id": None, "department_name": d, "code": ""}
                for d in ENGINEERING_DEPARTMENTS]
                
    filtered = []
    has_physics = False
    has_chemistry = False
    has_math = False
    
    for d in depts:
        name = d["department_name"]
        if name in ("Civil Engineering", "Basic Science", "Basic Sciences"):
            continue
        if name == "Physics":
            has_physics = True
        if name == "Chemistry":
            has_chemistry = True
        if name == "Mathematics":
            has_math = True
            
        filtered.append(d)
        
    if not has_physics:
        filtered.append({"id": None, "department_name": "Physics", "code": "PHY"})
    if not has_chemistry:
        filtered.append({"id": None, "department_name": "Chemistry", "code": "CHEM"})
    if not has_math:
        filtered.append({"id": None, "department_name": "Mathematics", "code": "MATH"})
        
    filtered.sort(key=lambda x: x["department_name"])
    return filtered


def get_department_names() -> list[str]:
    """Return department name strings; falls back to engineering list silently."""
    try:
        depts = fetch_departments()
        names = [d["department_name"] for d in depts]
        return names if names else ENGINEERING_DEPARTMENTS
    except Exception:
        return ENGINEERING_DEPARTMENTS


def add_department(name: str, code: str = "") -> bool:
    try:
        client = get_supabase_admin_client()
        client.table("departments").insert({"department_name": name, "code": code}).execute()
        return True
    except Exception as e:
        st.error(f"Error adding department: {e}")
        return False


def delete_department(dept_id: str) -> bool:
    try:
        client = get_supabase_admin_client()
        client.table("departments").delete().eq("id", dept_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting department: {e}")
        return False


# ════════════════════════════════════════════════════════════
# PROFILES / USERS
# ════════════════════════════════════════════════════════════

def fetch_profile(user_id: str) -> Optional[dict]:
    try:
        client = get_supabase_client()
        admin  = get_supabase_admin_client()
        
        # Fetch from profiles table
        res = client.table("profiles").select("*").eq("id", user_id).single().execute()
        profile = res.data or {}
        
        # Fetch from Auth Metadata (Fallback for new columns)
        try:
            user_data = admin.auth.admin.get_user_by_id(user_id)
            if user_data and user_data.user and user_data.user.user_metadata:
                # Merge metadata into profile (database takes priority for existing columns)
                meta = user_data.user.user_metadata
                for k, v in meta.items():
                    if k not in profile or profile[k] is None:
                        profile[k] = v
        except: pass
        
        return profile if profile else None
    except Exception as e:
        raise Exception(f"fetch_profile error for {user_id}: {e}")


def fetch_all_profiles() -> list[dict]:
    try:
        client = get_supabase_admin_client()
        res = client.table("profiles").select("*").order("full_name").execute()
        profiles = res.data or []
        
        # Merge Auth Metadata (Fallback for new columns missing from DB)
        try:
            users_list = client.auth.admin.list_users()
            user_meta_map = {u.id: u.user_metadata for u in users_list}
            for p in profiles:
                meta = user_meta_map.get(p["id"], {})
                for k, v in meta.items():
                    if k not in p or p[k] is None:
                        p[k] = v
        except: pass
        
        return profiles
    except Exception as e:
        st.error(f"Error fetching profiles: {e}")
        return []


def fetch_profiles_by_department(department: str) -> list[dict]:
    try:
        client = get_supabase_admin_client()
        res = (
            client.table("profiles")
            .select("*")
            .eq("department", department)
            .order("full_name")
            .execute()
        )
        profiles = res.data or []
        
        # Merge Auth Metadata (Fallback for new columns missing from DB)
        try:
            users_list = client.auth.admin.list_users()
            user_meta_map = {u.id: u.user_metadata for u in users_list}
            for p in profiles:
                meta = user_meta_map.get(p["id"], {})
                for k, v in meta.items():
                    if k not in p or p[k] is None:
                        p[k] = v
        except: pass
        
        return profiles
    except Exception as e:
        st.error(f"Error fetching profiles: {e}")
        return []


def update_profile(user_id: str, updates: dict) -> bool:
    """Updates profile with robust handling for missing columns."""
    try:
        client = get_supabase_admin_client()
        
        # 1. Try a direct update
        try:
            client.table("profiles").update(updates).eq("id", user_id).execute()
            return True
        except Exception as e:
            err_msg = str(e).lower()
            if "column" in err_msg:
                # 2. If columns are missing, filter them out and try a partial update
                # This ensures basic fields (name, dept) still save
                import re
                missing_col_match = re.search(r"column ['\"](.+?)['\"]", err_msg)
                if missing_col_match:
                    missing_col = missing_col_match.group(1)
                    safe_updates = {k: v for k, v in updates.items() if k != missing_col}
                    # Retry with safe fields
                    if safe_updates:
                        client.table("profiles").update(safe_updates).eq("id", user_id).execute()
                
                # 3. Fallback: Save ALL updates to Auth User Metadata 
                # This fixes it "from our end" without needing SQL!
                client.auth.admin.update_user_by_id(
                    user_id, 
                    {"user_metadata": updates}
                )
                return True
            else:
                raise e
    except Exception as e:
        st.error(f"Error updating profile: {e}")
        return False


def toggle_user_status(user_id: str, is_active: bool) -> bool:
    return update_profile(user_id, {"is_active": is_active})


def delete_user_profile(user_id: str) -> bool:
    try:
        client = get_supabase_admin_client()
        client.table("profiles").delete().eq("id", user_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False


# ════════════════════════════════════════════════════════════
# RESEARCH ENTRIES
# ════════════════════════════════════════════════════════════

def _build_academic_year(year: int, month: int) -> str:
    """Return academic year string like '2024-25'."""
    if month >= 6:
        return f"{year}-{str(year+1)[-2:]}"
    else:
        return f"{year-1}-{str(year)[-2:]}"

def _map_entry_types(entry: dict) -> dict:
    """Map DB 'Publication' type to 'Journal', 'Conference', or 'Book' for the UI based on conference_name field."""
    if entry.get("research_type") == "Publication":
        c_name = entry.get("conference_name")
        if c_name == "[BOOK]":
            entry["research_type"] = "Book"
            j_name = entry.get("journal_or_patent_office")
            entry["journal_or_patent_office"] = "" if j_name == "[JOUR_BLANK]" else j_name
        elif c_name is not None:
            entry["research_type"] = "Conference"
            entry["journal_or_patent_office"] = "" if c_name == "[CONF_BLANK]" else c_name
        else:
            entry["research_type"] = "Journal"
            j_name = entry.get("journal_or_patent_office")
            entry["journal_or_patent_office"] = "" if j_name == "[JOUR_BLANK]" else j_name
    # FDP, Consultancy, Project pass through unchanged
    return entry


def add_research_entry(data: dict) -> bool:
    try:
        client = get_supabase_client()
        if "submission_date" in data and isinstance(data["submission_date"], date):
            data["submission_date"] = data["submission_date"].isoformat()
        # Convert date objects for patent-specific fields
        for date_field in ("filing_date", "publication_date", "grant_date"):
            if date_field in data and isinstance(data[date_field], date):
                data[date_field] = data[date_field].isoformat()
        data["academic_year"] = _build_academic_year(data["year"], data["month"])
        
        # Map UI types to DB constraints
        if data.get("research_type") in ("Journal", "Conference", "Book"):
            val = data.get("journal_or_patent_office") or ""
            if data["research_type"] == "Conference":
                data["conference_name"] = val if val else "[CONF_BLANK]"
                data["journal_or_patent_office"] = None
            elif data["research_type"] == "Book":
                data["conference_name"] = "[BOOK]"
                data["journal_or_patent_office"] = val if val else "[JOUR_BLANK]"
            else:
                data["conference_name"] = None
                data["journal_or_patent_office"] = val if val else "[JOUR_BLANK]"
            data["research_type"] = "Publication"
            
        client.table("research_entries").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error adding research entry: {e}")
        return False


def update_research_entry(entry_id: str, data: dict) -> bool:
    try:
        client = get_supabase_client()
        if "submission_date" in data and isinstance(data["submission_date"], date):
            data["submission_date"] = data["submission_date"].isoformat()
        for date_field in ("filing_date", "publication_date", "grant_date"):
            if date_field in data and isinstance(data[date_field], date):
                data[date_field] = data[date_field].isoformat()
        if "year" in data and "month" in data:
            data["academic_year"] = _build_academic_year(data["year"], data["month"])
            
        # Map UI types to DB constraints
        if data.get("research_type") in ("Journal", "Conference", "Book"):
            val = data.get("journal_or_patent_office") or ""
            if data["research_type"] == "Conference":
                data["conference_name"] = val if val else "[CONF_BLANK]"
                data["journal_or_patent_office"] = None
            elif data["research_type"] == "Book":
                data["conference_name"] = "[BOOK]"
                data["journal_or_patent_office"] = val if val else "[JOUR_BLANK]"
            else:
                data["conference_name"] = None
                data["journal_or_patent_office"] = val if val else "[JOUR_BLANK]"
            data["research_type"] = "Publication"
            
        client.table("research_entries").update(data).eq("id", entry_id).execute()
        return True
    except Exception as e:
        st.error(f"Error updating entry: {e}")
        return False


def delete_research_entry(entry_id: str) -> bool:
    try:
        client = get_supabase_client()
        client.table("research_entries").delete().eq("id", entry_id).execute()
        return True
    except Exception as e:
        st.error(f"Error deleting entry: {e}")
        return False


def fetch_my_entries(faculty_id: str) -> list[dict]:
    try:
        client = get_supabase_client()
        res = (
            client.table("research_entries")
            .select("*")
            .eq("faculty_id", faculty_id)
            .order("created_at", desc=True)
            .execute()
        )
        return [_map_entry_types(e) for e in res.data] if res.data else []
    except Exception as e:
        st.error(f"Error fetching entries: {e}")
        return []


def fetch_department_entries(department: str, filters: dict = None) -> list[dict]:
    try:
        client = get_supabase_admin_client()
        q = (
            client.table("research_entries")
            .select("*, profiles(full_name, email)")
            .eq("department", department)
        )
        if filters:
            if filters.get("year"):
                q = q.eq("year", filters["year"])
            if filters.get("month"):
                q = q.eq("month", filters["month"])
            if filters.get("research_type"):
                rtype = filters["research_type"]
                q = q.eq("research_type", "Publication" if rtype in ("Journal", "Conference") else rtype)
            if filters.get("status"):
                q = q.eq("status", filters["status"])
            if filters.get("faculty_id"):
                q = q.eq("faculty_id", filters["faculty_id"])
        res = q.order("created_at", desc=True).execute()
        entries = [_map_entry_types(e) for e in res.data] if res.data else []
        if filters and filters.get("research_type") in ("Journal", "Conference"):
            entries = [e for e in entries if e["research_type"] == filters["research_type"]]
        return entries
    except Exception as e:
        st.error(f"Error fetching department entries: {e}")
        return []


def fetch_all_entries(filters: dict = None) -> list[dict]:
    try:
        client = get_supabase_admin_client()
        q = client.table("research_entries").select("*, profiles(full_name, email, department)")
        if filters:
            if filters.get("year"):
                q = q.eq("year", filters["year"])
            if filters.get("month"):
                q = q.eq("month", filters["month"])
            if filters.get("research_type"):
                rtype = filters["research_type"]
                q = q.eq("research_type", "Publication" if rtype in ("Journal", "Conference") else rtype)
            if filters.get("department"):
                q = q.eq("department", filters["department"])
            if filters.get("status"):
                q = q.eq("status", filters["status"])
            if filters.get("academic_year"):
                q = q.eq("academic_year", filters["academic_year"])
            if filters.get("faculty_id"):
                q = q.eq("faculty_id", filters["faculty_id"])
        res = q.order("created_at", desc=True).execute()
        entries = [_map_entry_types(e) for e in res.data] if res.data else []
        if filters and filters.get("research_type") in ("Journal", "Conference"):
            entries = [e for e in entries if e["research_type"] == filters["research_type"]]
        return entries
    except Exception as e:
        st.error(f"Error fetching all entries: {e}")
        return []


def fetch_entry_by_id(entry_id: str) -> Optional[dict]:
    try:
        client = get_supabase_client()
        res = client.table("research_entries").select("*").eq("id", entry_id).single().execute()
        return _map_entry_types(res.data) if res.data else None
    except Exception:
        return None


# ════════════════════════════════════════════════════════════
# ANALYTICS
# ════════════════════════════════════════════════════════════

def get_faculty_stats(faculty_id: str) -> dict:
    entries = fetch_my_entries(faculty_id)
    stats = {
        "total": len(entries),
        "publications": sum(1 for e in entries if e["research_type"] in ("Journal", "Conference")),
        "journals": sum(1 for e in entries if e["research_type"] == "Journal"),
        "conferences": sum(1 for e in entries if e["research_type"] == "Conference"),
        "patents": sum(1 for e in entries if e["research_type"] == "Patent"),
        "proposals": sum(1 for e in entries if e["research_type"] == "Research Proposal"),
        "fdps": sum(1 for e in entries if e["research_type"] == "FDP"),
        "consultancies": sum(1 for e in entries if e["research_type"] == "Consultancy"),
        "projects": sum(1 for e in entries if e["research_type"] == "Project"),
        "published": sum(1 for e in entries if e["status"] in ("Published", "Granted", "Completed")),
        "under_review": sum(1 for e in entries if e["status"] == "Under Review"),
    }
    return stats


def get_department_stats(department: str) -> dict:
    entries = fetch_department_entries(department)
    faculty = fetch_profiles_by_department(department)
    stats = {
        "total": len(entries),
        "publications": sum(1 for e in entries if e["research_type"] in ("Journal", "Conference")),
        "journals": sum(1 for e in entries if e["research_type"] == "Journal"),
        "conferences": sum(1 for e in entries if e["research_type"] == "Conference"),
        "patents": sum(1 for e in entries if e["research_type"] == "Patent"),
        "proposals": sum(1 for e in entries if e["research_type"] == "Research Proposal"),
        "faculty_count": len(faculty),
        "active_researchers": len(set(e["faculty_id"] for e in entries)),
    }
    return stats


def get_institution_stats() -> dict:
    entries = fetch_all_entries()
    profiles = fetch_all_profiles()
    depts = fetch_departments()
    
    # Filter entries to only include those belonging to currently active departments
    active_dept_names = [d["department_name"] for d in depts]
    valid_entries = [e for e in entries if e.get("department") in active_dept_names]
    valid_profiles = [p for p in profiles if p.get("department") in active_dept_names]

    stats = {
        "total": len(valid_entries),
        "publications": sum(1 for e in valid_entries if e["research_type"] in ("Journal", "Conference")),
        "journals": sum(1 for e in valid_entries if e["research_type"] == "Journal"),
        "conferences": sum(1 for e in valid_entries if e["research_type"] == "Conference"),
        "patents": sum(1 for e in valid_entries if e["research_type"] == "Patent"),
        "proposals": sum(1 for e in valid_entries if e["research_type"] == "Research Proposal"),
        "total_faculty": sum(1 for p in valid_profiles if p["role"] == "faculty"),
        "total_departments": len(depts),
        "active_researchers": len(set(e["faculty_id"] for e in valid_entries)),
    }
    return stats


# ════════════════════════════════════════════════════════════
# REMINDERS
# ════════════════════════════════════════════════════════════

def fetch_active_reminders(role: str) -> list[dict]:
    try:
        client = get_supabase_admin_client()
        res = (
            client.table("reminders")
            .select("*")
            .eq("is_active", True)
            .in_("target_role", [role, "all"])
            .order("sent_at", desc=True)
            .execute()
        )
        return res.data or []
    except Exception as e:
        return []


def add_reminder(message: str, target_role: str, target_dept: str = None,
                 sent_by: str = None, expires_at: str = None) -> bool:
    try:
        client = get_supabase_admin_client()
        payload = {
            "message": message,
            "target_role": target_role,
            "target_dept": target_dept,
            "sent_by": sent_by,
            "expires_at": expires_at,
        }
        client.table("reminders").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"Error adding reminder: {e}")
        return False


def deactivate_reminder(reminder_id: str) -> bool:
    try:
        client = get_supabase_admin_client()
        client.table("reminders").update({"is_active": False}).eq("id", reminder_id).execute()
        return True
    except Exception as e:
        return False


def fetch_all_reminders() -> list[dict]:
    try:
        client = get_supabase_admin_client()
        res = client.table("reminders").select("*").order("sent_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []
