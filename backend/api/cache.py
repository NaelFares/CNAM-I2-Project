"""In-memory cache for schedule preview workflow."""

from __future__ import annotations

import time
from collections.abc import Iterable

from backend.api.constants import PREVIEW_CACHE_TTL_SECONDS

_PREVIEW_CACHE: dict[int, tuple[float, list[dict]]] = {}


def set_preview_events(user_id: int, events: Iterable[dict]):
    _PREVIEW_CACHE[user_id] = (time.time() + PREVIEW_CACHE_TTL_SECONDS, list(events))


def get_preview_events(user_id: int) -> list[dict]:
    expiry_and_events = _PREVIEW_CACHE.get(user_id)
    if not expiry_and_events:
        return []
    expiry_ts, events = expiry_and_events
    if time.time() > expiry_ts:
        _PREVIEW_CACHE.pop(user_id, None)
        return []
    return list(events)


def clear_preview_events(user_id: int):
    _PREVIEW_CACHE.pop(user_id, None)
