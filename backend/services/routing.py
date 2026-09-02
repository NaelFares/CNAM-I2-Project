"""OpenRouteService routing helpers."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import requests

from backend.core.config import config


class RoutingService:
    """Client OpenRouteService pour le calcul d'itinéraires."""

    BASE_URL = "https://api.openrouteservice.org"

    @classmethod
    def _headers(cls) -> dict:
        return {
            "Authorization": config.ORS_API_KEY,
            "Accept": "application/json, application/geo+json",
        }

    @classmethod
    def get_route_geometry(
        cls,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[List[Tuple[float, float]]]:
        """Retourne la liste de points (lat, lon) de l'itinéraire, ou None."""
        start_lat, start_lon = start
        end_lat, end_lon = end
        try:
            response = requests.get(
                f"{cls.BASE_URL}/v2/directions/driving-car",
                params={
                    "start": f"{start_lon},{start_lat}",
                    "end": f"{end_lon},{end_lat}",
                },
                headers=cls._headers(),
                timeout=10,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
            # ORS retourne [lon, lat] → on convertit en (lat, lon)
            coords = features[0]["geometry"]["coordinates"]
            return [(lat, lon) for lon, lat in coords]
        except Exception:
            return None

    @classmethod
    def get_route_alternatives(
        cls,
        start: Tuple[float, float],
        end: Tuple[float, float],
        n: int = 3,
    ) -> Optional[List[List[Tuple[float, float]]]]:
        """Retourne jusqu'à n variantes d'itinéraire, chacune comme liste de (lat, lon)."""
        start_lat, start_lon = start
        end_lat, end_lon = end
        try:
            response = requests.post(
                f"{cls.BASE_URL}/v2/directions/driving-car/geojson",
                headers={**cls._headers(), "Content-Type": "application/json"},
                json={
                    "coordinates": [[start_lon, start_lat], [end_lon, end_lat]],
                    "alternative_routes": {
                        "share_factor": 0.6,
                        "target_count": n,
                        "weight_factor": 1.4,
                    },
                },
                timeout=10,
            )
            if response.status_code != 200:
                single = cls.get_route_geometry(start, end)
                return [single] if single else None
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
            return [[(lat, lon) for lon, lat in f["geometry"]["coordinates"]] for f in features]
        except Exception:
            single = cls.get_route_geometry(start, end)
            return [single] if single else None

    @classmethod
    def get_route_via_waypoint(
        cls,
        start: Tuple[float, float],
        via: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict]:
        """Itinéraire avec un détour par un point intermédiaire (ex. récupération
        d'un passager) : géométrie + distance + durée en un seul appel ORS."""
        try:
            response = requests.post(
                f"{cls.BASE_URL}/v2/directions/driving-car/geojson",
                headers={**cls._headers(), "Content-Type": "application/json"},
                json={
                    "coordinates": [
                        [start[1], start[0]],
                        [via[1], via[0]],
                        [end[1], end[0]],
                    ]
                },
                timeout=10,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]
            summary = features[0]["properties"]["summary"]
            return {
                "geometry": [(lat, lon) for lon, lat in coords],
                "distance_m": float(summary.get("distance", 0.0)),
                "duration_s": float(summary.get("duration", 0.0)),
            }
        except Exception:
            return None

    @classmethod
    def get_route_details(
        cls,
        start: Tuple[float, float],
        end: Tuple[float, float],
    ) -> Optional[Dict]:
        """Géométrie + distance (m) + durée (s) de l'itinéraire, en un seul appel ORS."""
        start_lat, start_lon = start
        end_lat, end_lon = end
        try:
            response = requests.get(
                f"{cls.BASE_URL}/v2/directions/driving-car",
                params={
                    "start": f"{start_lon},{start_lat}",
                    "end": f"{end_lon},{end_lat}",
                },
                headers=cls._headers(),
                timeout=10,
            )
            if response.status_code != 200:
                return None
            data = response.json()
            features = data.get("features", [])
            if not features:
                return None
            coords = features[0]["geometry"]["coordinates"]
            summary = features[0]["properties"]["summary"]
            return {
                "geometry": [(lat, lon) for lon, lat in coords],
                "distance_m": float(summary.get("distance", 0.0)),
                "duration_s": float(summary.get("duration", 0.0)),
            }
        except Exception:
            return None


routing_service = RoutingService()
