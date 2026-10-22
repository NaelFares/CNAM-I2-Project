"""Estimation de secours quand OSRM répond pas ou ne trouve pas de route.

Tracé en ligne droite, distance et durée approximatives (estimated: True)."""

from __future__ import annotations

from typing import Dict, List, Tuple

from backend.core.geo import haversine_distance

# Hypothèses de secours : distance x 1,3 et vitesse de 30 km/h.
# Pas calibré sur des trajets réels.
ROAD_FACTOR = 1.3
AVERAGE_SPEED_KMH = 30.0


def estimate_route(points: List[Tuple[float, float]]) -> Dict:
    """Estimation entre les points (lat, lon), avec un tracé en ligne droite."""
    straight_km = sum(
        haversine_distance(a[0], a[1], b[0], b[1])
        for a, b in zip(points, points[1:])
    )
    road_km = straight_km * ROAD_FACTOR
    return {
        "geometry": list(points),
        "distance_m": road_km * 1000,
        "duration_s": road_km / AVERAGE_SPEED_KMH * 3600,
        "estimated": True,
    }
