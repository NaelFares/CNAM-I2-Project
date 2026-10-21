"""Tests for the inexpensive matching prefilters and candidate cap."""

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from backend.core.config import config
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import MatchingService

# Itineraire direct simule des conducteurs : il passe par le depart et
# l'arrivee du passager, qui est donc toujours "sur la route".
PASSENGER_ROUTE = [(43.6000, 1.4400), (43.6100, 1.4500)]


class MatchingOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(2026, 9, 7, 8, 0)
        self.passenger = User(
            id=1,
            name="Passager",
            time_tolerance_min=15,
        )
        self.passenger_ride = Ride(
            id=1,
            user_id=1,
            event_id=1,
            ride_type="to_campus",
            ride_time=self.when,
            start_lat=43.6000,
            start_lon=1.4400,
            end_lat=43.6100,
            end_lon=1.4500,
        )

    def _driver_and_ride(self, index: int, minutes: int = 0):
        user = User(
            id=10 + index,
            name=f"Conducteur {index}",
            car_seats=4,
            time_tolerance_min=15,
        )
        ride = Ride(
            id=10 + index,
            user_id=user.id,
            event_id=10 + index,
            ride_type="to_campus",
            ride_time=self.when + timedelta(minutes=minutes),
            start_lat=43.6000 + index * 0.001,
            start_lon=1.4400,
            end_lat=43.6100,
            end_lon=1.4500,
            # C'est le trajet qui porte l'offre, plus le role de son auteur.
            is_offer=True,
        )
        return user, ride

    def test_candidate_cap_applies_when_current_user_is_passenger(self):
        pairs = [self._driver_and_ride(index) for index in range(1, 6)]
        users = {user.id: user for user, _ in pairs}
        rides = [ride for _, ride in pairs]
        direct = {"geometry": PASSENGER_ROUTE, "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=list(users.values())),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct) as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints", return_value=detour) as via,
            patch.object(config, "MAX_DETOUR_CANDIDATES", 3),
        ):
            matches = MatchingService.find_matches(self.passenger, [self.passenger_ride], rides)

        self.assertEqual(len(matches), 3)
        # L'itineraire direct sert a verifier que le passager est sur la
        # route : il est calcule pour chaque candidat. La limite porte sur
        # le calcul du detour, le plus couteux.
        self.assertEqual(details.call_count, 5)
        self.assertEqual(via.call_count, 3)

    def test_detour_above_the_limit_is_never_proposed(self):
        """Meme horaire et depart voisin (60 points) : le detour trop long
        reste eliminatoire, il ne suffit pas qu'il rapporte 0 point."""
        driver, ride = self._driver_and_ride(1)
        direct = {"geometry": PASSENGER_ROUTE, "distance_m": 1000, "duration_s": 600}
        too_long = {"geometry": [], "distance_m": 9000, "duration_s": 600 + 38 * 60}

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoints", return_value=too_long),
        ):
            matches = MatchingService.find_matches(self.passenger, [self.passenger_ride], [ride])

        self.assertEqual(matches, [])

    def test_time_filter_runs_before_any_routing_call(self):
        driver, ride = self._driver_and_ride(1, minutes=60)

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride],
                [ride],
            )

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_full_driver_ride_is_filtered_before_any_routing_call(self):
        driver, ride = self._driver_and_ride(1)
        driver.car_seats = 1

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride],
                [ride],
                selection_counts={ride.id: 1},
            )

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_match_exposes_driver_ride_and_remaining_capacity(self):
        driver, ride = self._driver_and_ride(1)
        direct = {"geometry": PASSENGER_ROUTE, "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoints", return_value=detour),
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride],
                [ride],
                selection_counts={ride.id: 2},
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["ride_id"], ride.id)
        self.assertEqual(matches[0]["car_seats"], 4)
        self.assertEqual(matches[0]["available_seats"], 2)

    def test_already_selected_ride_is_filtered_before_routing(self):
        driver, ride = self._driver_and_ride(1)

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride],
                [ride],
                selected_ride_ids={ride.id},
            )

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_reserved_minute_is_filtered_before_routing(self):
        driver, ride = self._driver_and_ride(1)

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride],
                [ride],
                reserved_times={ride.ride_time},
            )

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_same_driver_ride_is_returned_only_once(self):
        driver, ride = self._driver_and_ride(1)
        second_passenger_ride = Ride(
            id=2,
            user_id=self.passenger.id,
            event_id=2,
            ride_type="to_campus",
            ride_time=self.when,
            start_lat=self.passenger_ride.start_lat,
            start_lon=self.passenger_ride.start_lon,
            end_lat=self.passenger_ride.end_lat,
            end_lon=self.passenger_ride.end_lon,
        )
        direct = {"geometry": PASSENGER_ROUTE, "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoints", return_value=detour),
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride, second_passenger_ride],
                [ride],
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["ride_id"], ride.id)

    def test_own_offer_does_not_search(self):
        """Un trajet que je propose n'a pas a trouver de conducteur.

        Remplace l'ancienne regle "un conducteur ne cherche pas" : il n'y a
        plus de role, c'est le trajet lui-meme qui cherche ou propose.
        """
        driver, ride = self._driver_and_ride(1)

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(driver, [ride], [self.passenger_ride])

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_search_ride_of_someone_else_is_not_a_candidate(self):
        """Le trajet d'un autre qui cherche aussi une voiture n'est pas une offre."""
        driver, ride = self._driver_and_ride(1)
        ride.is_offer = False

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoints") as via,
        ):
            matches = MatchingService.find_matches(self.passenger, [self.passenger_ride], [ride])

        self.assertEqual(matches, [])
        details.assert_not_called()
        via.assert_not_called()

    def test_everyone_can_search_even_with_a_car(self):
        """Avoir une voiture n'empeche pas de chercher sur un autre trajet."""
        driver, ride = self._driver_and_ride(1)
        self.passenger.car_seats = 3
        direct = {"geometry": PASSENGER_ROUTE, "distance_m": 1000, "duration_s": 600}
        detour = {"geometry": [(43.60, 1.44)], "distance_m": 1200, "duration_s": 660}

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoints", return_value=detour),
        ):
            matches = MatchingService.find_matches(self.passenger, [self.passenger_ride], [ride])

        self.assertEqual(len(matches), 1)


