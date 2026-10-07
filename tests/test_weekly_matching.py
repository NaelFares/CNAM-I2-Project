"""Recherche du planning limitée à une semaine de cours."""

from datetime import date, datetime, timedelta
import unittest
from unittest.mock import patch

from backend.api.routes import matches as matches_route
from backend.api.schemas import PlanningMatchRequest
from backend.models.event import Event
from backend.models.ride import Ride
from backend.models.user import User


class WeeklyMatchingTests(unittest.TestCase):
    def setUp(self):
        self.user = User(id=1, role="passenger", start_lat=43.6, start_lon=1.4,
                         school_lat=43.61, school_lon=1.41)

    def test_creates_only_missing_rides_without_deleting_existing_ones(self):
        monday = datetime(2030, 9, 23)
        event = Event(id=10, user_id=1, start_time=monday.replace(hour=8),
                      end_time=monday.replace(hour=12))
        outside = Event(id=11, user_id=1, start_time=monday + timedelta(days=7),
                        end_time=monday + timedelta(days=7, hours=4))
        rides = [Ride(id=20, user_id=1, event_id=10, ride_type="to_campus",
                      ride_time=event.start_time)]

        def create_ride(ride):
            rides.append(ride)
            return len(rides) + 20

        with patch.object(matches_route, "db") as database:
            database.get_events_by_user.return_value = [event, outside]
            database.get_rides_by_user.side_effect = lambda _user_id: list(rides)
            database.create_ride.side_effect = create_ride
            for _ in range(2):
                matches_route._ensure_week_rides(
                    self.user, monday, monday + timedelta(days=5), monday - timedelta(days=1)
                )

        self.assertEqual(len(rides), 2)
        self.assertEqual({ride.ride_type for ride in rides}, {"to_campus", "from_campus"})
        database.delete_active_rides_by_user.assert_not_called()

    def test_search_sends_only_selected_week_rides_to_matching(self):
        monday = datetime(2030, 9, 23)
        inside = Ride(id=1, user_id=1, ride_time=monday + timedelta(days=1, hours=8))
        weekend = Ride(id=2, user_id=1, ride_time=monday + timedelta(days=5, hours=8))
        before = Ride(id=3, user_id=1, ride_time=monday - timedelta(days=1))
        driver = Ride(id=4, user_id=2, ride_time=inside.ride_time)

        with (
            patch.object(matches_route, "db") as database,
            patch.object(matches_route, "matching_service") as matching,
        ):
            database.get_events_by_user.return_value = []
            database.get_active_rides_by_user.return_value = [inside, weekend, before]
            database.get_all_active_rides.return_value = [driver, weekend, before]
            database.get_ride_selection_counts.return_value = {}
            database.get_passenger_selected_ride_ids.return_value = set()
            database.get_passenger_reserved_times.return_value = set()
            matching.find_matches.return_value = []

            matches_route.find_matches(
                PlanningMatchRequest(week_start=date(2030, 9, 25)), self.user
            )

        kwargs = matching.find_matches.call_args.kwargs
        self.assertEqual(kwargs["my_rides"], [inside])
        self.assertEqual(kwargs["all_rides"], [driver])


if __name__ == "__main__":
    unittest.main()
