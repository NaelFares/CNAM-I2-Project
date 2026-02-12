"""API-level helpers for standardized feedback responses."""

from __future__ import annotations

from fastapi import HTTPException, status

from backend.messages import get_message


def make_feedback(code: str, **kwargs) -> dict[str, str]:
    return {"code": code, "message": get_message(code, **kwargs)}


def raise_api_error(code: str, http_status: int = status.HTTP_400_BAD_REQUEST, **kwargs):
    raise HTTPException(status_code=http_status, detail=make_feedback(code, **kwargs))
