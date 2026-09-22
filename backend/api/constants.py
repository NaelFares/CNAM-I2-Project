"""Shared API constants and lightweight domain helpers."""

ROLE_VALUES = {"driver", "passenger"}

MIN_CAR_SEATS = 1
MAX_CAR_SEATS = 4

SESSION_COOKIE_NAME = "covoit_session"
SESSION_TTL_SECONDS = 60 * 60 * 24 * 30

MIN_TIME_TOLERANCE = 5
MAX_TIME_TOLERANCE = 60

PREVIEW_CACHE_TTL_SECONDS = 60 * 15
