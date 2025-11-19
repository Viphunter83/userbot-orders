"""Database module."""

from src.database.supabase_client import SupabaseClient, get_supabase_client

__all__ = ["SupabaseClient", "get_supabase_client"]
