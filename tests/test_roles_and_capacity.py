"""Tests ciblés pour les rôles exclusifs et la capacité conducteur."""

import unittest

from pydantic import ValidationError

from backend.api.schemas import RegisterRequest
from backend.models.user import User


class RolesAndCapacityTests(unittest.TestCase):
    def test_roles_are_exclusive_in_user_helpers(self):
        driver = User(role="driver", car_seats=4)
        passenger = User(role="passenger")

        self.assertTrue(driver.is_driver())
        self.assertFalse(driver.is_passenger())
        self.assertTrue(passenger.is_passenger())
        self.assertFalse(passenger.is_driver())

    def test_legacy_both_role_is_rejected_by_api_schema(self):
        with self.assertRaises(ValidationError):
            RegisterRequest(
                name="Ancien profil",
                email="ancien@example.com",
                password="Test1234!",
                role="both",
            )

    def test_driver_capacity_accepts_one_to_four_seats(self):
        for seats in range(1, 5):
            payload = RegisterRequest(
                name="Conducteur",
                email=f"driver{seats}@example.com",
                password="Test1234!",
                role="driver",
                car_seats=seats,
            )
            self.assertEqual(payload.car_seats, seats)

    def test_driver_capacity_rejects_values_outside_one_to_four(self):
        for seats in (0, 5):
            with self.subTest(seats=seats), self.assertRaises(ValidationError):
                RegisterRequest(
                    name="Conducteur",
                    email=f"invalid{seats}@example.com",
                    password="Test1234!",
                    role="driver",
                    car_seats=seats,
                )


if __name__ == "__main__":
    unittest.main()
