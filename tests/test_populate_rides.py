"""Jeu de donnees de demonstration : une semaine coherente, sans doublons."""

from collections import Counter
from datetime import datetime, timedelta
import unittest
from unittest.mock import patch

from backend.database import populate
from backend.models.ride import Ride
from backend.models.user import User


class SeedProfilesTests(unittest.TestCase):
    def test_profiles_are_complete_and_inside_the_osrm_map(self):
        self.assertEqual(len(populate.SEED_PROFILES), populate.SEED_COUNT)
        for profile in populate.SEED_PROFILES:
            self.assertIn(profile.school, populate.SCHOOLS)
            self.assertIn(profile.gender, ("femme", "homme", "autre"))
            # Zone de la carte OSRM (docker-compose.osrm.yml, OSRM_BBOX).
            self.assertTrue(43.40 <= profile.lat <= 43.82 and 1.10 <= profile.lon <= 1.70, profile)

    def test_names_are_unique(self):
        names = Counter(f"{p.first_name} {p.last_name}" for p in populate.SEED_PROFILES)
        self.assertEqual(max(names.values()), 1)

    def test_every_school_has_drivers_and_passengers(self):
        for school in populate.SCHOOLS:
            profiles = [p for p in populate.SEED_PROFILES if p.school == school]
            self.assertTrue(any(p.car_seats for p in profiles), school)
            self.assertTrue(any(not p.car_seats for p in profiles), school)

    def test_free_test_account_is_a_passenger_who_can_use_ladies_only(self):
        profile = populate.SEED_PROFILES[populate.FREE_TEST_ACCOUNT - 1]
        self.assertIsNone(profile.car_seats)
        self.assertEqual(profile.gender, "femme")
        school_drivers = [p for p in populate.SEED_PROFILES if p.school == profile.school and p.car_seats]
        self.assertTrue(any(p.gender == "femme" for p in school_drivers))


class DemoWeekTests(unittest.TestCase):
    def test_demo_week_is_always_the_next_monday(self):
        # Mercredi, samedi et lundi : la semaine de demo est toujours a venir.
        self.assertEqual(populate.demo_week_monday(datetime(2026, 10, 21, 15)), datetime(2026, 10, 26))
        self.assertEqual(populate.demo_week_monday(datetime(2026, 10, 24, 9)), datetime(2026, 10, 26))
        self.assertEqual(populate.demo_week_monday(datetime(2026, 10, 26, 7)), datetime(2026, 11, 2))


class EnsureSeedRidesTests(unittest.TestCase):
    def _run(self, index, now):
        user = User(id=index, car_seats=populate.SEED_PROFILES[index - 1].car_seats,
                    start_lat=43.6, start_lon=1.4, start_address="1 Rue de test")
        events, rides = [], []

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
            first = populate._ensure_seed_rides(user, index, now)
            second = populate._ensure_seed_rides(user, index, now)
        return first, second, events, rides

    def test_creates_one_round_trip_per_course_of_the_school_timetable(self):
        # Compte 02 : conducteur a l'INSA, cours les cinq jours.
        first, second, events, rides = self._run(2, datetime(2026, 10, 21, 15))

        self.assertEqual(first, 10)
        self.assertEqual(second, 0)
        self.assertEqual(len(events), 5)
        self.assertTrue(all(ride.is_offer for ride in rides))
        self.assertEqual({ride.ride_time.date() for ride in rides},
                         {datetime(2026, 10, day).date() for day in range(26, 31)})
        tuesday = [ride for ride in rides if ride.ride_time.weekday() == 1]
        self.assertEqual(sorted(ride.ride_time.strftime("%H:%M") for ride in tuesday), ["08:00", "17:00"])
        # Les trajets portent des adresses lisibles dans l'interface.
        to_campus = next(ride for ride in rides if ride.ride_type == "to_campus")
        self.assertEqual((to_campus.start_address, to_campus.end_address), ("1 Rue de test", "INSA Toulouse"))

    def test_late_group_starts_a_quarter_of_an_hour_later(self):
        # Compte 08 : groupe decale (un compte sur cinq), Capitole le lundi a 10h.
        _, _, _, rides = self._run(8, datetime(2026, 10, 21, 15))
        monday = next(ride for ride in rides if ride.ride_time.weekday() == 0 and ride.ride_type == "to_campus")
        self.assertEqual(monday.ride_time, datetime(2026, 10, 26, 10, 15))
        self.assertFalse(monday.is_offer)


