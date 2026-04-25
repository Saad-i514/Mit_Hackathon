"""
Pytest configuration and shared fixtures for AI Scientist Platform tests.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Set test environment variables before any imports
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("OPENAI_API_KEY", "test-key-not-real")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "test-anon-key")
os.environ.setdefault("SUPABASE_SERVICE_KEY", "test-service-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "test-jwt-secret-at-least-32-chars-long")
os.environ.setdefault("SEMANTIC_SCHOLAR_API_KEY", "test-ss-key")
os.environ.setdefault("SERPER_API_KEY", "test-serper-key")
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

# Patch supabase client creation before any app imports to avoid "Invalid API key" errors
_mock_supabase_client = MagicMock()
_supabase_patcher = patch("supabase.create_client", return_value=_mock_supabase_client)
_supabase_patcher.start()


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use default event loop policy for tests"""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def anyio_backend():
    return "asyncio"
