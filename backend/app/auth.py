"""
Authentication and Authorization module
Validates Supabase JWTs by calling the Supabase auth API directly.
This avoids needing the raw JWT secret and works with all Supabase token types.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import httpx
import jwt as pyjwt
from datetime import datetime
from app.config import settings


# HTTP Bearer token security
security = HTTPBearer()


class User:
    """User model for authenticated requests"""
    def __init__(self, user_id: str, email: str, role: Optional[str] = None):
        self.id = user_id
        self.email = email
        self.role = role

    def __repr__(self):
        return f"User(id={self.id}, email={self.email}, role={self.role})"


async def verify_supabase_token(token: str) -> dict:
    """
    Verify a Supabase JWT by calling the Supabase auth API.
    Returns the user payload if valid.
    """
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.supabase_url}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.supabase_anon_key,
            }
        )

    if response.status_code == 200:
        return response.json()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error_code": "AUTHENTICATION_FAILED",
            "message": "Invalid or expired token",
            "details": {"supabase_status": response.status_code},
            "timestamp": datetime.utcnow().isoformat()
        }
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Validate JWT token via Supabase and return current user.
    """
    token = credentials.credentials

    try:
        user_data = await verify_supabase_token(token)

        user_id = user_data.get("id")
        email = user_data.get("email")
        role = user_data.get("role", "authenticated")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error_code": "AUTHENTICATION_FAILED",
                    "message": "Invalid token: missing user ID",
                    "details": {},
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

        return User(user_id=user_id, email=email, role=role)

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "AUTHENTICATION_FAILED",
                "message": "Authentication failed",
                "details": {"reason": str(e)},
                "timestamp": datetime.utcnow().isoformat()
            }
        )


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
