"""Tests cibles : plus de role exclusif, capacite de la voiture facultative.

Tout compte peut chercher un trajet et en proposer un. Seul le nombre de
places, renseigne au profil, conditionne la possibilite de proposer.
"""

import unittest

from pydantic import ValidationError

from backend.api.schemas import ProfileUpdateRequest, RegisterRequest
from backend.models.user import User


def _profile(**overrides) -> ProfileUpdateRequest:
    data = {"name": "Etudiant", "email": "etu@example.com", "gender": "autre"}
    data.update(overrides)
    return ProfileUpdateRequest(**data)


class DrivingCapabilityTests(unittest.TestCase):
    def test_user_with_seats_can_drive(self):
        self.assertTrue(User(car_seats=3).can_drive())

    def test_user_without_car_cannot_drive(self):
        """Il peut tout de meme chercher : seul proposer lui est ferme."""
        self.assertFalse(User(car_seats=None).can_drive())

    def test_user_model_has_no_role_anymore(self):
        self.assertFalse(hasattr(User(), "role"))


class RegistrationTests(unittest.TestCase):
    def test_registration_asks_neither_role_nor_seats(self):
        """Le nombre de places se renseigne ensuite, au profil."""
        self.assertNotIn("role", RegisterRequest.model_fields)
        self.assertNotIn("car_seats", RegisterRequest.model_fields)

    def test_registration_still_requires_gender(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(name="Sans sexe", email="x@example.com", password="Test1234!")


class CarSeatsTests(unittest.TestCase):
    def test_seats_are_optional(self):
        self.assertIsNone(_profile().car_seats)

    def test_seats_accept_one_to_four(self):
        for seats in range(1, 5):
            with self.subTest(seats=seats):
                self.assertEqual(_profile(car_seats=seats).car_seats, seats)

    def test_seats_reject_values_outside_one_to_four(self):
        for seats in (0, 5):
            with self.subTest(seats=seats), self.assertRaises(ValidationError):
                _profile(car_seats=seats)


if __name__ == "__main__":
    unittest.main()
