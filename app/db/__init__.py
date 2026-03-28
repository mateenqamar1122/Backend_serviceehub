"""
Database package initialization.
"""
from app.db.base import BaseModel
from app.db.session import get_supabase, supabase_client

__all__ = [
    "BaseModel",
    "get_supabase",
    "supabase_client",
]

