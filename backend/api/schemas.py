"""Pydantic DTOs for the HTTP API layer."""

from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from backend.api.constants import clean_music_genres


Gender = Literal["homme", "femme", "autre"]
MusicPreference = Literal["peu_importe", "avec", "sans"]
SmokingPreference = Literal["peu_importe", "fumeur", "non_fumeur"]


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
    role: Literal["driver", "passenger"] = "passenger"
    car_seats: int | None = Field(default=None, ge=1, le=4)
    gender: Gender  # obligatoire a l'inscription, pas de valeur par defaut
    music_preference: MusicPreference = "peu_importe"
    music_genres: list[str] = []
    smoking_preference: SmokingPreference = "peu_importe"
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0

    _normalize_genres = field_validator("music_genres")(clean_music_genres)


class LoginResponse(BaseModel):
    status: Literal["ok", "register_required"]
    user: "UserDTO | None" = None
    feedback: ApiMessage


class UserDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["driver", "passenger"]
    car_seats: int | None = None
    gender: Gender = "autre"
    # URL publique reconstruite par l'API depuis photo_filename ; vide si
    # aucune photo n'a ete televersee.
    photo_url: str = ""
    music_preference: MusicPreference = "peu_importe"
    music_genres: list[str] = []
    smoking_preference: SmokingPreference = "peu_importe"
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
    role: Literal["driver", "passenger"]
    car_seats: int | None = Field(default=None, ge=1, le=4)
    gender: Gender
    music_preference: MusicPreference = "peu_importe"
    music_genres: list[str] = []
    smoking_preference: SmokingPreference = "peu_importe"
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15
    school_address: str = ""
    school_lat: float = 0.0
    school_lon: float = 0.0

    _normalize_genres = field_validator("music_genres")(clean_music_genres)


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
    event_id: int | None = None
    ride_type: Literal["to_campus", "from_campus"]
    ride_time: datetime
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    status: Literal["active", "archived"] = "active"
    archived_at: datetime | None = None


class RidesGenerateResponse(BaseModel):
    rides: list[RideDTO]
    feedback: ApiMessage


class MatchDTO(BaseModel):
    ride_id: int
    driver_name: str
    driver_id: int
    # Trajet du conducteur, cible d'une reservation. None pour une recherche
    # rapide, dont le trajet est transitoire et n'existe pas en base.
    driver_ride_id: int | None = None
    driver_gender: Gender = "autre"
    driver_photo_url: str = ""
    # Ambiance du trajet : ce sont les preferences du conducteur qui
    # s'appliquent, puisque c'est sa voiture.
    driver_music_preference: MusicPreference = "peu_importe"
    driver_music_genres: list[str] = []
    driver_smoking_preference: SmokingPreference = "peu_importe"
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
    car_seats: int
    available_seats: int


class MatchesResponse(BaseModel):
    matches: list[MatchDTO]
    feedback: ApiMessage


class PlanningMatchRequest(BaseModel):
    week_start: date


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


TrackingStep = Literal["picked_up", "on_board", "completed", "arrived"]
TrackingStatus = Literal[
    "pending", "picking_up", "on_board", "arriving", "completed", "cancelled"
]


class RideTrackingDTO(BaseModel):
    """Une reservation et son suivi, vue par l'un des deux participants."""

    id: int
    ride_id: int
    ride_time: datetime
    ride_type: Literal["to_campus", "from_campus"]
    # Role du demandeur, qui determine les boutons a afficher.
    my_role: Literal["driver", "passenger"]
    # L'autre partie : c'est elle que l'utilisateur doit reconnaitre.
    counterpart_id: int
    counterpart_name: str
    counterpart_photo_url: str = ""
    status: TrackingStatus
    # Etape que le demandeur peut confirmer maintenant ; None s'il doit
    # attendre l'autre partie ou s'il a termine.
    next_step: TrackingStep | None = None
    driver_picked_up_at: datetime | None = None
    passenger_onboard_at: datetime | None = None
    driver_completed_at: datetime | None = None
    passenger_arrived_at: datetime | None = None


class RideTrackingListResponse(BaseModel):
    trackings: list[RideTrackingDTO]


class RideTrackingResponse(BaseModel):
    tracking: RideTrackingDTO
    feedback: ApiMessage


class DashboardSummaryResponse(BaseModel):
    events_count: int
    rides_count: int
    matches_count: int
    profile_completed: bool


class SelectedPassengerDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    selected_at: datetime
    selection_status: Literal["pending", "accepted", "rejected"]


class DriverOfferDTO(BaseModel):
    id: int
    ride_type: Literal["to_campus", "from_campus"]
    ride_time: datetime
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    status: Literal["active", "archived"]
    archived_at: datetime | None = None
    car_seats: int
    occupied_seats: int
    available_seats: int
    passengers: list[SelectedPassengerDTO] = Field(default_factory=list)


class DriverOffersResponse(BaseModel):
    rides: list[DriverOfferDTO]


class PassengerSelectionDTO(BaseModel):
    selection_id: int
    ride_id: int
    driver_id: int
    driver_name: str
    ride_type: Literal["to_campus", "from_campus"]
    ride_time: datetime
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    status: Literal["active", "archived"]
    selected_at: datetime
    selection_status: Literal["pending", "accepted", "rejected"]


class PassengerSelectionsResponse(BaseModel):
    rides: list[PassengerSelectionDTO]


class RideSelectionResponse(BaseModel):
    ride_id: int
    available_seats: int
    feedback: ApiMessage


LoginResponse.model_rebuild()
SchedulePreviewResponse.model_rebuild()
ScheduleConfirmResponse.model_rebuild()
ScheduleEventsResponse.model_rebuild()
