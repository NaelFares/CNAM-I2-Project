import unittest
from datetime import datetime

from backend.models.ride import Ride


class RideTypeTests(unittest.TestCase):
    def test_legacy_ride_type_is_normalized(self):
        ride = Ride.from_dict(
            {
                "ride_type": "aller",
                "ride_time": datetime.now().isoformat(),
            }
        )
        self.assertEqual(ride.ride_type, "to_campus")
        self.assertEqual(ride.get_direction_label(), "Vers le campus")

    def test_modern_ride_type_from_campus(self):
        ride = Ride.from_dict(
            {
                "ride_type": "from_campus",
                "ride_time": datetime.now().isoformat(),
            }
        )
        self.assertEqual(ride.ride_type, "from_campus")
        self.assertEqual(ride.get_direction_label(), "Depuis le campus")


if __name__ == "__main__":
    unittest.main()

