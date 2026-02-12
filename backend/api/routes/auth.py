"""Authentication/session endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status

from backend.database.manager import db

from backend.api.constants import SESSION_COOKIE_NAME, SESSION_TTL_SECONDS
from backend.api.deps import get_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import LoginRequest, LoginResponse, RegisterRequest, SessionResponse, UserDTO
from backend.api.session import create_session_token
from backend.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, user_id: int, email: str):
    token = create_session_token(user_id=user_id, email=email, ttl_seconds=SESSION_TTL_SECONDS)
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response):
    email = str(payload.email).strip().lower()
    user = db.get_user_by_email(email)
    if not user:
        return LoginResponse(
            status="register_required",
            user=None,
            feedback=make_feedback("AUTH_UNKNOWN_EMAIL_REDIRECT"),
        )

    _set_session_cookie(response, user.id, user.email)
    return LoginResponse(
        status="ok",
        user=UserDTO(**user.to_dict()),
        feedback=make_feedback("PROFILE_SAVE_SUCCESS"),
    )


@router.post("/register", response_model=LoginResponse)
def register(payload: RegisterRequest, response: Response):
    existing = db.get_user_by_email(str(payload.email).strip().lower())
    if existing:
        raise_api_error("REGISTER_REQUIRED_FIELDS", http_status=status.HTTP_409_CONFLICT)

    if payload.time_tolerance_min < 5 or payload.time_tolerance_min > 60:
        raise_api_error("VALIDATION_TIME_TOLERANCE_INVALID")

    user = User(
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        role=payload.role,
        start_address=payload.start_address.strip(),
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        time_tolerance_min=payload.time_tolerance_min,
    )
    user.id = db.create_user(user)
    _set_session_cookie(response, user.id, user.email)

    return LoginResponse(
        status="ok",
        user=UserDTO(**user.to_dict()),
        feedback=make_feedback("PROFILE_SAVE_SUCCESS"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


@router.get("/session", response_model=SessionResponse)
def session(user=Depends(get_current_user)):
    if not user:
        return SessionResponse(authenticated=False, user=None)
    return SessionResponse(authenticated=True, user=UserDTO(**user.to_dict()))
