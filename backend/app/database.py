"""
Database client and utilities for Supabase
"""
from supabase import create_client, Client
from typing import Optional
from app.config import settings


class DatabaseClient:
    """Supabase database client wrapper"""
    
    def __init__(self):
        """Initialize Supabase client with service key for full access"""
        self.client: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    def get_client(self) -> Client:
        """Get the Supabase client instance"""
        return self.client


# Global database client instance
db_client = DatabaseClient()


def get_db() -> Client:
    """
    Dependency function to get database client.
    Use this in FastAPI route dependencies.
    """
    return db_client.get_client()


# Alias for backward compatibility
get_db_session = get_db
