"""Dependency providers for FastAPI routes."""

from __future__ import annotations

from fastapi import Depends, Request, status

from backend.database.manager import db
from backend.models.user import User

from backend.api.constants import SESSION_COOKIE_NAME
from backend.api.feedback import raise_api_error
from backend.api.session import parse_session_token


def get_current_user(request: Request) -> User | None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        return None

    payload = parse_session_token(token)
    if not payload:
        return None

    user = db.get_user_by_id(payload.user_id)
    if not user:
        return None
    if user.email != payload.email:
        return None
    return user


def require_current_user(user: User | None = Depends(get_current_user)) -> User:
    if not user:
        raise_api_error("AUTH_EMAIL_REQUIRED", http_status=status.HTTP_401_UNAUTHORIZED)
    return user
