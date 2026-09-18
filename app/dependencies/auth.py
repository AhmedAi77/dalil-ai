"""Authentication dependency shared by protected API routes."""

from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status

from app.models.user import UserRecord
from app.services.auth_service import AuthService, get_auth_service

SESSION_COOKIE = "contexta_session"


def require_user(
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    auth: Annotated[AuthService, Depends(get_auth_service)] = None,
) -> UserRecord:
    user = auth.authenticate(session_token)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user
