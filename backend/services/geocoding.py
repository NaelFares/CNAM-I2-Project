"""
Service de geocodage avec Nominatim (OpenStreetMap).
Permet de rechercher des adresses et obtenir leurs coordonnees GPS.
"""

from typing import Dict, List, Optional

import requests


class GeocodingService:
    """Service de recherche et geocodage d'adresses."""

    BASE_URL = "https://nominatim.openstreetmap.org"
    USER_AGENT = "CovoitEtudiant/1.0"

    @staticmethod
    def _extract_place_label(address_details: Dict) -> str:
        priority_keys = (
            "hamlet",
            "suburb",
            "quarter",
            "neighbourhood",
            "village",
            "town",
            "city_district",
            "city",
            "municipality",
            "county",
            "state",
        )
        for key in priority_keys:
            value = address_details.get(key)
            if value:
                return str(value)
        return ""

    @staticmethod
    def search_address(query: str, limit: int = 5) -> List[Dict]:
        """
        Recherche une adresse et retourne des suggestions.

        Args:
            query: Texte de recherche (ex: "15 rue de la Republique Paris")
            limit: Nombre maximum de resultats

        Returns:
            Liste de dictionnaires avec display_name, place_label, lat, lon.
        """
        if not query or len(query) < 3:
            return []

        try:
            response = requests.get(
                f"{GeocodingService.BASE_URL}/search",
                params={
                    "q": query,
                    "format": "json",
                    "limit": limit,
                    "addressdetails": 1,
                    "countrycodes": "fr",
                },
                headers={"User-Agent": GeocodingService.USER_AGENT},
                timeout=5,
            )

            if response.status_code == 200:
                results = response.json()
                suggestions: List[Dict] = []
                for result in results:
                    address = result.get("address", {}) or {}
                    suggestions.append(
                        {
                            "display_name": result.get("display_name", ""),
                            "place_label": GeocodingService._extract_place_label(address),
                            "lat": float(result.get("lat", 0) or 0),
                            "lon": float(result.get("lon", 0) or 0),
                        }
                    )
                return suggestions
        except Exception as exc:
            print(f"Erreur geocodage: {exc}")

        return []

    @staticmethod
    def reverse_geocode_details(lat: float, lon: float) -> Optional[Dict]:
        """
        Convertit des coordonnees en adresse complete et lieu-dit.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionnaire avec display_name, place_label, lat, lon ou None.
        """
        try:
            response = requests.get(
                f"{GeocodingService.BASE_URL}/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                },
                headers={"User-Agent": GeocodingService.USER_AGENT},
                timeout=5,
            )

            if response.status_code == 200:
                result = response.json()
                address = result.get("address", {}) or {}
                return {
                    "display_name": result.get("display_name", ""),
                    "place_label": GeocodingService._extract_place_label(address),
                    "lat": float(result.get("lat", lat) or lat),
                    "lon": float(result.get("lon", lon) or lon),
                }
        except Exception as exc:
            print(f"Erreur geocodage inverse: {exc}")

        return None

    @staticmethod
    def reverse_geocode(lat: float, lon: float) -> Optional[str]:
        """Compatibilite legacy: retourne uniquement l'adresse texte."""
        result = GeocodingService.reverse_geocode_details(lat, lon)
        if not result:
            return None
        return result.get("display_name") or None


# Instance globale
geocoding_service = GeocodingService()
