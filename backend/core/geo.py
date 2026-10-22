"""Distances et coordonnées."""
import math


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance en km par Haversine ; coordonnées en degrés."""
    # Rayon de la Terre en km
    R = 6371.0

    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return round(distance, 2)


def is_valid_coords(lat: float, lon: float) -> bool:
    """Latitude et longitude dans les bornes."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def format_coords(lat: float, lon: float) -> str:
    """Affichage avec quatre décimales."""
    return f"{lat:.4f}, {lon:.4f}"
