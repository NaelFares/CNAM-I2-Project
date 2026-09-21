"""Profile endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, UploadFile, status

from backend.core.config import config
from backend.database.manager import db
from backend.models.user import User
from backend.services import photo_storage

from backend.api.constants import MAX_TIME_TOLERANCE, MIN_TIME_TOLERANCE
from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import ApiMessage, ProfileUpdateRequest, UserDTO
from backend.api.serialization import user_to_dto

router = APIRouter(prefix="/profile", tags=["profile"])
logger = logging.getLogger(__name__)


@router.get("", response_model=UserDTO)
def get_profile(user: User = Depends(require_current_user)):
    return user_to_dto(user)


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
        gender=payload.gender,
        # La photo n'est pas transportee par ce formulaire : on reporte celle
        # deja enregistree, pour que le DTO renvoye reste exact.
        photo_filename=user.photo_filename,
        music_preference=payload.music_preference,
        smoking_preference=payload.smoking_preference,
        car_seats=payload.car_seats,
        start_address=payload.start_address.strip(),
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        time_tolerance_min=payload.time_tolerance_min,
        school_address=payload.school_address.strip(),
        school_lat=payload.school_lat,
        school_lon=payload.school_lon,
    )
    db.update_user(next_user)
    return user_to_dto(next_user)


@router.post("/photo", response_model=UserDTO)
async def upload_profile_photo(
    file: UploadFile = File(...),
    user: User = Depends(require_current_user),
):
    content = await file.read()
    if not content:
        raise_api_error("PROFILE_PHOTO_EMPTY")

    if len(content) > photo_storage.max_size_bytes():
        raise_api_error(
            "PROFILE_PHOTO_TOO_LARGE",
            http_status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            max_mb=config.MAX_PHOTO_SIZE_MB,
        )

    # Le type est deduit du contenu reel, pas du Content-Type declare par le
    # client ni de l'extension du nom de fichier : les deux se falsifient.
    content_type = photo_storage.detect_content_type(content)
    if content_type not in photo_storage.ALLOWED_CONTENT_TYPES:
        raise_api_error("PROFILE_PHOTO_UNSUPPORTED")

    previous_filename = user.photo_filename
    try:
        filename = photo_storage.save_photo(user.id, content, content_type)
    except OSError as exc:
        logger.exception("Ecriture de la photo de profil impossible: %r", exc)
        raise_api_error(
            "PROFILE_PHOTO_SAVE_FAILED",
            http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    db.update_user_photo(user.id, filename)
    # L'ancien fichier n'est supprime qu'une fois le nouveau enregistre en
    # base : en cas d'echec, l'utilisateur garde une photo valide.
    if previous_filename and previous_filename != filename:
        photo_storage.delete_photo(previous_filename)

    user.photo_filename = filename
    return user_to_dto(user)


@router.delete("/photo", response_model=UserDTO)
def delete_profile_photo(user: User = Depends(require_current_user)):
    if user.photo_filename:
        db.update_user_photo(user.id, "")
        photo_storage.delete_photo(user.photo_filename)
        user.photo_filename = ""
    return user_to_dto(user)


@router.get("/feedback/success", response_model=ApiMessage)
def profile_feedback_success():
    return ApiMessage(**make_feedback("PROFILE_SAVE_SUCCESS"))
