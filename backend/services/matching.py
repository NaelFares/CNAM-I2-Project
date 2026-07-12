"""
Moteur de recommandation de covoiturage basé sur l'itinéraire.

Critères primaires (filtre d'éligibilité) :
  1. Horaires d'arrivée dans la tolérance des deux utilisateurs (score 0-50)
  2. Temps de détour réel pour aller récupérer le passager (aller direct vs
     aller-via-passager, calculé par le moteur de routing), en dessous de
     MAX_DETOUR_MIN (score 0-50) — pas une simple distance géométrique à un
     itinéraire fixe : ça permet de détecter des correspondances entre des
     personnes allant vers des écoles différentes, tant que le détour réel
     pour passer les prendre reste raisonnable (ex. quelqu'un de Blagnac qui
     va à l'INSA en passant par le centre-ville peut tout à fait récupérer au
     passage quelqu'un du centre-ville qui va au CNAM).

Critères secondaires (classement) :
  - Temps de détour ajouté (tiebreaker principal, le plus petit d'abord)
  - Proximité des points de départ (bonus 0-10)
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
        extra_time_min: float,
    ):
        self.driver = driver
        self.passenger = passenger
        self.driver_ride = driver_ride
        self.passenger_ride = passenger_ride
        self.route_points = route_points
        self.extra_time_min = extra_time_min
        self.score = 0
        self.time_diff_min = 0
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

        # --- Critère primaire 2 : temps de détour réel pour récupérer le passager ---
        max_detour = config.MAX_DETOUR_MIN
        if self.extra_time_min <= max_detour:
            route_score = 50 * (1 - self.extra_time_min / max_detour)
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
            "distance_km": self.departure_distance_km,
            "extra_time_min": round(self.extra_time_min, 1),
            "score": self.score,
            "driver_coords": (self.driver_ride.start_lat, self.driver_ride.start_lon),
            "passenger_coords": (self.passenger_ride.start_lat, self.passenger_ride.start_lon),
            "campus_coords": (self.driver_ride.end_lat, self.driver_ride.end_lon),
            "route_geometry": [[lat, lon] for lat, lon in self.route_points],
            "route_distance_km": self.departure_distance_km,
        }


class MatchingService:
    """Service de matching conducteur/passager."""

    @staticmethod
    def _get_direct_route_cached(cache: Dict, driver_ride: Ride) -> Dict:
        """Itinéraire direct (sans détour) du conducteur, depuis le cache ou via ORS."""
        key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
        if key not in cache:
            details = routing_service.get_route_details(
                (driver_ride.start_lat, driver_ride.start_lon),
                (driver_ride.end_lat, driver_ride.end_lon),
            )
            cache[key] = details or {"geometry": [], "distance_m": 0.0, "duration_s": 0.0}
        return cache[key]

    @staticmethod
    def _get_detour_route_cached(cache: Dict, driver_ride: Ride, passenger_ride: Ride) -> Optional[Dict]:
        """Itinéraire du conducteur en passant récupérer le passager, depuis le
        cache ou via ORS (une entrée par couple trajet conducteur/point de
        récupération, arrondi pour regrouper les passagers au même endroit)."""
        driver_key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
        key = (driver_key, round(passenger_ride.start_lat, 4), round(passenger_ride.start_lon, 4))
        if key not in cache:
            cache[key] = routing_service.get_route_via_waypoint(
                (driver_ride.start_lat, driver_ride.start_lon),
                (passenger_ride.start_lat, passenger_ride.start_lon),
                (driver_ride.end_lat, driver_ride.end_lon),
            )
        return cache[key]

    @staticmethod
    def find_matches(current_user: User, my_rides: List[Ride], all_rides: List[Ride]) -> List[Dict]:
        """
        Trouve les trajets compatibles pour l'utilisateur courant.
        Critère principal : le temps de détour réel pour aller récupérer le
        passager (aller-via-passager vs aller direct) doit rester sous
        MAX_DETOUR_MIN — indépendant de la destination du passager, tant que
        le détour reste raisonnable.

        Le calcul du détour réel appelle le service de routing (ORS) — coûteux
        et limité en débit sur une clé gratuite. On fait donc d'abord une passe
        bon marché (aucun appel réseau) qui filtre par type/rôle et distance
        haversine des départs, puis on ne calcule le détour ORS que pour les
        MAX_DETOUR_CANDIDATES candidats les plus proches (par trajet
        conducteur) — borne le nombre d'appels ORS indépendamment de la taille
        de la base.
        """
        # --- Passe 1 : filtre bon marché, aucun appel réseau ---
        candidates_by_driver_ride: Dict[object, List[Tuple[float, User, User, Ride, Ride]]] = {}

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

                dep_dist = haversine_distance(
                    driver_ride.start_lat, driver_ride.start_lon,
                    passenger_ride.start_lat, passenger_ride.start_lon,
                )
                if dep_dist > config.MAX_DISTANCE_KM:
                    continue

                driver_key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
                candidates_by_driver_ride.setdefault(driver_key, []).append(
                    (dep_dist, driver, passenger, driver_ride, passenger_ride)
                )

        # --- Passe 2 : détour réel via ORS, uniquement pour le top-N par trajet conducteur ---
        matches: List[Match] = []
        direct_route_cache: Dict = {}
        detour_route_cache: Dict = {}

        for candidates in candidates_by_driver_ride.values():
            candidates.sort(key=lambda c: c[0])
            for dep_dist, driver, passenger, driver_ride, passenger_ride in candidates[: config.MAX_DETOUR_CANDIDATES]:
                direct = MatchingService._get_direct_route_cached(direct_route_cache, driver_ride)
                detour = MatchingService._get_detour_route_cached(
                    detour_route_cache, driver_ride, passenger_ride
                )
                if not detour:
                    continue

                extra_time_min = max(0.0, (detour["duration_s"] - direct["duration_s"]) / 60)

                match = Match(driver, passenger, driver_ride, passenger_ride, detour["geometry"], extra_time_min)
                if match.score >= config.MIN_MATCH_SCORE:
                    matches.append(match)

        # Tri principal par score, secondaire par temps de détour ajouté (asc)
        matches.sort(key=lambda m: (-m.score, m.extra_time_min))
        return [match.to_dict() for match in matches]


matching_service = MatchingService()
