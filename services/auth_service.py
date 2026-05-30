"""
services/auth_service.py - Authentication & session management
"""
from __future__ import annotations
import streamlit as st
from database.connection import get_supabase_client, get_supabase_admin_client
from database.queries import fetch_profile

# Set True in production (Supabase email confirmations must be ON)
# Set False during development to skip email verification check
REQUIRE_EMAIL_VERIFICATION = False


# ════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════

def _init_session():
    defaults = {
        "authenticated": False,
        "user": None,
        "profile": None,
        "access_token": None,
        "refresh_token": None,
        "pending_verify_email": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def get_current_user() -> dict | None:
    _init_session()
    return st.session_state.get("user")


def get_current_profile() -> dict | None:
    _init_session()
    return st.session_state.get("profile")


def get_current_role() -> str | None:
    p = get_current_profile()
    return p.get("role") if p else None


def get_current_department() -> str | None:
    p = get_current_profile()
    return p.get("department") if p else None


def is_authenticated() -> bool:
    _init_session()
    return st.session_state.get("authenticated", False)


def is_role(role: str | list) -> bool:
    cur = get_current_role()
    return cur in role if isinstance(role, list) else cur == role


def has_pending_verification() -> bool:
    _init_session()
    return bool(st.session_state.get("pending_verify_email"))


# ════════════════════════════════════════════════════════════
# SIGN-UP
# ════════════════════════════════════════════════════════════

def sign_up(email: str, password: str, full_name: str,
            department: str, role: str = "faculty") -> tuple[bool, str]:
    try:
        client = get_supabase_client()
        res = client.auth.sign_up({
            "email": email,
            "password": password,
            "options": {
                "data": {
                    "full_name": full_name,
                    "department": department,
                    "role": role,
                }
            },
        })
        if res.user:
            if res.user.email_confirmed_at is None and REQUIRE_EMAIL_VERIFICATION:
                return True, "VERIFY_EMAIL"
            return True, "Registration successful! You can now log in."
        return False, "Registration failed. Please try again."
    except Exception as e:
        err = str(e)
        if "already registered" in err.lower() or "already exists" in err.lower():
            return False, "An account with this email already exists."
        return False, f"Error: {err}"


# ════════════════════════════════════════════════════════════
# SIGN-IN
# ════════════════════════════════════════════════════════════

def sign_in(email: str, password: str) -> tuple[bool, str]:
    _init_session()
    try:
        client = get_supabase_client()
        res = client.auth.sign_in_with_password({"email": email, "password": password})

        if not res.user:
            return False, "Invalid email or password."

        # Email verification check
        if REQUIRE_EMAIL_VERIFICATION and not res.user.email_confirmed_at:
            client.auth.sign_out()
            st.session_state["pending_verify_email"] = email
            return False, "EMAIL_NOT_VERIFIED"

        # Fetch profile with detailed error handling
        try:
            profile = fetch_profile(res.user.id)
        except Exception as e:
            st.error(f"Database error querying schema (fetch_profile): {e}")
            return False, f"Profile fetch error: {e}"

        if not profile:
            # Fallback: create profile if trigger failed
            try:
                admin_client = get_supabase_admin_client()
                meta = res.user.user_metadata or {}
                new_profile = {
                    "id": res.user.id,
                    "full_name": meta.get("full_name", "Unknown User"),
                    "email": res.user.email,
                    "department": meta.get("department"),
                    "role": meta.get("role", "faculty"),
                    "is_active": True
                }
                admin_client.table("profiles").insert(new_profile).execute()
                profile = fetch_profile(res.user.id)
                if not profile:
                    return False, "Failed to create profile row. Contact administrator."
            except Exception as e:
                st.error(f"Profile synchronization database error: {e}")
                return False, f"Profile synchronization error: {e}"

        if not profile.get("is_active", True):
            client.auth.sign_out()
            return False, "Your account has been deactivated. Contact administrator."

        st.session_state["authenticated"]    = True
        st.session_state["user"]             = {"id": res.user.id, "email": res.user.email}
        st.session_state["profile"]          = profile
        st.session_state["access_token"]     = res.session.access_token
        st.session_state["refresh_token"]    = res.session.refresh_token
        st.session_state["pending_verify_email"] = None

        return True, f"Welcome back, {profile['full_name']}!"
    except Exception as e:
        err = str(e)
        if "invalid" in err.lower() or "credentials" in err.lower():
            return False, "Invalid email or password."
        return False, f"Login error: {err}"


# ════════════════════════════════════════════════════════════
# SIGN-OUT
# ════════════════════════════════════════════════════════════

def sign_out():
    try:
        get_supabase_client().auth.sign_out()
    except Exception:
        pass
    for k in ["authenticated", "user", "profile", "access_token",
              "refresh_token", "pending_verify_email"]:
        st.session_state[k] = None
    st.session_state.pop("current_page", None)
    st.session_state["authenticated"] = False
    st.rerun()


# ════════════════════════════════════════════════════════════
# EMAIL VERIFICATION
# ════════════════════════════════════════════════════════════

def resend_verification_email(email: str) -> tuple[bool, str]:
    try:
        client = get_supabase_client()
        client.auth.resend({"type": "signup", "email": email})
        return True, "Verification email resent. Please check your inbox."
    except Exception as e:
        return False, f"Could not resend: {e}"


def clear_pending_verification():
    _init_session()
    st.session_state["pending_verify_email"] = None


# ════════════════════════════════════════════════════════════
# PASSWORD RESET
# ════════════════════════════════════════════════════════════

def request_password_reset(email: str) -> tuple[bool, str]:
    try:
        get_supabase_client().auth.reset_password_email(email)
        return True, "Password reset email sent. Check your inbox."
    except Exception as e:
        return False, f"Error: {e}"


# ════════════════════════════════════════════════════════════
# ADMIN USER MANAGEMENT
# ════════════════════════════════════════════════════════════

def admin_create_user(email: str, password: str, full_name: str,
                      department: str, role: str) -> tuple[bool, str]:
    try:
        client = get_supabase_admin_client()
        res = client.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": full_name,
                "department": department,
                "role": role,
            },
        })
        if res.user:
            return True, f"User '{full_name}' created successfully."
        return False, "Failed to create user."
    except Exception as e:
        return False, f"Error: {e}"


def admin_delete_user(user_id: str) -> tuple[bool, str]:
    try:
        get_supabase_admin_client().auth.admin.delete_user(user_id)
        return True, "User deleted."
    except Exception as e:
        return False, f"Error: {e}"