class EnsureSeedSelectionsTests(unittest.TestCase):
    def test_books_drivers_on_the_way_once_and_leaves_a_free_seat(self):
        # Un lundi de la semaine de demo : la premiere demande y est acceptee.
        ride_time = populate.demo_week_monday(datetime.now()) + timedelta(hours=8)
        # Comptes 04 (conducteur N7, 4 places), 18 et 35 (passagers N7, pas
        # dans FREE_TEST_ACCOUNTS).
        users = {
            4: User(id=4, car_seats=4, time_tolerance_min=15),
            18: User(id=18, time_tolerance_min=15),
            35: User(id=35, time_tolerance_min=15),
        }
        rides = {
            4: [Ride(id=40, user_id=4, ride_time=ride_time, is_offer=True)],
            18: [Ride(id=180, user_id=18, ride_time=ride_time)],
            35: [Ride(id=350, user_id=35, ride_time=ride_time + timedelta(minutes=15))],
        }
        selections, accepted, stops = set(), set(), []

        def select_ride(ride_id, passenger_id, stop=None):
            selections.add((ride_id, passenger_id))
            stops.append(stop)
            return {"status": "selected"}

        def decide_ride_selection(ride_id, passenger_id, driver_id, decision):
            accepted.add((ride_id, passenger_id))
            return {"status": "accepted"}

        with patch.object(populate, "db") as database:
            database.get_user_by_email.side_effect = lambda email: users.get(int(email[8:10]))
            database.get_rides_by_user.side_effect = lambda user_id: rides[user_id]
            database.get_ride_request_counts.side_effect = lambda: {40: len(selections)}
            database.get_ride_selection_counts.side_effect = lambda: {40: len(accepted)}
            database.get_passenger_reserved_times.side_effect = lambda user_id: {
                ride.ride_time for (ride_id, selected_user_id) in selections
                for ride in rides[user_id] if selected_user_id == user_id
            }
            database.select_ride.side_effect = select_ride
            database.decide_ride_selection.side_effect = decide_ride_selection

            self.assertEqual(populate._ensure_seed_selections(), 2)
            self.assertEqual(populate._ensure_seed_selections(), 0)

        # Le passager du groupe decale (15 min) est dans la tolerance.
        self.assertEqual(selections, {(40, 18), (40, 35)})
        # Chaque demande garde son heure de passage et son detour estimes.
        self.assertTrue(all(stop and stop["passage_time"] and stop["detour_min"] is not None for stop in stops))
        # Seule la premiere demande est acceptee, l'autre attend le conducteur.
        self.assertEqual(len(accepted), 1)

    def test_free_test_account_is_never_booked(self):
        ride_time = datetime.now() + timedelta(days=2)
        users = {
            1: User(id=1, time_tolerance_min=15),
            2: User(id=2, car_seats=3, time_tolerance_min=15),
        }
        rides = {
            1: [Ride(id=10, user_id=1, ride_time=ride_time)],
            2: [Ride(id=20, user_id=2, ride_time=ride_time, is_offer=True)],
        }
        with patch.object(populate, "db") as database:
            database.get_user_by_email.side_effect = lambda email: users.get(int(email[8:10]))
            database.get_rides_by_user.side_effect = lambda user_id: rides[user_id]
            database.get_ride_request_counts.return_value = {}
            database.get_ride_selection_counts.return_value = {}
            database.get_passenger_reserved_times.return_value = set()

            self.assertEqual(populate._ensure_seed_selections(), 0)
            database.select_ride.assert_not_called()


if __name__ == "__main__":
    unittest.main()
