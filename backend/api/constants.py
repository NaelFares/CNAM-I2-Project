"""Shared API constants and lightweight domain helpers."""

ROLE_VALUES = {"both", "driver", "passenger"}

SESSION_COOKIE_NAME = "covoit_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30

MIN_TIME_TOLERANCE = 5
MAX_TIME_TOLERANCE = 60

PREVIEW_CACHE_TTL_SECONDS = 60 * 15
