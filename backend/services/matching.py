"""
Moteur de recommandation de covoiturage basé sur l'itinéraire.

Critères primaires (filtre d'éligibilité) :
  1. Horaires d'arrivée dans la tolérance des deux utilisateurs (score 0-50)
  2. Point de départ passager à moins de MAX_ROUTE_DETOUR_KM d'un point du trajet conducteur (score 0-50)

Critères secondaires (classement) :
  - Proximité des points de départ (tiebreaker)
  - Proximité des points d'arrivée (tiebreaker)
"""

from typing import Dict, List, Optional, Tuple

from backend.core.config import config
from backend.core.geo import haversine_distance
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.routing import routing_service


class Match:
    """Représente une paire conducteur/passager avec son score de compatibilité."""

    def __init__(
        self,
        driver: User,
        passenger: User,
        driver_ride: Ride,
        passenger_ride: Ride,
        route_points: List[Tuple[float, float]],
    ):
        self.driver = driver
        self.passenger = passenger
        self.driver_ride = driver_ride
        self.passenger_ride = passenger_ride
        self.route_points = route_points
        self.score = 0
        self.time_diff_min = 0
        self.distance_km = 0.0       # distance min passager → trajet conducteur
        self.departure_distance_km = 0.0
        self._calculate_score()

    def _calculate_score(self):
        # --- Critère primaire 1 : horaires ---
        time_diff = abs(
            (self.driver_ride.ride_time - self.passenger_ride.ride_time).total_seconds() / 60
        )
        self.time_diff_min = int(time_diff)
        max_tolerance = max(1, self.driver.time_tolerance_min, self.passenger.time_tolerance_min)
        if time_diff <= max_tolerance:
            time_score = 50 * (1 - time_diff / max_tolerance)
        else:
            time_score = 0

        # --- Critère primaire 2 : proximité passager ↔ itinéraire conducteur ---
        min_dist = routing_service.min_distance_to_route(
            self.passenger_ride.start_lat,
            self.passenger_ride.start_lon,
            self.route_points,
        )
        self.distance_km = round(min_dist, 2)
        max_detour = config.MAX_ROUTE_DETOUR_KM
        if min_dist <= max_detour:
            route_score = 50 * (1 - min_dist / max_detour)
        else:
            route_score = 0

        # --- Critère secondaire : proximité des départs (tiebreaker, 0-10 pts bonus) ---
        dep_dist = haversine_distance(
            self.driver_ride.start_lat,
            self.driver_ride.start_lon,
            self.passenger_ride.start_lat,
            self.passenger_ride.start_lon,
        )
        self.departure_distance_km = round(dep_dist, 2)
        max_dep = config.MAX_DISTANCE_KM
        departure_bonus = 10 * (1 - min(dep_dist, max_dep) / max_dep)

        self.score = int(time_score + route_score + departure_bonus)

    def to_dict(self) -> Dict:
        return {
            "driver_name": self.driver.name,
            "driver_id": self.driver.id,
            "passenger_name": self.passenger.name,
            "passenger_id": self.passenger.id,
            "ride_time": self.driver_ride.format_time(),
            "ride_type": self.driver_ride.get_direction_label(),
            "time_diff_min": self.time_diff_min,
            "distance_km": self.distance_km,
            "score": self.score,
            "driver_coords": (self.driver_ride.start_lat, self.driver_ride.start_lon),
            "passenger_coords": (self.passenger_ride.start_lat, self.passenger_ride.start_lon),
            "campus_coords": (self.driver_ride.end_lat, self.driver_ride.end_lon),
            "route_geometry": [[lat, lon] for lat, lon in self.route_points],
            "route_distance_km": self.distance_km,
        }


class MatchingService:
    """Service de matching conducteur/passager."""

    @staticmethod
    def _get_route_cached(
        cache: Dict,
        driver_ride: Ride,
    ) -> List[Tuple[float, float]]:
        """Récupère l'itinéraire du conducteur depuis le cache ou via ORS."""
        key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
        if key not in cache:
            points = routing_service.get_route_geometry(
                (driver_ride.start_lat, driver_ride.start_lon),
                (driver_ride.end_lat, driver_ride.end_lon),
            )
            cache[key] = points or []
        return cache[key]

    @staticmethod
    def find_matches(current_user: User, my_rides: List[Ride], all_rides: List[Ride]) -> List[Dict]:
        """
        Trouve les trajets compatibles pour l'utilisateur courant.
        Critère principal : le point de départ du passager doit se trouver
        à moins de MAX_ROUTE_DETOUR_KM d'un point de l'itinéraire du conducteur.
        """
        matches: List[Match] = []
        route_cache: Dict = {}

        for my_ride in my_rides:
            for other_ride in all_rides:
                if other_ride.user_id == current_user.id:
                    continue
                if my_ride.ride_type != other_ride.ride_type:
                    continue

                other_user = db.get_user_by_id(other_ride.user_id)
                if not other_user:
                    continue

                if current_user.is_driver() and other_user.is_passenger():
                    driver, passenger = current_user, other_user
                    driver_ride, passenger_ride = my_ride, other_ride
                elif current_user.is_passenger() and other_user.is_driver():
                    driver, passenger = other_user, current_user
                    driver_ride, passenger_ride = other_ride, my_ride
                else:
                    continue

                route_points = MatchingService._get_route_cached(route_cache, driver_ride)

                match = Match(driver, passenger, driver_ride, passenger_ride, route_points)
                if match.score >= config.MIN_MATCH_SCORE:
                    matches.append(match)

        # Tri principal par score, secondaire par distance au trajet (asc)
        matches.sort(key=lambda m: (-m.score, m.distance_km))
        return [match.to_dict() for match in matches]


matching_service = MatchingService()
