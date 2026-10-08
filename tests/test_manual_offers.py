"""Trajets proposes a la main, independamment de l'emploi du temps."""

from datetime import datetime
import unittest
from unittest.mock import MagicMock, patch

from backend.database.manager import Database
from backend.models.ride import Ride

WHEN = datetime(2030, 10, 19, 10, 30)


def _ride(**overrides) -> Ride:
    data = dict(
        user_id=7, event_id=None, ride_type="to_campus", ride_time=WHEN,
        start_lat=43.60, start_lon=1.44, end_lat=43.56, end_lon=1.47,
        is_offer=True, start_address="12 rue de Metz", end_address="INSA Toulouse",
    )
    data.update(overrides)
    return Ride(**data)


class _DbTestCase(unittest.TestCase):
    def setUp(self):
        self.database = Database()
        self.connection = MagicMock()
        self.cursor = MagicMock()
        self.connection.cursor.return_value = self.cursor

    def _run(self, method, *args):
        with (
            patch.object(self.database, "archive_expired_rides", return_value=0),
            patch.object(self.database, "get_connection", return_value=self.connection),
        ):
            return getattr(self.database, method)(*args)


class CreateOfferTests(_DbTestCase):
    def test_creates_an_offer_outside_the_timetable(self):
        self.cursor.fetchone.side_effect = [
            {"id": 7, "car_seats": 3},
            {"is_past": False},
            None,          # aucun conflit a cette minute
            {"id": 42},
        ]
        result = self._run("create_offer", _ride())

        self.assertEqual(result, {"status": "created", "ride_id": 42})
        insert_query, params = self.cursor.execute.call_args_list[-1].args
        self.assertIn("NULL", insert_query)     # event_id NULL : hors emploi du temps
        self.assertIn("TRUE", insert_query)     # directement propose
        self.assertIn("12 rue de Metz", params)
        self.connection.commit.assert_called_once_with()

    def test_requires_a_car(self):
        self.cursor.fetchone.side_effect = [{"id": 7, "car_seats": None}]
        self.assertEqual(self._run("create_offer", _ride()), {"status": "no_car"})
        self.connection.commit.assert_not_called()

    def test_refuses_a_past_time(self):
        self.cursor.fetchone.side_effect = [{"id": 7, "car_seats": 3}, {"is_past": True}]
        self.assertEqual(self._run("create_offer", _ride()), {"status": "past"})
        self.connection.commit.assert_not_called()

    def test_refuses_a_minute_already_taken(self):
        """Ni deux voitures, ni conduire et etre passager a la fois."""
        self.cursor.fetchone.side_effect = [
            {"id": 7, "car_seats": 3}, {"is_past": False}, {"exists": 1},
        ]
        self.assertEqual(self._run("create_offer", _ride()), {"status": "time_conflict"})
        conflict_query = self.cursor.execute.call_args_list[2].args[0]
        self.assertIn("is_offer", conflict_query)
        self.assertIn("ride_selections", conflict_query)
        self.connection.commit.assert_not_called()


class WithdrawOfferTests(_DbTestCase):
    def test_manual_offer_is_deleted(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, {"id": 42, "event_id": None}, None]
        self.assertEqual(self._run("withdraw_offer", 42, 7), {"status": "withdrawn"})
        self.assertIn("DELETE FROM rides", self.cursor.execute.call_args_list[-1].args[0])

    def test_timetable_offer_becomes_a_search_again(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, {"id": 43, "event_id": 10}, None]
        self.assertEqual(self._run("withdraw_offer", 43, 7), {"status": "withdrawn"})
        self.assertIn("is_offer = FALSE", self.cursor.execute.call_args_list[-1].args[0])

    def test_refused_while_passengers_are_waiting_or_accepted(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, {"id": 42, "event_id": None}, {"exists": 1}]
        self.assertEqual(self._run("withdraw_offer", 42, 7), {"status": "has_passengers"})
        self.connection.commit.assert_not_called()

    def test_someone_elses_ride_is_not_found(self):
        self.cursor.fetchone.side_effect = [{"id": 7}, None]
        self.assertEqual(self._run("withdraw_offer", 42, 7), {"status": "not_found"})


class TimetableReimportTests(_DbTestCase):
    def test_reimport_spares_manual_offers(self):
        """Reimporter son emploi du temps ne doit pas effacer un trajet propose a la main."""
        self._run("delete_active_rides_by_user", 7)
        query = self.cursor.execute.call_args.args[0]
        self.assertIn("event_id IS NOT NULL", query)


if __name__ == "__main__":
    unittest.main()
