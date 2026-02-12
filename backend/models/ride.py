"""
Data model for carpool rides generated from schedule events.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Ride:
    """Represents a generated ride."""

    id: Optional[int] = None
    user_id: int = 0
    event_id: int = 0
    ride_type: str = "to_campus"  # Canonical: to_campus or from_campus
    ride_time: datetime = None
    start_lat: float = 0.0
    start_lon: float = 0.0
    end_lat: float = 0.0
    end_lon: float = 0.0

    @staticmethod
    def normalize_ride_type(ride_type: str) -> str:
        mapping = {
            "aller": "to_campus",
            "retour": "from_campus",
            "to_campus": "to_campus",
            "from_campus": "from_campus",
        }
        return mapping.get(ride_type, "to_campus")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_id": self.event_id,
            "ride_type": self.normalize_ride_type(self.ride_type),
            "ride_time": self.ride_time.isoformat() if self.ride_time else None,
            "start_lat": self.start_lat,
            "start_lon": self.start_lon,
            "end_lat": self.end_lat,
            "end_lon": self.end_lon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ride":
        ride_time = None
        if data.get("ride_time"):
            if isinstance(data["ride_time"], str):
                ride_time = datetime.fromisoformat(data["ride_time"])
            else:
                ride_time = data["ride_time"]

        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            event_id=data.get("event_id", 0),
            ride_type=cls.normalize_ride_type(data.get("ride_type", "to_campus")),
            ride_time=ride_time,
            start_lat=data.get("start_lat", 0.0),
            start_lon=data.get("start_lon", 0.0),
            end_lat=data.get("end_lat", 0.0),
            end_lon=data.get("end_lon", 0.0),
        )

    def format_time(self) -> str:
        if self.ride_time:
            return self.ride_time.strftime("%Y-%m-%d %H:%M")
        return "N/A"

    def get_direction_label(self) -> str:
        ride_type = self.normalize_ride_type(self.ride_type)
        return "Vers le campus" if ride_type == "to_campus" else "Depuis le campus"

