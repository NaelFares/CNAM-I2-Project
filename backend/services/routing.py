"""OSRM routing helpers (prepared for future UI usage)."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import requests


class RoutingService:
    """Lightweight OSRM client for distance and route previews."""

    BASE_URL = "https://router.project-osrm.org"

    @staticmethod
    def _build_coords(start: Tuple[float, float], end: Tuple[float, float]) -> str:
        start_lat, start_lon = start
        end_lat, end_lon = end
        return f"{start_lon},{start_lat};{end_lon},{end_lat}"

    @classmethod
    def route_between_points(
        cls,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict]:
        """Return the best route payload from OSRM, or None."""
        coords = cls._build_coords(start, end)
        try:
            response = requests.get(
                f"{cls.BASE_URL}/route/v1/driving/{coords}",
                params={"overview": "full", "geometries": "geojson"},
                timeout=5,
            )
            if response.status_code != 200:
                return None
            payload = response.json()
            routes = payload.get("routes", [])
            if not routes:
                return None
            return routes[0]
        except Exception:
            return None

    @classmethod
    def distance_duration_between_points(
        cls,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict[str, float]]:
        """Return distance (m) and duration (s) for the best route."""
        route = cls.route_between_points(start, end)
        if not route:
            return None
        return {
            "distance_m": float(route.get("distance", 0.0) or 0.0),
            "duration_s": float(route.get("duration", 0.0) or 0.0),
        }


routing_service = RoutingService()