INSA, IUT, CAPITOLE = (43.5722, 1.4689), (43.6495, 1.3749), (43.6061, 1.4382)


def _ride(start, end, ride_type="to_campus"):
    return Ride(ride_type=ride_type, ride_time=datetime(2026, 10, 26, 8),
                start_lat=start[0], start_lon=start[1], end_lat=end[0], end_lon=end[1])


class DetourWaypointsTests(unittest.TestCase):
    """Le detour compte la prise en charge ET la depose du passager."""

    def test_same_school_on_the_way_in_only_adds_the_pickup(self):
        driver = _ride((43.5871, 1.4614), INSA)
        passenger = _ride((43.5497, 1.4710), INSA)
        self.assertEqual(MatchingService._passenger_waypoints(driver, passenger), [(43.5497, 1.4710)])

    def test_other_school_on_the_way_adds_pickup_then_dropoff(self):
        # Le conducteur va a l'IUT Blagnac ; la passagere descend au Capitole.
        driver = _ride((43.5871, 1.4614), IUT)
        passenger = _ride((43.6000, 1.4500), CAPITOLE)
        self.assertEqual(
            MatchingService._passenger_waypoints(driver, passenger),
            [(43.6000, 1.4500), CAPITOLE],
        )

    def test_way_back_from_the_same_campus_counts_the_dropoff_at_home(self):
        # Avant : depart commun au campus, donc detour toujours nul au retour.
        driver = _ride(INSA, (43.5871, 1.4614), "from_campus")
        passenger = _ride(INSA, (43.5497, 1.4710), "from_campus")
        self.assertEqual(MatchingService._passenger_waypoints(driver, passenger), [(43.5497, 1.4710)])

    def test_candidates_are_ranked_by_estimated_detour_not_departure_distance(self):
        passenger = _ride((43.6000, 1.4500), CAPITOLE)
        # Tout proche au depart mais part a l'oppose (vers l'INSA, au sud).
        opposite = _ride((43.6010, 1.4510), INSA)
        # Un peu plus loin, mais sa route vers l'IUT passe par le Capitole.
        on_the_way = _ride((43.5950, 1.4600), IUT)
        self.assertLess(
            MatchingService._straight_line_detour_km(on_the_way, passenger),
            MatchingService._straight_line_detour_km(opposite, passenger),
        )


if __name__ == "__main__":
    unittest.main()
