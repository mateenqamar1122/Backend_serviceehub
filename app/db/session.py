"""
Supabase client configuration for database operations.
"""
from supabase import create_client, Client

from app.core.config import settings

# Initialize Supabase client
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_key,
)


def get_supabase() -> Client:
    """
    Get Supabase client dependency.

    Usage in endpoints:
        async def my_endpoint(supabase: Client = Depends(get_supabase)):
            response = supabase.table('users').select('*').execute()
    """
    return supabase_client

