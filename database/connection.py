"""
database/connection.py - Supabase client management
"""
import streamlit as st
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY


@st.cache_resource
def get_supabase_client() -> Client:
    """Return a cached Supabase anon client."""
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise ValueError(
            "Supabase credentials are missing. "
            "Please set SUPABASE_URL and SUPABASE_ANON_KEY in your .env file."
        )
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


@st.cache_resource
def get_supabase_admin_client() -> Client:
    """Return a cached Supabase admin (service-role) client for elevated ops."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError(
            "Supabase service role key is missing. "
            "Please set SUPABASE_SERVICE_ROLE_KEY in your .env file."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def test_connection() -> bool:
    """Quick connectivity check — returns True on success."""
    try:
        client = get_supabase_client()
        client.table("departments").select("id").limit(1).execute()
        return True
    except Exception:
        return False
