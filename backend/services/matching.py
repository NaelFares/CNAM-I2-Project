"""
Matching service between drivers and passengers.
"""

from typing import Dict, List

from backend.core.config import config
from backend.core.geo import haversine_distance
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User


class Match:
    """Represents one driver/passenger match."""

    def __init__(self, driver: User, passenger: User, driver_ride: Ride, passenger_ride: Ride):
        self.driver = driver
        self.passenger = passenger
        self.driver_ride = driver_ride
        self.passenger_ride = passenger_ride
        self.score = 0
        self.time_diff_min = 0
        self.distance_km = 0.0
        self._calculate_score()

    def _calculate_score(self):
        time_diff = abs((self.driver_ride.ride_time - self.passenger_ride.ride_time).total_seconds() / 60)
        self.time_diff_min = int(time_diff)

        distance = haversine_distance(
            self.driver_ride.start_lat,
            self.driver_ride.start_lon,
            self.passenger_ride.start_lat,
            self.passenger_ride.start_lon,
        )
        self.distance_km = distance

        max_tolerance = max(1, self.driver.time_tolerance_min, self.passenger.time_tolerance_min)
        if time_diff <= max_tolerance:
            time_score = 50 * (1 - time_diff / max_tolerance)
        else:
            time_score = 0

        max_distance = config.MAX_DISTANCE_KM
        if distance <= max_distance:
            distance_score = 50 * (1 - distance / max_distance)
        else:
            distance_score = 0

        self.score = int(time_score + distance_score)

    def to_dict(self) -> Dict:
        return {
            "driver_name": self.driver.name,
            "driver_id": self.driver.id,
            "passenger_name": self.passenger.name,
            "passenger_id": self.passenger.id,
            "ride_time": self.driver_ride.format_time(),
            "ride_type": self.driver_ride.get_direction_label(),
            "time_diff_min": self.time_diff_min,
            "distance_km": self.distance_km,
            "score": self.score,
            "driver_coords": (self.driver_ride.start_lat, self.driver_ride.start_lon),
            "passenger_coords": (self.passenger_ride.start_lat, self.passenger_ride.start_lon),
            "campus_coords": (self.driver_ride.end_lat, self.driver_ride.end_lon),
        }


class MatchingService:
    """Matching operations."""

    @staticmethod
    def find_matches(current_user: User, my_rides: List[Ride], all_rides: List[Ride]) -> List[Dict]:
        """
        Find compatible rides for the current user only.
        """
        matches: List[Match] = []

        for my_ride in my_rides:
            for other_ride in all_rides:
                if other_ride.user_id == current_user.id:
                    continue
                if my_ride.ride_type != other_ride.ride_type:
                    continue

                other_user = db.get_user_by_id(other_ride.user_id)
                if not other_user:
                    continue

                if current_user.is_driver() and other_user.is_passenger():
                    driver = current_user
                    passenger = other_user
                    driver_ride = my_ride
                    passenger_ride = other_ride
                elif current_user.is_passenger() and other_user.is_driver():
                    driver = other_user
                    passenger = current_user
                    driver_ride = other_ride
                    passenger_ride = my_ride
                else:
                    continue

                match = Match(driver, passenger, driver_ride, passenger_ride)
                if match.score >= config.MIN_MATCH_SCORE:
                    matches.append(match)

        matches.sort(key=lambda m: m.score, reverse=True)
        return [match.to_dict() for match in matches]


matching_service = MatchingService()

