"""Le passager est-il sur la route du conducteur ?

Fonctions pures, sans appel reseau : elles comparent des points a la
geometrie d'un itineraire deja calcule (liste de points (lat, lon)).
Elles servent a choisir les candidats ; c'est ensuite le vrai detour,
calcule par OSRM, qui decide.
"""

from __future__ import annotations

import math
from typing import List, NamedTuple, Optional, Sequence, Tuple

Point = Tuple[float, float]

# Conversion degres -> km, suffisante a l'echelle d'une agglomeration.
KM_PER_DEGREE_LAT = 110.57


class RouteFit(NamedTuple):
    """Position du passager par rapport a la route du conducteur."""

    pickup_km: float
    dropoff_km: float

    @property
    def max_km(self) -> float:
        return max(self.pickup_km, self.dropoff_km)


def _to_km(point: Point, ref_lat: float) -> Tuple[float, float]:
    """Projection plane locale (x, y) en km autour de la latitude ref_lat."""
    lat, lon = point
    return (lon * KM_PER_DEGREE_LAT * math.cos(math.radians(ref_lat)), lat * KM_PER_DEGREE_LAT)


def nearest_on_route(point: Point, route: Sequence[Point]) -> Tuple[float, float]:
    """Distance (km) du point a la route, et position du point le plus
    proche le long de la route (indice de segment + fraction, pour comparer
    l'ordre de deux points).

    On mesure la distance a chaque segment, pas seulement aux sommets : un
    itineraire estime (ligne droite) n'a que deux points.
    """
    if not route:
        return math.inf, 0.0
    if len(route) == 1:
        route = [route[0], route[0]]
    ref_lat = point[0]
    px, py = _to_km(point, ref_lat)
    best = (math.inf, 0.0)
    for index, (a, b) in enumerate(zip(route, route[1:])):
        ax, ay = _to_km(a, ref_lat)
        bx, by = _to_km(b, ref_lat)
        dx, dy = bx - ax, by - ay
        length2 = dx * dx + dy * dy
        t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
        distance = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
        if distance < best[0]:
            best = (distance, index + t)
    return best


def fit_on_route(
    route: Sequence[Point],
    pickup: Optional[Point],
    dropoff: Optional[Point],
    max_km: float,
) -> Optional[RouteFit]:
    """Le passager peut-il etre pris puis depose le long de cette route ?

    `pickup` ou `dropoff` a None : point confondu avec le depart ou
    l'arrivee du conducteur (meme campus), donc forcement sur la route.
    Retourne None si un point est trop loin de la route, ou si la depose
    arrive avant la prise en charge (le passager va dans l'autre sens).
    """
    pickup_km, pickup_pos = (0.0, 0.0) if pickup is None else nearest_on_route(pickup, route)
    dropoff_km, dropoff_pos = (0.0, math.inf) if dropoff is None else nearest_on_route(dropoff, route)
    if pickup_km > max_km or dropoff_km > max_km:
        return None
    if dropoff_pos < pickup_pos:
        return None
    return RouteFit(pickup_km=round(pickup_km, 2), dropoff_km=round(dropoff_km, 2))


def route_points(geometry: List) -> List[Point]:
    """Geometrie du cache ([lat, lon]) ou d'OSRM ((lat, lon)) -> tuples."""
    return [(float(lat), float(lon)) for lat, lon in geometry]
