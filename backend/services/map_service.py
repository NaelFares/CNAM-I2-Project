"""
Service de génération de données pour cartes Leaflet (NiceGUI).
Retourne des structures de données pour affichage dans ui.leaflet().
"""
from typing import List, Dict, Tuple

from backend.services.matching import Match
from backend.core.config import config


class MapService:
    """Service de préparation des données cartographiques pour NiceGUI"""

    @staticmethod
    def get_matches_map_data(matches: List[Match]) -> Dict:
        """
        Prépare les données pour afficher une carte des matchs.

        Args:
            matches: Liste des matchs à afficher

        Returns:
            Dictionnaire avec center, zoom et markers
        """
        campus_coords = config.get_campus_coords()

        # Couleurs pour différencier les matchs
        colors = ["blue", "green", "purple", "orange", "red", "darkred", "lightblue", "darkblue", "darkgreen", "cadetblue"]

        markers = []

        # Marqueur du campus
        markers.append({
            "lat": campus_coords[0],
            "lon": campus_coords[1],
            "title": config.CAMPUS_NAME,
            "color": "red",
            "icon": "school",
            "popup": f"<b>{config.CAMPUS_NAME}</b>",
        })

        # Ajouter les matchs
        for idx, match in enumerate(matches):
            color = colors[idx % len(colors)]

            # Conducteur
            markers.append({
                "lat": match.driver_ride.start_lat,
                "lon": match.driver_ride.start_lon,
                "title": f"Conducteur: {match.driver.name}",
                "color": color,
                "icon": "car",
                "popup": f"<b>Conducteur:</b> {match.driver.name}<br><b>Score:</b> {match.score}/100",
            })

            # Passager
            markers.append({
                "lat": match.passenger_ride.start_lat,
                "lon": match.passenger_ride.start_lon,
                "title": f"Passager: {match.passenger.name}",
                "color": color,
                "icon": "person",
                "popup": f"<b>Passager:</b> {match.passenger.name}<br><b>Score:</b> {match.score}/100",
            })

        return {
            "center": campus_coords,
            "zoom": config.DEFAULT_ZOOM,
            "markers": markers,
        }

    @staticmethod
    def get_user_location_map_data(lat: float, lon: float, label: str = "Ma position") -> Dict:
        """
        Prépare les données pour afficher la position d'un utilisateur.

        Args:
            lat: Latitude
            lon: Longitude
            label: Label du marqueur

        Returns:
            Dictionnaire avec center, zoom et markers
        """
        campus_coords = config.get_campus_coords()

        markers = [
            {
                "lat": lat,
                "lon": lon,
                "title": label,
                "color": "blue",
                "icon": "home",
                "popup": f"<b>{label}</b>",
            },
            {
                "lat": campus_coords[0],
                "lon": campus_coords[1],
                "title": config.CAMPUS_NAME,
                "color": "red",
                "icon": "school",
                "popup": f"<b>{config.CAMPUS_NAME}</b>",
            },
        ]

        return {
            "center": (lat, lon),
            "zoom": 13,
            "markers": markers,
        }


# Instance globale
map_service = MapService()
