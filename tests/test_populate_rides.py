"""Les trajets de démonstration restent présents sans recréer les réservations."""

from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from backend.database import populate
from backend.models.ride import Ride
from backend.models.user import User


class PopulateRidesTests(unittest.TestCase):
    def test_creates_missing_future_rides_without_duplicating_existing_ones(self):
        user = User(
            id=7,
            role="driver",
            car_seats=4,
            start_lat=43.6,
            start_lon=1.4,
            school_lat=43.61,
            school_lon=1.41,
        )
        events = []
        rides = []

        def create_event(event):
            event.id = len(events) + 1
            events.append(event)
            return event.id

        def create_ride(ride):
            ride.id = len(rides) + 1
            rides.append(ride)
            return ride.id

        with patch.object(populate, "db") as database:
            database.get_events_by_user.side_effect = lambda _user_id: list(events)
            database.get_rides_by_user.side_effect = lambda _user_id: list(rides)
            database.create_event.side_effect = create_event
            database.create_ride.side_effect = create_ride

            first_count = populate._ensure_seed_rides(user, "CNAM", now=datetime(2026, 9, 23))
            second_count = populate._ensure_seed_rides(user, "CNAM", now=datetime(2026, 9, 23))

            self.assertEqual(first_count, 4)
            self.assertEqual(second_count, 0)
            self.assertEqual(len(events), 2)
            self.assertEqual(len(rides), 4)
            self.assertEqual({ride.ride_type for ride in rides}, {"to_campus", "from_campus"})
            self.assertEqual({ride.ride_time.date().isoformat() for ride in rides}, {"2026-09-28", "2026-09-30"})

            rides.pop()
            replacement_count = populate._ensure_seed_rides(user, "CNAM", now=datetime(2026, 9, 23))
            self.assertEqual(replacement_count, 1)
            self.assertEqual(len(events), 2)
            self.assertEqual(len(rides), 4)

            next_week_count = populate._ensure_seed_rides(user, "CNAM", now=datetime(2026, 10, 1))
            self.assertEqual(next_week_count, 4)
            self.assertEqual(len(events), 4)
            self.assertEqual(len(rides), 8)
            self.assertEqual(
                {ride.ride_time.date().isoformat() for ride in rides},
                {"2026-09-28", "2026-09-30", "2026-10-05", "2026-10-07"},
            )

    def test_seeds_passenger_selection_once_and_leaves_a_free_seat(self):
        ride_time = datetime.now() + timedelta(days=2)
        passenger = User(id=1, role="passenger", start_lat=43.60, start_lon=1.40,
                         school_lat=43.61, school_lon=1.41)
        other_passenger = User(id=3, role="passenger", start_lat=43.60, start_lon=1.40,
                               school_lat=43.61, school_lon=1.41)
        driver = User(id=7, role="driver", car_seats=3, start_lat=43.60, start_lon=1.40,
                      school_lat=43.61, school_lon=1.41)
        users = {1: passenger, 3: other_passenger, 7: driver}
        rides = {
            1: [Ride(id=11, user_id=1, ride_time=ride_time)],
            3: [Ride(id=13, user_id=3, ride_time=ride_time)],
            7: [Ride(id=17, user_id=7, ride_time=ride_time)],
        }
        selections = set()
        accepted = set()

        def select_ride(ride_id, passenger_id):
            selections.add((ride_id, passenger_id))
            return {"status": "selected"}

        def decide_ride_selection(ride_id, passenger_id, driver_id, decision):
            accepted.add((ride_id, passenger_id))
            return {"status": "accepted"}

        with patch.object(populate, "db") as database:
            database.get_user_by_email.side_effect = lambda email: users.get(int(email[8:10]))
            database.get_rides_by_user.side_effect = lambda user_id: rides[user_id]
            database.get_ride_request_counts.side_effect = lambda: {17: len(selections)}
            database.get_ride_selection_counts.side_effect = lambda: {17: len(accepted)}
            database.get_passenger_reserved_times.side_effect = lambda user_id: {
                ride_time for _, selected_user_id in selections if selected_user_id == user_id
            }
            database.select_ride.side_effect = select_ride
            database.decide_ride_selection.side_effect = decide_ride_selection

            self.assertEqual(populate._ensure_seed_selections(), 2)
            self.assertEqual(populate._ensure_seed_selections(), 0)

        self.assertEqual(selections, {(17, 1), (17, 3)})
        self.assertEqual(accepted, {(17, 1)})


if __name__ == "__main__":
    unittest.main()
