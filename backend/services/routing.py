"""Routing facade used by the rest of the application.

Each route request goes through three layers, in order:
1. the persistent PostgreSQL cache (`routing_cache`);
2. the local OSRM server (see osrm_client.py and docker-compose.osrm.yml);
3. a straight-line estimate (see route_estimate.py) if OSRM cannot answer.

Callers always get a result. Estimated routes are flagged with
``estimated: True`` and never cached, so the real route is computed as
soon as OSRM is back.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional, Sequence, Tuple

from backend.core.config import config
from backend.database.manager import db
from backend.services.osrm_client import OsrmClient
from backend.services.route_estimate import estimate_route


class RoutingService:
    """Cached route computation with an always-available fallback."""

    PROVIDER = "osrm"
    PROFILE = "driving"
    # v2 : passage d'ORS a OSRM. Changer la version ignore les anciennes
    # entrees du cache sans avoir a le vider.
    CACHE_VERSION = "v2"

    def __init__(self, client: Optional[OsrmClient] = None) -> None:
        self.client = client or OsrmClient(config.OSRM_URL)

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

    def _get_cached_or_calculate(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
        waypoints: Sequence[Tuple[float, float]] = (),
    ) -> Dict:
        points = [start, *waypoints, end]
        cache_key = self._cache_key(points)
        cached = db.get_routing_cache(cache_key)
        if cached:
            return {
                "geometry": cached["geometry"],
                "distance_m": float(cached["distance_m"]),
                "duration_s": float(cached["duration_s"]),
                "estimated": False,
            }

        result = self.client.route(points)
        if not result:
            # OSRM indisponible ou sans itineraire : estimation, jamais mise
            # en cache. La cause est deja loguee par le client.
            return estimate_route(points)

        db.upsert_routing_cache(
            cache_key=cache_key,
            start=start,
            # La cle couvre tous les points ; la colonne via ne garde que le
            # premier (prise en charge), a titre indicatif.
            via=waypoints[0] if waypoints else None,
            end=end,
            result=result,
            provider=self.PROVIDER,
            profile=self.PROFILE,
        )
        return {**result, "estimated": False}

    def get_route_via_waypoints(
        self,
        start: Tuple[float, float],
        waypoints: Sequence[Tuple[float, float]],
        end: Tuple[float, float],
    ) -> Dict:
        """Returns a route through waypoints, in order (passenger pickup,
        then drop-off)."""
        return self._get_cached_or_calculate(start, end, waypoints)

    def get_route_details(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Dict:
        """Returns geometry, distance and duration for a direct route."""
        return self._get_cached_or_calculate(start, end)


routing_service = RoutingService()
