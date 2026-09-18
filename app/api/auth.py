"""Account registration and secure cookie-session routes."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status

from app.config import Settings, get_settings
from app.database.auth_repository import EmailAlreadyRegisteredError
from app.dependencies.auth import SESSION_COOKIE, require_user
from app.models.user import UserRecord
from app.schemas.auth import LoginRequest, LogoutResponse, RegisterRequest, UserResponse
from app.services.auth_service import AuthService, InvalidCredentialsError, get_auth_service

router = APIRouter(prefix="/auth", tags=["authentication"])


def _public(user: UserRecord) -> UserResponse:
    return UserResponse(
        id=user.id, name=user.name, email=user.email, created_at=user.created_at
    )


def _set_session(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.auth_session_days * 24 * 60 * 60,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    try:
        user, token = auth.register(
            name=request.name, email=str(request.email), password=request.password
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    _set_session(response, token, settings)
    return _public(user)


@router.post("/login", response_model=UserResponse)
def login(
    request: LoginRequest,
    response: Response,
    auth: Annotated[AuthService, Depends(get_auth_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> UserResponse:
    try:
        user, token = auth.login(email=str(request.email), password=request.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    _set_session(response, token, settings)
    return _public(user)


@router.get("/me", response_model=UserResponse)
def me(user: Annotated[UserRecord, Depends(require_user)], response: Response) -> UserResponse:
    response.headers["Cache-Control"] = "no-store"
    return _public(user)


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
    auth: Annotated[AuthService, Depends(get_auth_service)] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None,
) -> LogoutResponse:
    auth.logout(session_token)
    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
        secure=settings.auth_cookie_secure,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return LogoutResponse(logged_out=True)
