"""
Moteur de recommandation de covoiturage basé sur l'itinéraire.

Un conducteur convient à un passager si sa route passe près du passager
(prise en charge puis dépose, dans cet ordre), si le vrai détour reste
raisonnable, et s'il passe au bon moment.

Critères éliminatoires :
  - Option "ladies only" de la recherche, si elle est activée : seules les
    autres utilisatrices sont retenues. C'est un filtre unilatéral posé par
    l'utilisatrice qui cherche — il restreint ses résultats à elle, sans
    changer sa propre visibilité dans les recherches des autres.
  - Prise en charge et dépose à moins de MAX_ROUTE_DISTANCE_KM de la route
    du conducteur, la dépose après la prise en charge. Les deux personnes
    n'ont pas besoin d'habiter ni d'étudier au même endroit.
  - Détour réel (calculé par OSRM) sous MAX_DETOUR_MIN.
  - Heure de passage du conducteur dans la tolérance horaire du passager :
    à l'aller il dépose le passager avant son heure d'arrivée, au retour il
    le prend après son heure de départ. Le conducteur garde son horaire.

Score (classement seulement, aucun minimum) : horaire (0-50), détour (0-50),
bonus de proximité à la route (0-10), plafonné à 100.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from backend.core.config import config
from backend.core.geo import haversine_distance
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.photo_storage import build_photo_url
from backend.services.reputation import compute_tier
from backend.services.route_estimate import estimate_route
from backend.services.route_fit import RouteFit, fit_on_route, nearest_on_route, route_points
from backend.services.routing import routing_service

# En dessous de cette distance, prise en charge ou depose sont considerees
# au meme endroit que le depart ou l'arrivee du conducteur (meme campus).
SAME_PLACE_KM = 0.3

# Marge (minutes) du pre-filtre horaire, ou l'heure de passage n'est encore
# qu'estimee a vol d'oiseau : la vraie verification se fait avec OSRM.
PREFILTER_TIME_SLACK_MIN = 15


def time_tolerance_min(passenger: User) -> int:
    """Ecart d'horaire accepte : celui du passager.

    Le conducteur garde son horaire (il arrive ou part a son heure) ; ce que
    le trajet lui coute est deja borne par le detour (MAX_DETOUR_MIN). L'heure
    a laquelle le passager est depose ou pris ne concerne que le passager.
    """
    return max(1, passenger.time_tolerance_min)


def overlaps_reserved_slot(reserved_times: set, ride_time: datetime) -> bool:
    """Le trajet tombe-t-il sur un creneau deja pris (autre reservation, ou
    trajet propose comme conducteur) ? Fenetre de SLOT_CONFLICT_MIN, pas la
    minute exacte : deux trajets a 8h00 et 8h15 se chevauchent."""
    window = config.SLOT_CONFLICT_MIN * 60
    return any(abs((ride_time - reserved).total_seconds()) < window for reserved in reserved_times)


def passage_gap_min(ride_type: str, passage: datetime, target: datetime) -> float:
    """Ecart, en minutes, entre le passage du conducteur et l'heure du
    passager. Negatif quand le passage tombe du mauvais cote.

    - Aller (to_campus) : l'heure du passager est son heure d'arrivee
      (debut du cours). Il doit etre depose avant, pas apres.
    - Retour (from_campus) : l'heure du passager est son heure de depart
      (fin du cours). Il ne peut etre pris qu'apres.
    """
    minutes = (passage - target).total_seconds() / 60
    return -minutes if ride_type == "to_campus" else minutes


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
        time_gap_min: float,
        route_fit: RouteFit,
        passage_time: datetime,
        occupied_seats: int = 0,
        driver_rating=None,
        driver_rides_count: int = 0,
        route_estimated: bool = False,
    ):
        self.driver = driver
        self.passenger = passenger
        self.driver_ride = driver_ride
        self.passenger_ride = passenger_ride
        self.route_points = route_points
        self.extra_time_min = extra_time_min
        # Ecart entre le passage du conducteur et l'heure du passager (>= 0).
        self.time_gap_min = time_gap_min
        self.route_fit = route_fit
        # Heure a laquelle le conducteur depose (aller) ou prend (retour) le passager.
        self.passage_time = passage_time
        # True si OSRM n'a pas repondu : trace et detour sont alors des
        # estimations (ligne droite), a signaler a l'utilisateur.
        self.route_estimated = route_estimated
        self.car_seats = int(driver.car_seats or 0)
        self.available_seats = max(0, self.car_seats - occupied_seats)
        # Reputation injectee par l'appelant : le moteur ne doit pas emettre
        # une requete par match.
        self.driver_rating = driver_rating
        self.driver_rides_count = driver_rides_count
        self.score = self._calculate_score()

    def _calculate_score(self) -> int:
        # Horaire (0-50). A l'aller, etre depose en avance dans la tolerance
        # n'est pas un defaut : note pleine. Au retour, l'ecart est une
        # attente apres le cours : 50 sans attente, 0 a la limite.
        tolerance = time_tolerance_min(self.passenger)
        if self.driver_ride.ride_type == "to_campus":
            time_score = 50.0
        else:
            time_score = 50 * max(0.0, 1 - self.time_gap_min / tolerance)

        # Detour reel (0-50) : 50 sans detour, 0 a MAX_DETOUR_MIN.
        route_score = 50 * max(0.0, 1 - self.extra_time_min / config.MAX_DETOUR_MIN)

        # Bonus de proximite a la route (0-10) : departage les candidats
        # dont la route passe au plus pres du passager.
        proximity_bonus = 10 * max(0.0, 1 - self.route_fit.max_km / config.MAX_ROUTE_DISTANCE_KM)

        # Le score expose comme un pourcentage ne doit jamais depasser 100.
        return min(100, int(time_score + route_score + proximity_bonus))

    def to_dict(self) -> Dict:
        return {
            "ride_id": self.driver_ride.id,
            "driver_name": self.driver.name,
            "driver_id": self.driver.id,
            "driver_ride_id": self.driver_ride.id,
            "driver_gender": self.driver.gender,
            "driver_photo_url": build_photo_url(self.driver.photo_filename),
            "driver_music_preference": self.driver.music_preference,
            "driver_music_genres": list(self.driver.music_genres),
            "driver_rating_average": self.driver_rating.average if self.driver_rating else None,
            "driver_rating_count": self.driver_rating.count if self.driver_rating else 0,
            "driver_tier_key": compute_tier(self.driver_rides_count).key,
            "driver_tier_label": compute_tier(self.driver_rides_count).label,
            "driver_rides_count": self.driver_rides_count,
            "driver_smoking_preference": self.driver.smoking_preference,
            "passenger_name": self.passenger.name,
            "passenger_id": self.passenger.id,
            "passenger_gender": self.passenger.gender,
            "passenger_photo_url": build_photo_url(self.passenger.photo_filename),
            "ride_time": self.driver_ride.format_time(),
            "ride_type": self.driver_ride.get_direction_label(),
            "time_diff_min": round(self.time_gap_min),
            # Heure de depose (aller) ou de prise en charge (retour).
            "passage_time": self.passage_time.strftime("%H:%M"),
            # Plus grand ecart entre la route du conducteur et le passager.
            "distance_km": self.route_fit.max_km,
            "extra_time_min": round(self.extra_time_min, 1),
            "score": self.score,
            "driver_coords": (self.driver_ride.start_lat, self.driver_ride.start_lon),
            "passenger_coords": (self.passenger_ride.start_lat, self.passenger_ride.start_lon),
            "campus_coords": (self.driver_ride.end_lat, self.driver_ride.end_lon),
            # Ou le passager descend : sa propre destination, qui peut differer
            # de celle du conducteur (autre ecole sur sa route, domicile).
            "passenger_dropoff_coords": (self.passenger_ride.end_lat, self.passenger_ride.end_lon),
            "route_geometry": [[lat, lon] for lat, lon in self.route_points],
            "route_distance_km": self.route_fit.max_km,
            "route_estimated": self.route_estimated,
            "car_seats": self.car_seats,
            "available_seats": self.available_seats,
        }


class MatchingService:
    """Service de matching conducteur/passager."""

    @staticmethod
    def _get_direct_route_cached(cache: Dict, driver_ride: Ride) -> Dict:
        """Itinéraire direct (sans détour) du conducteur, depuis le cache ou via OSRM."""
        key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
        if key not in cache:
            details = routing_service.get_route_details(
                (driver_ride.start_lat, driver_ride.start_lon),
                (driver_ride.end_lat, driver_ride.end_lon),
            )
            cache[key] = details or {"geometry": [], "distance_m": 0.0, "duration_s": 0.0}
        return cache[key]

    @staticmethod
    def _pickup_and_dropoff(driver_ride: Ride, passenger_ride: Ride) -> Tuple[Optional[Tuple], Optional[Tuple]]:
        """Points de prise en charge et de depose du passager. None quand le
        point se confond avec le depart ou l'arrivee du conducteur (meme
        campus) : il n'ajoute aucun detour ni aucune etape."""
        pickup = (passenger_ride.start_lat, passenger_ride.start_lon)
        dropoff = (passenger_ride.end_lat, passenger_ride.end_lon)
        if haversine_distance(*pickup, driver_ride.start_lat, driver_ride.start_lon) <= SAME_PLACE_KM:
            pickup = None
        if haversine_distance(*dropoff, driver_ride.end_lat, driver_ride.end_lon) <= SAME_PLACE_KM:
            dropoff = None
        return pickup, dropoff

    @staticmethod
    def _passenger_waypoints(driver_ride: Ride, passenger_ride: Ride) -> List[Tuple[float, float]]:
        """Etapes du conducteur pour le passager, dans l'ordre : prise en
        charge, puis depose (sans celles confondues avec son depart ou son
        arrivee)."""
        return [point for point in MatchingService._pickup_and_dropoff(driver_ride, passenger_ride) if point]

    @staticmethod
    def _get_detour_route_cached(cache: Dict, driver_ride: Ride, passenger_ride: Ride) -> Optional[Dict]:
        """Itinéraire du conducteur en passant prendre puis déposer le
        passager, depuis le cache ou via OSRM (une entrée par trajet
        conducteur et couple de points, arrondis pour regrouper les passagers
        qui partent et vont au même endroit)."""
        driver_key = driver_ride.id or (driver_ride.user_id, str(driver_ride.ride_time))
        waypoints = MatchingService._passenger_waypoints(driver_ride, passenger_ride)
        key = (driver_key, tuple((round(lat, 4), round(lon, 4)) for lat, lon in waypoints))
        if key not in cache:
            cache[key] = routing_service.get_route_via_waypoints(
                (driver_ride.start_lat, driver_ride.start_lon),
                waypoints,
                (driver_ride.end_lat, driver_ride.end_lon),
            )
        return cache[key]

    @staticmethod
    def _straight_line_detour_km(driver_ride: Ride, passenger_ride: Ride) -> float:
        """Detour estime a vol d'oiseau (prise en charge puis depose), sans
        appel reseau. Sert au jeu de donnees de demonstration."""
        stops = [
            (driver_ride.start_lat, driver_ride.start_lon),
            *MatchingService._passenger_waypoints(driver_ride, passenger_ride),
            (driver_ride.end_lat, driver_ride.end_lon),
        ]
        via_km = sum(haversine_distance(*a, *b) for a, b in zip(stops, stops[1:]))
        return via_km - haversine_distance(*stops[0], *stops[-1])

    @staticmethod
    def _leg_to_passenger(driver_ride: Ride, passenger_ride: Ride) -> Optional[Tuple[Tuple, Tuple]]:
        """Portion de route qui fixe l'heure de passage : a l'aller, de la
        depose a l'arrivee du conducteur ; au retour, du depart du conducteur
        a la prise en charge. None si le point est confondu (passage a
        l'heure du conducteur)."""
        pickup, dropoff = MatchingService._pickup_and_dropoff(driver_ride, passenger_ride)
        if driver_ride.ride_type == "to_campus":
            return (dropoff, (driver_ride.end_lat, driver_ride.end_lon)) if dropoff else None
        return ((driver_ride.start_lat, driver_ride.start_lon), pickup) if pickup else None

    @staticmethod
    def _passage_time(driver_ride: Ride, leg_duration_s: float) -> datetime:
        """Heure ou le conducteur depose (aller) ou prend (retour) le passager.

        A l'aller, l'heure du conducteur est son heure d'arrivee : il passe
        chez le passager avant, d'autant que la fin de son trajet est longue.
        Au retour, c'est son heure de depart : il passe apres.
        """
        offset = timedelta(seconds=leg_duration_s)
        if driver_ride.ride_type == "to_campus":
            return driver_ride.ride_time - offset
        return driver_ride.ride_time + offset

    @staticmethod
    def _total_detour_min(direct: Dict, driver_ride: Ride, stops: List[Tuple]) -> float:
        """Detour total du conducteur avec tous ses passagers.

        `stops` : couples (prise en charge, depose) en (lat, lon). Les points
        confondus avec son depart ou son arrivee sont ignores ; les autres
        sont visites dans l'ordre ou ils se trouvent le long de sa route.
        """
        start = (driver_ride.start_lat, driver_ride.start_lon)
        end = (driver_ride.end_lat, driver_ride.end_lon)
        points = [
            point
            for pickup, dropoff in stops
            for point, ref in ((pickup, start), (dropoff, end))
            if point and haversine_distance(*point, *ref) > SAME_PLACE_KM
        ]
        route = route_points(direct["geometry"])
        points.sort(key=lambda point: nearest_on_route(point, route)[1])
        total = routing_service.get_route_via_waypoints(start, points, end)
        return max(0.0, (total["duration_s"] - direct["duration_s"]) / 60)

    @staticmethod
    def accept_exceeds_total_detour(driver_ride: Ride, new_stop: Tuple, accepted: List[Tuple]) -> bool:
        """Accepter ce passager ferait-il depasser MAX_TOTAL_DETOUR_MIN ?

        Verifie au moment ou le conducteur accepte : plusieurs demandes en
        attente ont pu etre calculees chacune seule, le total n'est connu qu'a
        l'acceptation. Sans autre passager accepte, rien a additionner.
        """
        if not accepted:
            return False
        direct = routing_service.get_route_details(
            (driver_ride.start_lat, driver_ride.start_lon),
            (driver_ride.end_lat, driver_ride.end_lon),
        )
        total = MatchingService._total_detour_min(direct, driver_ride, accepted + [new_stop])
        return total > config.MAX_TOTAL_DETOUR_MIN

    @staticmethod
    def _estimated_gap_min(driver_ride: Ride, passenger_ride: Ride) -> float:
        """Ecart horaire (voir passage_gap_min) avec une heure de passage
        estimee a vol d'oiseau, sans appel reseau."""
        leg = MatchingService._leg_to_passenger(driver_ride, passenger_ride)
        leg_s = estimate_route(list(leg))["duration_s"] if leg else 0.0
        passage = MatchingService._passage_time(driver_ride, leg_s)
        return passage_gap_min(driver_ride.ride_type, passage, passenger_ride.ride_time)

    @staticmethod
    def _time_may_fit(driver: User, passenger: User, driver_ride: Ride, passenger_ride: Ride) -> bool:
        """Pre-filtre horaire : heure de passage estimee, avec une marge.
        La verification exacte, avec la vraie route, vient apres."""
        gap = MatchingService._estimated_gap_min(driver_ride, passenger_ride)
        tolerance = time_tolerance_min(passenger)
        return -PREFILTER_TIME_SLACK_MIN <= gap <= tolerance + PREFILTER_TIME_SLACK_MIN

    @staticmethod
    def find_matches(
        current_user: User,
        my_rides: List[Ride],
        all_rides: List[Ride],
        selection_counts: Optional[Dict[int, int]] = None,
        selected_ride_ids: Optional[set[int]] = None,
        reserved_times: Optional[set] = None,
        ladies_only: bool = False,
        rating_summaries: Optional[Dict[int, object]] = None,
        driver_ride_counts: Optional[Dict[int, int]] = None,
        accepted_stops: Optional[Dict[int, List[Tuple]]] = None,
    ) -> List[Dict]:
        """
        Trouve les trajets compatibles pour l'utilisateur courant.

        `ladies_only` restreint les résultats aux autres utilisatrices. C'est
        une option ponctuelle de la recherche (pas un réglage de profil), et
        un filtre unilatéral : il ne retire pas `current_user` des résultats
        renvoyés aux autres. Son autorisation est vérifiée côté route.

        Trois passes, de la moins chère à la plus chère :
        1. Filtres en mémoire (rôle, places, sens, doublons, horaire estimé).
        2. Le passager est-il sur la route du conducteur ? Prise en charge et
           dépose à moins de MAX_ROUTE_DISTANCE_KM de son itinéraire direct,
           dans le bon ordre. Les MAX_DETOUR_CANDIDATES plus proches de la
           route sont retenus par trajet du passager.
        3. Détour réel (prise en charge puis dépose) et heure de passage
           exacte, calculés par OSRM. Le détour doit rester sous
           MAX_DETOUR_MIN et le passage dans la tolérance horaire. Si la
           voiture a déjà des passagers acceptés (`accepted_stops`), le détour
           total de tous les arrêts doit aussi rester sous MAX_TOTAL_DETOUR_MIN.
        """
        # Seules mes recherches cherchent : un trajet que je propose n'a pas a
        # trouver de conducteur.
        my_rides = [ride for ride in my_rides if not ride.is_offer]

        selection_counts = selection_counts or {}
        selected_ride_ids = selected_ride_ids or set()
        reserved_times = reserved_times or set()
        accepted_stops = accepted_stops or {}

        # --- Passe 1 : filtres en memoire, aucun appel reseau ---
        candidates_by_my_ride: Dict[object, List[Tuple[User, User, Ride, Ride]]] = {}
        users_by_id = {user.id: user for user in db.get_all_users()}
        users_by_id[current_user.id] = current_user

        for my_ride in my_rides:
            for other_ride in all_rides:
                if other_ride.user_id == current_user.id:
                    continue
                if other_ride.id in selected_ride_ids:
                    continue
                if my_ride.ride_type != other_ride.ride_type:
                    continue
                if not my_ride.ride_time or not other_ride.ride_time:
                    continue
                if overlaps_reserved_slot(reserved_times, other_ride.ride_time):
                    continue

                # Seuls les trajets proposes sont des candidats : c'est le trajet
                # qui dit "je prends ma voiture", plus le role de son auteur.
                if not other_ride.is_offer:
                    continue
                other_user = users_by_id.get(other_ride.user_id)
                if not other_user or not other_user.can_drive():
                    continue

                # "Ladies only" : filtre applique avant tout calcul, pour ne
                # gaspiller aucun appel de routing sur une paire ecartee.
                if ladies_only and not other_user.is_woman():
                    continue

                driver, passenger = other_user, current_user
                driver_ride, passenger_ride = other_ride, my_ride
                capacity = int(driver.car_seats or 0)
                occupied = selection_counts.get(driver_ride.id, 0)
                if capacity < 1 or occupied >= capacity:
                    continue

                if not MatchingService._time_may_fit(driver, passenger, driver_ride, passenger_ride):
                    continue

                my_ride_key = my_ride.id or (
                    my_ride.user_id,
                    my_ride.ride_type,
                    str(my_ride.ride_time),
                    round(my_ride.start_lat, 5),
                    round(my_ride.start_lon, 5),
                )
                candidates_by_my_ride.setdefault(my_ride_key, []).append(
                    (driver, passenger, driver_ride, passenger_ride)
                )

        # --- Passe 2 : le passager est-il sur la route du conducteur ? ---
        direct_route_cache: Dict = {}
        shortlist: List[Tuple[RouteFit, User, User, Ride, Ride]] = []
        for candidates in candidates_by_my_ride.values():
            fitting = []
            for driver, passenger, driver_ride, passenger_ride in candidates:
                direct = MatchingService._get_direct_route_cached(direct_route_cache, driver_ride)
                pickup, dropoff = MatchingService._pickup_and_dropoff(driver_ride, passenger_ride)
                fit = fit_on_route(
                    route_points(direct["geometry"]), pickup, dropoff, config.MAX_ROUTE_DISTANCE_KM
                )
                if fit:
                    fitting.append((fit, driver, passenger, driver_ride, passenger_ride))
            fitting.sort(key=lambda item: item[0].pickup_km + item[0].dropoff_km)
            shortlist.extend(fitting[: config.MAX_DETOUR_CANDIDATES])

        # --- Passe 3 : detour reel et heure de passage exacte ---
        matches: List[Match] = []
        detour_route_cache: Dict = {}
        for fit, driver, passenger, driver_ride, passenger_ride in shortlist:
            direct = MatchingService._get_direct_route_cached(direct_route_cache, driver_ride)
            detour = MatchingService._get_detour_route_cached(detour_route_cache, driver_ride, passenger_ride)
            if not detour:
                continue

            extra_time_min = max(0.0, (detour["duration_s"] - direct["duration_s"]) / 60)
            # Seuil eliminatoire : un detour trop long n'est jamais propose,
            # meme si l'horaire et la proximite sont parfaits.
            if extra_time_min > config.MAX_DETOUR_MIN:
                continue

            leg = MatchingService._leg_to_passenger(driver_ride, passenger_ride)
            leg_route = routing_service.get_route_details(*leg) if leg else None
            passage = MatchingService._passage_time(driver_ride, leg_route["duration_s"] if leg_route else 0.0)
            gap = passage_gap_min(driver_ride.ride_type, passage, passenger_ride.ride_time)
            if not 0 <= gap <= time_tolerance_min(passenger):
                continue

            # Voiture deja partagee : les detours s'additionnent.
            if driver_ride.id in accepted_stops:
                stops = accepted_stops[driver_ride.id] + [
                    MatchingService._pickup_and_dropoff(driver_ride, passenger_ride)
                ]
                if MatchingService._total_detour_min(direct, driver_ride, stops) > config.MAX_TOTAL_DETOUR_MIN:
                    continue

            occupied = selection_counts.get(driver_ride.id, 0)
            match = Match(
                driver,
                passenger,
                driver_ride,
                passenger_ride,
                detour["geometry"],
                extra_time_min,
                time_gap_min=gap,
                route_fit=fit,
                passage_time=passage,
                occupied_seats=occupied,
                driver_rating=(rating_summaries or {}).get(driver.id),
                driver_rides_count=(driver_ride_counts or {}).get(driver.id, 0),
                # Le detour est une difference entre deux itineraires :
                # il suffit que l'un des deux soit estime pour qu'il le soit.
                route_estimated=bool(detour.get("estimated") or direct.get("estimated")),
            )
            # Pas de score minimum : les regles ci-dessus eliminent, le score
            # ne sert qu'a classer. Un seuil filtrait une seconde fois sur les
            # memes criteres (une depose 8 min avant le cours etait ecartee).
            matches.append(match)

        # Tri principal par score, secondaire par temps de détour ajouté (asc).
        # Un meme trajet conducteur peut correspondre a plusieurs entrees du
        # planning passager : on ne conserve que sa meilleure correspondance.
        matches.sort(key=lambda m: (-m.score, m.extra_time_min))
        unique_matches: List[Match] = []
        seen_ride_ids: set[int] = set()
        for match in matches:
            ride_id = match.driver_ride.id
            if ride_id in seen_ride_ids:
                continue
            seen_ride_ids.add(ride_id)
            unique_matches.append(match)

        return [match.to_dict() for match in unique_matches]


matching_service = MatchingService()
