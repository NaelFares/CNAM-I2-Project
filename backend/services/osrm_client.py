"""Client HTTP pour le serveur OSRM local (service docker "osrm").

Ne connait que l'API OSRM : il transforme une liste de points en itineraire
et ne gere ni cache ni repli, qui sont du ressort de RoutingService.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

# Un serveur local repond en quelques millisecondes : au-dela, il est
# arrete ou encore en train de demarrer, inutile de bloquer la recherche.
REQUEST_TIMEOUT_S = 5


class OsrmClient:
    """Calcule des itineraires voiture via l'API /route d'OSRM."""

    PROFILE = "driving"

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")

    def route(self, points: List[Tuple[float, float]]) -> Optional[Dict]:
        """Returns geometry (lat, lon), distance_m and duration_s, or None.

        `points` are (lat, lon) pairs, in order: start, optional waypoints,
        end. None means OSRM is unreachable or found no route (point outside
        the prepared map, for instance): the caller decides what to do.
        """
        # OSRM attend des coordonnees "lon,lat" separees par des ";".
        coordinates = ";".join(f"{lon},{lat}" for lat, lon in points)
        url = f"{self.base_url}/route/v1/{self.PROFILE}/{coordinates}"
        try:
            response = requests.get(
                url,
                params={"overview": "full", "geometries": "geojson"},
                timeout=REQUEST_TIMEOUT_S,
            )
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("OSRM unreachable (%s): is the osrm container running?", exc)
            return None

        # Erreur metier (NoRoute, NoSegment...) : renvoyee avec un code HTTP 400.
        if data.get("code") != "Ok" or not data.get("routes"):
            logger.warning("OSRM found no route: %s", data.get("code"))
            return None

        best = data["routes"][0]
        return {
            "geometry": [(lat, lon) for lon, lat in best["geometry"]["coordinates"]],
            "distance_m": float(best["distance"]),
            "duration_s": float(best["duration"]),
        }
