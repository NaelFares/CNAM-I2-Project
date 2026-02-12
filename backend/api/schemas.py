"""Pydantic DTOs for the HTTP API layer."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class ApiMessage(BaseModel):
    code: str
    message: str


class LoginRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: Literal["both", "driver", "passenger"] = "both"
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15


class LoginResponse(BaseModel):
    status: Literal["ok", "register_required"]
    user: "UserDTO | None" = None
    feedback: ApiMessage


class UserDTO(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: Literal["both", "driver", "passenger"]
    start_address: str
    start_lat: float
    start_lon: float
    time_tolerance_min: int


class SessionResponse(BaseModel):
    authenticated: bool
    user: UserDTO | None = None


class ProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    role: Literal["both", "driver", "passenger"]
    start_address: str = ""
    start_lat: float = 0.0
    start_lon: float = 0.0
    time_tolerance_min: int = 15


class GeocodeResult(BaseModel):
    display_name: str
    place_label: str = ""
    lat: float
    lon: float


class SchedulePreviewResponse(BaseModel):
    events: list["EventDTO"]
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
    passenger_name: str
    passenger_id: int
    ride_time: str
    ride_type: str
    time_diff_min: int
    distance_km: float
    score: int
    driver_coords: tuple[float, float]
    passenger_coords: tuple[float, float]
    campus_coords: tuple[float, float]


class MatchesResponse(BaseModel):
    matches: list[MatchDTO]
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
