"""Pydantic DTOs for the HTTP API layer."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


Gender = Literal["homme", "femme", "autre"]
MusicPreference = Literal["peu_importe", "avec", "sans"]
SmokingPreference = Literal["peu_importe", "fumeur", "non_fumeur"]

# Borne haute volontairement large : on valide une saisie plausible, pas un
# modele de vehicule precis.
MAX_CAR_SEATS = 8


class ApiMessage(BaseModel):
    code: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
    role: Literal["both", "driver", "passenger"] = "both"
    gender: Gender  # obligatoire a l'inscription, pas de valeur par defaut
    music_preference: MusicPreference = "peu_importe"
    smoking_preference: SmokingPreference = "peu_importe"
    car_seats: int = Field(default=0, ge=0, le=MAX_CAR_SEATS)
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0


class LoginResponse(BaseModel):
    status: Literal["ok", "register_required"]
    user: "UserDTO | None" = None
    feedback: ApiMessage


class UserDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["both", "driver", "passenger"]
    gender: Gender = "autre"
    # URL publique reconstruite par l'API depuis photo_filename ; vide si
    # aucune photo n'a ete televersee.
    photo_url: str = ""
    music_preference: MusicPreference = "peu_importe"
    smoking_preference: SmokingPreference = "peu_importe"
    car_seats: int = 0
    start_address: str
    start_lat: float
    start_lon: float
    time_tolerance_min: int
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0


class SessionResponse(BaseModel):
    authenticated: bool
    user: UserDTO | None = None


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: Literal["both", "driver", "passenger"]
    gender: Gender
    music_preference: MusicPreference = "peu_importe"
    smoking_preference: SmokingPreference = "peu_importe"
    car_seats: int = Field(default=0, ge=0, le=MAX_CAR_SEATS)
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0


class GeocodeResult(BaseModel):
    display_name: str
    place_label: str = ""
    lat: float
    lon: float


class SchedulePreviewResponse(BaseModel):
    events: list["EventDTO"]
    confidence_score: float | None = None
    requires_user_review: bool = False
    mapping_explanation: str | None = None
    feedback: ApiMessage


class ScheduleConfirmResponse(BaseModel):
    events: list["EventDTO"]
    feedback: ApiMessage


class ScheduleEventsResponse(BaseModel):
    events: list["EventDTO"]


class EventDTO(BaseModel):
    id: int | None = None
    user_id: int | None = None
    title: str
    start_time: datetime
    end_time: datetime
    location: str = ""
    description: str = ""


class RideDTO(BaseModel):
    id: int | None = None
    user_id: int
    event_id: int
    ride_type: Literal["to_campus", "from_campus"]
    ride_time: datetime
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float


class RidesGenerateResponse(BaseModel):
    rides: list[RideDTO]
    feedback: ApiMessage


class MatchDTO(BaseModel):
    driver_name: str
    driver_id: int
    driver_gender: Gender = "autre"
    driver_photo_url: str = ""
    # Ambiance du trajet : ce sont les preferences du conducteur qui
    # s'appliquent, puisque c'est sa voiture.
    driver_music_preference: MusicPreference = "peu_importe"
    driver_smoking_preference: SmokingPreference = "peu_importe"
    driver_car_seats: int = 0
    passenger_name: str
    passenger_id: int
    passenger_gender: Gender = "autre"
    passenger_photo_url: str = ""
    ride_time: str
    ride_type: str
    time_diff_min: int
    distance_km: float
    extra_time_min: float = 0.0
    score: int
    driver_coords: tuple[float, float]
    passenger_coords: tuple[float, float]
    campus_coords: tuple[float, float]
    route_geometry: list[list[float]] = []
    route_distance_km: float = 0.0


class MatchesResponse(BaseModel):
    matches: list[MatchDTO]
    feedback: ApiMessage


class MatchSearchRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    ride_time: datetime
    ride_type: Literal["to_campus", "from_campus"]
    # Option ponctuelle de la recherche : restreint les resultats aux femmes.
    # Reservee aux utilisatrices (cf. routes/matches.py).
    ladies_only: bool = False


class MatchSearchResponse(BaseModel):
    matches: list[MatchDTO]
    search_route_geometry: list[list[float]] = []
    feedback: ApiMessage


class DashboardSummaryResponse(BaseModel):
    events_count: int
    rides_count: int
    matches_count: int
    profile_completed: bool


LoginResponse.model_rebuild()
SchedulePreviewResponse.model_rebuild()
ScheduleConfirmResponse.model_rebuild()
ScheduleEventsResponse.model_rebuild()
