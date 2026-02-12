"""
Utilitaires géographiques pour calculs de distance et manipulation de coordonnées.
Utilise la formule de Haversine pour calculer la distance entre deux points.
"""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcule la distance entre deux points géographiques en km.
    Utilise la formule de Haversine.

    Args:
        lat1: Latitude du point 1 (degrés)
        lon1: Longitude du point 1 (degrés)
        lat2: Latitude du point 2 (degrés)
        lon2: Longitude du point 2 (degrés)

    Returns:
        Distance en kilomètres
    """
    # Rayon de la Terre en km
    R = 6371.0

    # Conversion en radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Différences
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Formule de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


def is_valid_coords(lat: float, lon: float) -> bool:
    """
    Vérifie si les coordonnées sont valides.

    Args:
        lat: Latitude (degrés)
        lon: Longitude (degrés)

    Returns:
        True si les coordonnées sont valides
    """
    return -90 <= lat <= 90 and -180 <= lon <= 180


def format_coords(lat: float, lon: float) -> str:
    """
    Formate les coordonnées pour l'affichage.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Chaîne formatée (ex: "48.8566, 2.3522")
    """
    return f"{lat:.4f}, {lon:.4f}"
