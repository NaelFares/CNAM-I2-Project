"""Estimation d'itineraire de dernier recours, sans aucun service externe.

Utilisee uniquement quand OSRM ne repond pas (conteneur arrete, carte en
cours de preparation, point hors de la zone couverte). Assez fiable pour
classer des conducteurs, approximative pour les durees affichees : le
resultat est donc toujours marque `estimated: True`.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from backend.core.geo import haversine_distance

# La route reelle est en moyenne ~30 % plus longue que la ligne droite
# (detours des rues, ponts, rocade), et la vitesse moyenne d'un trajet
# urbain/periurbain tourne autour de 30 km/h, feux et bouchons compris.
ROAD_FACTOR = 1.3
AVERAGE_SPEED_KMH = 30.0


def estimate_route(points: List[Tuple[float, float]]) -> Dict:
    """Builds an approximate route through (lat, lon) points.

    Distance = straight line between consecutive points x road factor,
    duration = distance / average speed, geometry = straight segments.
    """
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
