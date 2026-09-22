"""Tests for the inexpensive matching prefilters and candidate cap."""

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from backend.core.config import config
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import MatchingService


class MatchingOptimizationTests(unittest.TestCase):
    def setUp(self):
        self.when = datetime(2026, 9, 7, 8, 0)
        self.passenger = User(
            id=1,
            name="Passager",
            role="passenger",
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
            role="driver",
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
        )
        return user, ride

    def test_candidate_cap_applies_when_current_user_is_passenger(self):
        pairs = [self._driver_and_ride(index) for index in range(1, 6)]
        users = {user.id: user for user, _ in pairs}
        rides = [ride for _, ride in pairs]
        direct = {"geometry": [], "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=list(users.values())),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct) as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoint", return_value=detour) as via,
            patch.object(config, "MAX_DETOUR_CANDIDATES", 3),
        ):
            matches = MatchingService.find_matches(self.passenger, [self.passenger_ride], rides)

        self.assertEqual(len(matches), 3)
        self.assertEqual(details.call_count, 3)
        self.assertEqual(via.call_count, 3)

    def test_time_filter_runs_before_any_routing_call(self):
        driver, ride = self._driver_and_ride(1, minutes=60)

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoint") as via,
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
            patch("backend.services.matching.routing_service.get_route_via_waypoint") as via,
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
        direct = {"geometry": [], "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoint", return_value=detour),
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
            patch("backend.services.matching.routing_service.get_route_via_waypoint") as via,
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
            patch("backend.services.matching.routing_service.get_route_via_waypoint") as via,
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
        direct = {"geometry": [], "distance_m": 1000, "duration_s": 600}
        detour = {
            "geometry": [(43.60, 1.44), (43.61, 1.45)],
            "distance_m": 1200,
            "duration_s": 660,
        }

        with (
            patch("backend.services.matching.db.get_all_users", return_value=[driver]),
            patch("backend.services.matching.routing_service.get_route_details", return_value=direct),
            patch("backend.services.matching.routing_service.get_route_via_waypoint", return_value=detour),
        ):
            matches = MatchingService.find_matches(
                self.passenger,
                [self.passenger_ride, second_passenger_ride],
                [ride],
            )

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["ride_id"], ride.id)

    def test_driver_cannot_use_passenger_matching(self):
        driver, ride = self._driver_and_ride(1)

        with (
            patch("backend.services.matching.db.get_all_users") as users,
            patch("backend.services.matching.routing_service.get_route_details") as details,
            patch("backend.services.matching.routing_service.get_route_via_waypoint") as via,
        ):
            matches = MatchingService.find_matches(driver, [ride], [self.passenger_ride])

        self.assertEqual(matches, [])
        users.assert_not_called()
        details.assert_not_called()
        via.assert_not_called()


if __name__ == "__main__":
    unittest.main()
