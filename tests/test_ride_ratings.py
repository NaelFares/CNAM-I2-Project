import unittest
from datetime import datetime

from backend.models.ride_rating import RatingSummary
from backend.models.ride_selection import RideSelection
from backend.services import ride_rating_rules

NOW = datetime(2026, 10, 7, 8, 0)
DRIVER_ID = 1
PASSENGER_ID = 2
STRANGER_ID = 99


def _completed(**kwargs) -> RideSelection:
    """Course terminee des deux cotes : le seul etat ou noter est permis."""
    base = dict(
        id=10,
        ride_id=5,
        passenger_id=PASSENGER_ID,
        selection_status="accepted",
        driver_picked_up_at=NOW,
        passenger_onboard_at=NOW,
        driver_completed_at=NOW,
        passenger_arrived_at=NOW,
    )
    base.update(kwargs)
    return RideSelection(**base)


class WhoCanRateTests(unittest.TestCase):
    def _evaluate(self, user_id, score=5, already=False, **kwargs):
        return ride_rating_rules.evaluate_rating(
            _completed(**kwargs), user_id, DRIVER_ID, score, already_rated=already
        )

    def test_passenger_rates_the_driver(self):
        decision = self._evaluate(PASSENGER_ID)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.rated_id, DRIVER_ID)

    def test_driver_rates_the_passenger(self):
        decision = self._evaluate(DRIVER_ID)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.rated_id, PASSENGER_ID)

    def test_nobody_rates_themselves(self):
        """Le destinataire est toujours l'autre participant."""
        for user_id in (DRIVER_ID, PASSENGER_ID):
            self.assertNotEqual(self._evaluate(user_id).rated_id, user_id)

    def test_stranger_is_treated_as_unknown(self):
        decision = self._evaluate(STRANGER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "RATING_NOT_A_PARTICIPANT")


class WhenRatingIsAllowedTests(unittest.TestCase):
    """On ne note qu'une course reellement terminee."""

    def _evaluate(self, selection, user_id=PASSENGER_ID, score=5, already=False):
        return ride_rating_rules.evaluate_rating(
            selection, user_id, DRIVER_ID, score, already_rated=already
        )

    def test_refused_before_any_confirmation(self):
        selection = _completed(
            driver_picked_up_at=None,
            passenger_onboard_at=None,
            driver_completed_at=None,
            passenger_arrived_at=None,
        )
        decision = self._evaluate(selection)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "RATING_RIDE_NOT_COMPLETED")

    def test_refused_when_only_one_side_confirmed_the_end(self):
        """Le conducteur a termine, le passager n'a pas confirme son arrivee."""
        selection = _completed(passenger_arrived_at=None)
        decision = self._evaluate(selection)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "RATING_RIDE_NOT_COMPLETED")

    def test_refused_on_cancelled_ride(self):
        selection = _completed(selection_status="rejected")
        decision = self._evaluate(selection)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "RATING_SELECTION_CANCELLED")

    def test_allowed_once_both_confirmed(self):
        self.assertTrue(self._evaluate(_completed()).allowed)


class ScoreValidationTests(unittest.TestCase):
    def _evaluate(self, score):
        return ride_rating_rules.evaluate_rating(
            _completed(), PASSENGER_ID, DRIVER_ID, score, already_rated=False
        )

    def test_accepts_one_to_five(self):
        for score in (1, 2, 3, 4, 5):
            self.assertTrue(self._evaluate(score).allowed, f"score {score} refuse")

    def test_rejects_out_of_range(self):
        for score in (0, 6, -1, 100):
            decision = self._evaluate(score)
            self.assertFalse(decision.allowed, f"score {score} accepte")
            self.assertEqual(decision.error_code, "RATING_SCORE_INVALID")

    def test_rejects_non_integer(self):
        self.assertFalse(self._evaluate(3.5).allowed)


class DefinitiveRatingTests(unittest.TestCase):
    """Une note est definitive : une seule par personne et par course."""

    def test_second_rating_refused(self):
        decision = ride_rating_rules.evaluate_rating(
            _completed(), PASSENGER_ID, DRIVER_ID, 5, already_rated=True
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "RATING_ALREADY_RATED")

    def test_can_rate_now_drives_the_form(self):
        self.assertTrue(ride_rating_rules.can_rate_now(_completed(), already_rated=False))
        self.assertFalse(ride_rating_rules.can_rate_now(_completed(), already_rated=True))
        self.assertFalse(
            ride_rating_rules.can_rate_now(_completed(passenger_arrived_at=None), already_rated=False)
        )


class RatingSummaryTests(unittest.TestCase):
    def test_no_rating_yields_none_not_zero(self):
        """Distinguer 'jamais note' de 'mal note' : compute_tier en depend."""
        summary = RatingSummary.from_dict({"average": None, "count": 0})
        self.assertIsNone(summary.average)
        self.assertEqual(summary.count, 0)

    def test_average_is_rounded(self):
        summary = RatingSummary.from_dict({"average": 4.33333, "count": 3})
        self.assertEqual(summary.average, 4.33)
        self.assertEqual(summary.count, 3)


if __name__ == "__main__":
    unittest.main()
