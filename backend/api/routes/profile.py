"""Profile endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.database.manager import db
from backend.models.user import User

from backend.api.constants import MAX_TIME_TOLERANCE, MIN_TIME_TOLERANCE
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
        start_address=payload.start_address.strip(),
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        time_tolerance_min=payload.time_tolerance_min,
    )
    db.update_user(next_user)
    return UserDTO(**next_user.to_dict())


@router.get("/feedback/success", response_model=ApiMessage)
def profile_feedback_success():
    return ApiMessage(**make_feedback("PROFILE_SAVE_SUCCESS"))
