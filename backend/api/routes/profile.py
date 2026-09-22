"""Profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database.manager import db
from backend.models.user import User

from backend.api.constants import (
    MAX_CAR_SEATS,
    MAX_TIME_TOLERANCE,
    MIN_CAR_SEATS,
    MIN_TIME_TOLERANCE,
)
from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import ApiMessage, ProfileUpdateRequest, UserDTO

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserDTO)
def get_profile(user: User = Depends(require_current_user)):
    return UserDTO(**user.to_dict())


@router.put("", response_model=UserDTO)
def update_profile(payload: ProfileUpdateRequest, user: User = Depends(require_current_user)):
    if payload.time_tolerance_min < MIN_TIME_TOLERANCE or payload.time_tolerance_min > MAX_TIME_TOLERANCE:
        raise_api_error("VALIDATION_TIME_TOLERANCE_INVALID")

    if payload.role == "driver" and not (
        payload.car_seats is not None
        and MIN_CAR_SEATS <= payload.car_seats <= MAX_CAR_SEATS
    ):
        raise_api_error("VALIDATION_CAR_SEATS_INVALID")

    max_occupancy = db.get_max_active_occupancy_for_driver(user.id)
    if max_occupancy and (
        payload.role != "driver" or payload.car_seats < max_occupancy
    ):
        raise_api_error(
            "VALIDATION_CAR_SEATS_OCCUPIED",
            http_status=status.HTTP_409_CONFLICT,
            count=max_occupancy,
        )

    if (
        user.is_passenger()
        and payload.role == "driver"
        and db.get_passenger_selections(user.id)
    ):
        raise_api_error(
            "VALIDATION_ROLE_ACTIVE_SELECTIONS",
            http_status=status.HTTP_409_CONFLICT,
        )

    car_seats = payload.car_seats if payload.role == "driver" else None

    same_email = str(payload.email).strip().lower() == user.email.lower()
    if not same_email:
        existing = db.get_user_by_email(str(payload.email).strip().lower())
        if existing and existing.id != user.id:
            raise_api_error("REGISTER_REQUIRED_FIELDS")

    next_user = User(
        id=user.id,
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        role=payload.role,
        car_seats=car_seats,
        start_address=payload.start_address.strip(),
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        time_tolerance_min=payload.time_tolerance_min,
        school_address=payload.school_address.strip(),
        school_lat=payload.school_lat,
        school_lon=payload.school_lon,
    )
    db.update_user(next_user)
    return UserDTO(**next_user.to_dict())


@router.get("/feedback/success", response_model=ApiMessage)
def profile_feedback_success():
    return ApiMessage(**make_feedback("PROFILE_SAVE_SUCCESS"))
