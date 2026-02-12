"""
Modèle de données pour les événements de l'emploi du temps.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Event:
    """Représente un événement dans l'emploi du temps (cours, TD, etc.)"""

    id: Optional[int] = None
    user_id: int = 0
    title: str = ""
    start_time: datetime = None
    end_time: datetime = None
    location: str = ""
    description: str = ""

    def to_dict(self) -> dict:
        """Convertit l'événement en dictionnaire"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "location": self.location,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """Crée un événement depuis un dictionnaire"""
        start_time = None
        end_time = None

        if data.get("start_time"):
            if isinstance(data["start_time"], str):
                start_time = datetime.fromisoformat(data["start_time"])
            else:
                start_time = data["start_time"]

        if data.get("end_time"):
            if isinstance(data["end_time"], str):
                end_time = datetime.fromisoformat(data["end_time"])
            else:
                end_time = data["end_time"]

        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            title=data.get("title", ""),
            start_time=start_time,
            end_time=end_time,
            location=data.get("location", ""),
            description=data.get("description", ""),
        )

    def format_time(self) -> str:
        """Formate l'heure pour l'affichage"""
        if self.start_time:
            return self.start_time.strftime("%Y-%m-%d %H:%M")
        return "N/A"
