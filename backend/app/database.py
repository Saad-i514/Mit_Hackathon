"""
Database client and utilities for Supabase
"""
from supabase import create_client, Client
from typing import Optional
from app.config import settings


class DatabaseClient:
    """Supabase database client wrapper — lazy initialization"""

    def __init__(self):
        self._client: Optional[Client] = None

    def get_client(self) -> Client:
        """Get or create the Supabase client instance"""
        if self._client is None:
            if not settings.supabase_url or not settings.supabase_service_key:
                raise RuntimeError(
                    "SUPABASE_URL and SUPABASE_SERVICE_KEY must be set. "
                    "Add them as environment variables in Railway."
                )
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_service_key
            )
        return self._client


# Global database client instance (lazy)
db_client = DatabaseClient()


def get_db() -> Client:
    """
    Dependency function to get database client.
    Use this in FastAPI route dependencies.
    """
    return db_client.get_client()


# Alias for backward compatibility
get_db_session = get_db
