"""Itinéraire depuis le cache PostgreSQL, sinon OSRM.

Si OSRM répond pas, estimation marquée estimated et jamais mise en cache."""

from __future__ import annotations

import hashlib
import json
from typing import Dict, List, Optional, Sequence, Tuple

from backend.core.config import config
from backend.database.manager import db
from backend.services.osrm_client import OsrmClient
from backend.services.route_estimate import estimate_route


class RoutingService:
    """Cache, puis OSRM, puis estimation si besoin."""

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
        """Itinéraire avec prise en charge puis dépose du passager."""
        return self._get_cached_or_calculate(start, end, waypoints)

    def get_route_details(
        self,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Dict:
        """Tracé, distance et durée du trajet direct."""
        return self._get_cached_or_calculate(start, end)


routing_service = RoutingService()
