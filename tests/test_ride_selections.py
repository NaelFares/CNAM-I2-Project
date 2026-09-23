"""Tests unitaires de la réservation de places sans base réelle."""

from datetime import datetime
import unittest
from unittest.mock import MagicMock, patch

from backend.database.manager import Database


class RideSelectionTests(unittest.TestCase):
    def setUp(self):
        self.database = Database()
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.cursor.return_value = self.cursor

    def _patch_connection(self):
        return patch.object(
            self.database,
            "get_connection",
            return_value=self.connection,
        )

    def test_select_ride_locks_it_and_returns_remaining_seats(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {
                "id": 25,
                "user_id": 10,
                "status": "active",
                "owner_role": "driver",
                "car_seats": 3,
                "is_past": False,
                "ride_time": datetime(2026, 9, 28, 8, 15),
            },
            None,
            None,
            {"count": 1},
        ]

        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.select_ride(ride_id=25, passenger_id=7)

        self.assertEqual(
            result,
            {"status": "selected", "available_seats": 2},
        )
        self.assertIn("FOR UPDATE", self.cursor.execute.call_args_list[0].args[0])
        self.assertIn("FOR UPDATE OF r", self.cursor.execute.call_args_list[1].args[0])
        self.connection.commit.assert_called_once_with()
        self.connection.close.assert_called_once_with()
        insert_query = self.cursor.execute.call_args_list[-1].args[0]
        self.assertIn("'pending'", insert_query)

    def test_driver_accepts_pending_passenger(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {"id": 25, "status": "active", "ride_time": datetime(2026, 9, 28, 8, 15),
             "car_seats": 3, "is_past": False},
            {"id": 5, "status": "pending"},
            {"count": 1},
            None,
        ]
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.decide_ride_selection(25, 7, 10, "accept")

        self.assertEqual(result, {"status": "accepted", "available_seats": 1})
        self.assertEqual(self.cursor.execute.call_args.args[1], ("accepted", 5))
        self.connection.commit.assert_called_once_with()

    def test_driver_rejects_accepted_passenger_and_frees_seat(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {"id": 25, "status": "active", "ride_time": datetime(2026, 9, 28, 8, 15),
             "car_seats": 3, "is_past": False},
            {"id": 5, "status": "accepted"},
            {"count": 2},
        ]
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.decide_ride_selection(25, 7, 10, "reject")

        self.assertEqual(result, {"status": "rejected", "available_seats": 2})
        self.connection.commit.assert_called_once_with()

    def test_driver_cannot_accept_when_car_is_full(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {"id": 25, "status": "active", "ride_time": datetime(2026, 9, 28, 8, 15),
             "car_seats": 1, "is_past": False},
            {"id": 5, "status": "pending"},
            {"count": 1},
        ]
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.decide_ride_selection(25, 7, 10, "accept")

        self.assertEqual(result, {"status": "full"})
        self.connection.commit.assert_not_called()

    def test_driver_cannot_accept_conflicting_reservation(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {"id": 25, "status": "active", "ride_time": datetime(2026, 9, 28, 8, 15),
             "car_seats": 3, "is_past": False},
            {"id": 5, "status": "pending"},
            {"count": 0},
            {"exists": 1},
        ]
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.decide_ride_selection(25, 7, 10, "accept")

        self.assertEqual(result, {"status": "time_conflict"})
        self.connection.commit.assert_not_called()

    def test_other_driver_cannot_decide_passenger(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, None]
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.decide_ride_selection(25, 7, 99, "accept")

        self.assertEqual(result, {"status": "not_found"})
        self.assertEqual(self.cursor.execute.call_args.args[1], (25, 99))
        self.connection.commit.assert_not_called()

    def test_select_ride_refuses_a_full_car(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {
                "id": 25,
                "user_id": 10,
                "status": "active",
                "owner_role": "driver",
                "car_seats": 1,
                "is_past": False,
                "ride_time": datetime(2026, 9, 28, 8, 15),
            },
            None,
            None,
            {"count": 1},
        ]

        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.select_ride(ride_id=25, passenger_id=7)

        self.assertEqual(result, {"status": "full"})
        self.connection.commit.assert_not_called()

    def test_select_ride_refuses_a_duplicate_selection(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {
                "id": 25,
                "user_id": 10,
                "status": "active",
                "owner_role": "driver",
                "car_seats": 4,
                "is_past": False,
                "ride_time": datetime(2026, 9, 28, 8, 15),
            },
            {"exists": 1},
        ]

        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.select_ride(ride_id=25, passenger_id=7)

        self.assertEqual(result, {"status": "already_selected"})
        self.connection.commit.assert_not_called()

    def test_select_ride_refuses_another_ride_at_the_same_minute(self):
        ride_time = datetime(2026, 9, 28, 8, 15)
        self.cursor.fetchone.side_effect = [
            {"id": 7},
            {
                "id": 26,
                "user_id": 11,
                "status": "active",
                "owner_role": "driver",
                "car_seats": 4,
                "is_past": False,
                "ride_time": ride_time,
            },
            None,
            {"exists": 1},
        ]

        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            self._patch_connection(),
        ):
            result = self.database.select_ride(ride_id=26, passenger_id=7)

        self.assertEqual(result, {"status": "time_conflict"})
        conflict_query, params = self.cursor.execute.call_args_list[3].args
        self.assertIn("date_trunc('minute'", conflict_query)
        self.assertEqual(params, (7, ride_time))
        self.connection.commit.assert_not_called()

    def test_cancel_only_removes_the_connected_passenger_selection(self):
        self.cursor.fetchone.return_value = None

        with self._patch_connection():
            result = self.database.cancel_ride_selection(
                ride_id=25,
                passenger_id=7,
            )

        self.assertEqual(result, {"status": "not_found"})
        query, parameters = self.cursor.execute.call_args.args
        self.assertIn("passenger_id = %s", query)
        self.assertEqual(parameters, (25, 7))
        self.connection.rollback.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
