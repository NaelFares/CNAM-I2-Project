"""OpenRouteService routing helpers with persistent caching and quota protection."""

from __future__ import annotations

from collections import deque
import hashlib
import json
import logging
import threading
import time
from typing import Dict, List, Optional, Tuple

import requests

from backend.core.config import config
from backend.database.manager import db

logger = logging.getLogger(__name__)


class RoutingProviderError(RuntimeError):
    """Base error raised when the external routing provider cannot be used."""


class RoutingQuotaExceededError(RoutingProviderError):
    """The ORS daily quota is exhausted."""


class RoutingRateLimitError(RoutingProviderError):
    """The ORS minute limit is reached."""


class RoutingService:
    """ORS client with a PostgreSQL cache and a local request limiter."""

    BASE_URL = "https://api.openrouteservice.org"
    PROVIDER = "ors"
    PROFILE = "driving-car"
    CACHE_VERSION = "v1"

    def __init__(self) -> None:
        self._request_timestamps: deque[float] = deque()
        self._quota_lock = threading.Lock()
        self._blocked_until = 0.0
        self._blocked_reason = ""
        self.remaining_daily_quota: Optional[int] = None

    @classmethod
    def _headers(cls) -> dict:
        return {
            "Authorization": config.ORS_API_KEY,
            "Accept": "application/json, application/geo+json",
        }

    @classmethod
    def _cache_key(cls, points: List[Tuple[float, float]]) -> str:
        rounded_points = [[round(lat, 5), round(lon, 5)] for lat, lon in points]
        payload = json.dumps(
            {
                "version": cls.CACHE_VERSION,
                "provider": cls.PROVIDER,
                "profile": cls.PROFILE,
                "points": rounded_points,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _reserve_request_slot(self) -> None:
        now_wall = time.time()
        now_monotonic = time.monotonic()
        with self._quota_lock:
            if self._blocked_until > now_wall:
                if self._blocked_reason == "daily":
                    raise RoutingQuotaExceededError("ORS daily quota exhausted")
                raise RoutingRateLimitError("ORS request limit reached")

            while self._request_timestamps and now_monotonic - self._request_timestamps[0] >= 60:
                self._request_timestamps.popleft()

            safe_limit = max(1, min(config.ORS_MAX_REQUESTS_PER_MINUTE, 39))
            if len(self._request_timestamps) >= safe_limit:
                self._blocked_until = now_wall + 60
                self._blocked_reason = "minute"
                raise RoutingRateLimitError("Local ORS safety limit reached")

            self._request_timestamps.append(now_monotonic)

    def _block_provider(self, reason: str, response: requests.Response) -> None:
        now = time.time()
        if reason == "daily":
            blocked_until = now + 15 * 60
            reset_value = response.headers.get("x-ratelimit-reset")
            if reset_value:
                try:
                    parsed_reset = float(reset_value)
                    blocked_until = parsed_reset if parsed_reset > now else now + max(60, parsed_reset)
                except ValueError:
                    pass
        else:
            retry_after = response.headers.get("retry-after", "60")
            try:
                blocked_until = now + max(1, int(retry_after))
            except ValueError:
                blocked_until = now + 60

        with self._quota_lock:
            self._blocked_until = blocked_until
            self._blocked_reason = reason

    def _update_quota_information(self, response: requests.Response) -> None:
        remaining = response.headers.get("x-ratelimit-remaining")
        if remaining is not None:
            try:
                self.remaining_daily_quota = int(remaining)
            except ValueError:
                self.remaining_daily_quota = None

    def _request(self, method: str, path: str, **kwargs) -> Optional[dict]:
        if not config.ORS_API_KEY:
            logger.warning("ORS_API_KEY is not configured.")
            return None

        self._reserve_request_slot()
        try:
            response = requests.request(
                method,
                f"{self.BASE_URL}{path}",
                headers=self._headers(),
                timeout=10,
                **kwargs,
            )
        except requests.RequestException as exc:
            logger.warning("ORS request failed: %s", exc)
            return None

        self._update_quota_information(response)
        if response.status_code == 403:
            self._block_provider("daily", response)
            raise RoutingQuotaExceededError("ORS daily quota exhausted")
        if response.status_code == 429:
            self._block_provider("minute", response)
            raise RoutingRateLimitError("ORS request limit reached")
        if response.status_code != 200:
            logger.warning("ORS returned HTTP %s.", response.status_code)
            return None

        try:
            return response.json()
        except ValueError:
            logger.warning("ORS returned an invalid JSON response.")
            return None

    @staticmethod
    def _result_from_geojson(data: Optional[dict]) -> Optional[Dict]:
        if not data:
            return None
        features = data.get("features", [])
        if not features:
            return None
        feature = features[0]
        coordinates = feature.get("geometry", {}).get("coordinates", [])
        if not coordinates:
            return None
        summary = feature.get("properties", {}).get("summary", {})
        return {
            "geometry": [(lat, lon) for lon, lat in coordinates],
            "distance_m": float(summary.get("distance", 0.0)),
            "duration_s": float(summary.get("duration", 0.0)),
        }

    def _get_cached_or_calculate(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        via: Optional[Tuple[float, float]] = None,
    ) -> Optional[Dict]:
        points = [start, *([via] if via else []), end]
        cache_key = self._cache_key(points)
        cached = db.get_routing_cache(cache_key)
        if cached:
            return {
                "geometry": cached["geometry"],
                "distance_m": float(cached["distance_m"]),
                "duration_s": float(cached["duration_s"]),
            }

        coordinates = [[point[1], point[0]] for point in points]
        data = self._request(
            "POST",
            f"/v2/directions/{self.PROFILE}/geojson",
            json={"coordinates": coordinates},
        )
        result = self._result_from_geojson(data)
        if result:
            db.upsert_routing_cache(
                cache_key=cache_key,
                start=start,
                via=via,
                end=end,
                result=result,
                provider=self.PROVIDER,
                profile=self.PROFILE,
            )
        return result

    def get_route_geometry(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[List[Tuple[float, float]]]:
        """Returns route points as (lat, lon), using the persistent cache."""
        details = self._get_cached_or_calculate(start, end)
        return details["geometry"] if details else None

    def get_route_alternatives(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        n: int = 3,
    ) -> Optional[List[List[Tuple[float, float]]]]:
        """Returns up to n alternative geometries."""
        data = self._request(
            "POST",
            f"/v2/directions/{self.PROFILE}/geojson",
            json={
                "coordinates": [[start[1], start[0]], [end[1], end[0]]],
                "alternative_routes": {
                    "share_factor": 0.6,
                    "target_count": n,
                    "weight_factor": 1.4,
                },
            },
        )
        if not data:
            single = self.get_route_geometry(start, end)
            return [single] if single else None
        features = data.get("features", [])
        routes = []
        for feature in features:
            coordinates = feature.get("geometry", {}).get("coordinates", [])
            if coordinates:
                routes.append([(lat, lon) for lon, lat in coordinates])
        return routes or None

    def get_route_via_waypoint(
        self,
        start: Tuple[float, float],
        via: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict]:
        """Returns a route through a passenger pickup point."""
        return self._get_cached_or_calculate(start, end, via=via)

    def get_route_details(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict]:
        """Returns geometry, distance and duration for a direct route."""
        return self._get_cached_or_calculate(start, end)


routing_service = RoutingService()
