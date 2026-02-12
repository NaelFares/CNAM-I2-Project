"""Signed session cookie helpers for API auth."""

from __future__ import annotations

import base64
import hashlib
import hmac
import time
from dataclasses import dataclass

from backend.core.config import config


@dataclass(frozen=True)
class SessionPayload:
    user_id: int
    email: str
    exp: int


def _secret_bytes() -> bytes:
    return config.STORAGE_SECRET.encode("utf-8")


def _sign(raw_payload: str) -> str:
    return hmac.new(_secret_bytes(), raw_payload.encode("utf-8"), hashlib.sha256).hexdigest()


def create_session_token(user_id: int, email: str, ttl_seconds: int) -> str:
    exp = int(time.time()) + ttl_seconds
    raw = f"{user_id}:{email}:{exp}"
    signature = _sign(raw)
    wire = f"{raw}:{signature}".encode("utf-8")
    return base64.urlsafe_b64encode(wire).decode("utf-8")


def parse_session_token(token: str) -> SessionPayload | None:
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        user_id_raw, email, exp_raw, signature = decoded.rsplit(":", 3)
        raw = f"{user_id_raw}:{email}:{exp_raw}"
        expected = _sign(raw)
        if not hmac.compare_digest(expected, signature):
            return None

        user_id = int(user_id_raw)
        exp = int(exp_raw)
        if exp < int(time.time()):
            return None

        return SessionPayload(user_id=user_id, email=email, exp=exp)
    except Exception:
        return None
