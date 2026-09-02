"""
Modèle de données pour les utilisateurs (étudiants).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """Représente un étudiant utilisateur de l'application"""

    id: Optional[int] = None
    name: str = ""
    email: str = ""
    hashed_password: str = ""  # Stockage du mot de passe haché pour la sécurité
    role: str = "both"  # "driver", "passenger", "both"
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0

    def is_driver(self) -> bool:
        """Vérifie si l'utilisateur est conducteur"""
        return self.role in ["driver", "both"]

    def is_passenger(self) -> bool:
        """Vérifie si l'utilisateur est passager"""
        return self.role in ["passenger", "both"]

    def has_school_location(self) -> bool:
        return bool(self.school_lat and self.school_lon)

    def to_dict(self) -> dict:
        """Convertit l'utilisateur en dictionnaire"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role": self.role,
            "start_address": self.start_address,
            "start_lat": self.start_lat,
            "start_lon": self.start_lon,
            "time_tolerance_min": self.time_tolerance_min,
            "school_address": self.school_address,
            "school_lat": self.school_lat,
            "school_lon": self.school_lon,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Crée un utilisateur depuis un dictionnaire"""
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            email=data.get("email", ""),
            hashed_password=data.get("hashed_password", ""),
            role=data.get("role", "both"),
            start_address=data.get("start_address", ""),
            start_lat=data.get("start_lat", 0.0),
            start_lon=data.get("start_lon", 0.0),
            time_tolerance_min=data.get("time_tolerance_min", 15),
            school_address=data.get("school_address", ""),
            school_lat=data.get("school_lat", 0.0),
            school_lon=data.get("school_lon", 0.0),
        )
