import unittest
from datetime import datetime

from backend.models.ride_selection import RideSelection
from backend.services import ride_tracking

NOW = datetime(2026, 9, 28, 8, 0)
DRIVER_ID = 1
PASSENGER_ID = 2
STRANGER_ID = 99


def _selection(**kwargs) -> RideSelection:
    """Reservation acceptee par defaut : le suivi ne concerne que celles-la."""
    kwargs.setdefault("selection_status", "accepted")
    return RideSelection(id=10, ride_id=5, passenger_id=PASSENGER_ID, **kwargs)


class StatusTests(unittest.TestCase):
    def test_pending_when_nothing_confirmed(self):
        self.assertEqual(_selection().status, "pending")

    def test_picking_up_with_only_one_confirmation(self):
        self.assertEqual(_selection(driver_picked_up_at=NOW).status, "picking_up")
        self.assertEqual(_selection(passenger_onboard_at=NOW).status, "picking_up")

    def test_on_board_requires_both(self):
        selection = _selection(driver_picked_up_at=NOW, passenger_onboard_at=NOW)
        self.assertEqual(selection.status, "on_board")
        self.assertTrue(selection.is_pickup_confirmed())

    def test_arriving_with_only_one_completion(self):
        selection = _selection(
            driver_picked_up_at=NOW, passenger_onboard_at=NOW, driver_completed_at=NOW
        )
        self.assertEqual(selection.status, "arriving")
        self.assertFalse(selection.is_completed())

    def test_completed_requires_both(self):
        selection = _selection(
            driver_picked_up_at=NOW,
            passenger_onboard_at=NOW,
            driver_completed_at=NOW,
            passenger_arrived_at=NOW,
        )
        self.assertEqual(selection.status, "completed")
        self.assertTrue(selection.is_completed())

    def test_cancelled_wins_over_everything(self):
        selection = _selection(driver_picked_up_at=NOW, selection_status="rejected")
        self.assertEqual(selection.status, "cancelled")

    def test_pending_selection_has_no_tracking(self):
        """Une demande non encore acceptee n'a aucune etape a confirmer."""
        selection = _selection(selection_status="pending")
        self.assertEqual(selection.status, "pending")
        self.assertIsNone(ride_tracking.next_step_for(selection, "driver"))
        self.assertIsNone(ride_tracking.next_step_for(selection, "passenger"))


class AuthorizationTests(unittest.TestCase):
    """Chacun ne confirme que sa propre etape."""

    def _evaluate(self, step, user_id, **kwargs):
        return ride_tracking.evaluate_step(_selection(**kwargs), step, user_id, DRIVER_ID)

    def test_driver_confirms_pickup(self):
        self.assertTrue(self._evaluate("picked_up", DRIVER_ID).allowed)

    def test_passenger_cannot_confirm_driver_step(self):
        decision = self._evaluate("picked_up", PASSENGER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_STEP_FORBIDDEN")

    def test_driver_cannot_confirm_passenger_step(self):
        decision = self._evaluate("on_board", DRIVER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_STEP_FORBIDDEN")

    def test_stranger_is_treated_as_unknown(self):
        """Un tiers ne doit pas apprendre que cette reservation existe."""
        decision = self._evaluate("picked_up", STRANGER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_NOT_A_PARTICIPANT")

    def test_unknown_step_rejected(self):
        decision = self._evaluate("teleported", DRIVER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_STEP_UNKNOWN")

    def test_cancelled_selection_accepts_nothing(self):
        decision = self._evaluate("picked_up", DRIVER_ID, selection_status="rejected")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_SELECTION_CANCELLED")


class CompletionOrderTests(unittest.TestCase):
    """On ne termine pas une course que personne n'a commencee."""

    def _evaluate(self, step, user_id, **kwargs):
        return ride_tracking.evaluate_step(_selection(**kwargs), step, user_id, DRIVER_ID)

    def test_completion_refused_before_pickup(self):
        decision = self._evaluate("completed", DRIVER_ID)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_PICKUP_REQUIRED")

    def test_completion_refused_with_half_pickup(self):
        decision = self._evaluate("arrived", PASSENGER_ID, driver_picked_up_at=NOW)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.error_code, "TRACKING_PICKUP_REQUIRED")

    def test_completion_allowed_after_full_pickup(self):
        both = {"driver_picked_up_at": NOW, "passenger_onboard_at": NOW}
        self.assertTrue(self._evaluate("completed", DRIVER_ID, **both).allowed)
        self.assertTrue(self._evaluate("arrived", PASSENGER_ID, **both).allowed)

    def test_allowed_decision_targets_right_column(self):
        both = {"driver_picked_up_at": NOW, "passenger_onboard_at": NOW}
        self.assertEqual(self._evaluate("completed", DRIVER_ID, **both).column, "driver_completed_at")
        self.assertEqual(self._evaluate("arrived", PASSENGER_ID, **both).column, "passenger_arrived_at")


class NextStepTests(unittest.TestCase):
    """L'interface n'affiche qu'un bouton a la fois, celui qui a du sens."""

    def test_first_steps(self):
        selection = _selection()
        self.assertEqual(ride_tracking.next_step_for(selection, "driver"), "picked_up")
        self.assertEqual(ride_tracking.next_step_for(selection, "passenger"), "on_board")

    def test_waits_for_counterpart_before_completion(self):
        """Conducteur ayant confirme la prise en charge, passager pas encore."""
        selection = _selection(driver_picked_up_at=NOW)
        self.assertIsNone(ride_tracking.next_step_for(selection, "driver"))
        self.assertEqual(ride_tracking.next_step_for(selection, "passenger"), "on_board")

    def test_completion_offered_once_on_board(self):
        selection = _selection(driver_picked_up_at=NOW, passenger_onboard_at=NOW)
        self.assertEqual(ride_tracking.next_step_for(selection, "driver"), "completed")
        self.assertEqual(ride_tracking.next_step_for(selection, "passenger"), "arrived")

    def test_nothing_left_when_done(self):
        selection = _selection(
            driver_picked_up_at=NOW,
            passenger_onboard_at=NOW,
            driver_completed_at=NOW,
            passenger_arrived_at=NOW,
        )
        self.assertIsNone(ride_tracking.next_step_for(selection, "driver"))
        self.assertIsNone(ride_tracking.next_step_for(selection, "passenger"))

    def test_nothing_left_when_cancelled(self):
        selection = _selection(selection_status="rejected")
        self.assertIsNone(ride_tracking.next_step_for(selection, "driver"))
        self.assertIsNone(ride_tracking.next_step_for(selection, "passenger"))


class FromDictTests(unittest.TestCase):
    def test_missing_tracking_columns_default_to_none(self):
        selection = RideSelection.from_dict({"id": 1, "ride_id": 2, "passenger_id": 3})
        self.assertIsNone(selection.driver_picked_up_at)
        self.assertEqual(selection.status, "pending")

    def test_status_column_is_read_from_her_schema(self):
        """La colonne s'appelle `status` en base, `selection_status` ici."""
        selection = RideSelection.from_dict(
            {"id": 1, "ride_id": 2, "passenger_id": 3, "status": "accepted"}
        )
        self.assertTrue(selection.is_accepted())


if __name__ == "__main__":
    unittest.main()
