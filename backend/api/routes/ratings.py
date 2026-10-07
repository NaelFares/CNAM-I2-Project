"""Reputation d'un utilisateur : moyenne, palier et notes recues."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database import ride_ratings as ratings_db
from backend.database import ride_selections as selections_db
from backend.database.manager import db
from backend.models.user import User
from backend.services.photo_storage import build_photo_url
from backend.services.reputation import compute_tier, rides_to_next_tier

from backend.api.deps import require_current_user
from backend.api.feedback import raise_api_error
from backend.api.schemas import (
    ExperienceTierDTO,
    RatingSummaryDTO,
    ReceivedRatingDTO,
    UserRatingsResponse,
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


def _tier_dto(rides_count: int) -> ExperienceTierDTO:
    tier = compute_tier(rides_count)
    return ExperienceTierDTO(
        rides_count=rides_count,
        tier_key=tier.key,
        tier_label=tier.label,
        rides_to_next=rides_to_next_tier(rides_count),
    )


def _summary_dto(user_id: int) -> RatingSummaryDTO:
    """Moyenne des notes recues et paliers d'experience par role.

    Le palier se base sur les courses terminees des deux cotes, pas sur le
    nombre de notes : quelqu'un de jamais note progresse quand meme, et une
    course confirmee par les deux participants ne peut pas etre gonflee.
    """
    summary = ratings_db.get_summary(user_id)
    counts = selections_db.count_completed_rides(user_id)
    return RatingSummaryDTO(
        average=summary.average,
        count=summary.count,
        driver=_tier_dto(counts["driver"]),
        passenger=_tier_dto(counts["passenger"]),
    )


def _received_dto(row: dict) -> ReceivedRatingDTO:
    """Convertit une ligne jointe (note + auteur) en DTO d'affichage."""
    return ReceivedRatingDTO(
        id=row["id"],
        score=row["score"],
        comment=row.get("comment") or "",
        created_at=row["created_at"],
        rater_id=row.get("rater_id"),
        rater_name=row.get("rater_name") or "Utilisateur supprimé",
        rater_photo_url=build_photo_url(row.get("rater_photo_filename") or ""),
    )


@router.get("/me", response_model=UserRatingsResponse)
def my_ratings(user: User = Depends(require_current_user)):
    """Ma reputation et les notes que j'ai recues."""
    return UserRatingsResponse(
        summary=_summary_dto(user.id),
        ratings=[_received_dto(row) for row in ratings_db.get_received_ratings(user.id)],
    )


@router.get("/users/{user_id}", response_model=UserRatingsResponse)
def user_ratings(user_id: int, _: User = Depends(require_current_user)):
    """Reputation publique d'un autre utilisateur.

    Les commentaires sont exposes sans l'identite de leur auteur : ils
    servent a juger la personne notee, pas a retracer qui a dit quoi.
    """
    if not db.get_user_by_id(user_id):
        raise_api_error("RATING_NOT_A_PARTICIPANT", http_status=status.HTTP_404_NOT_FOUND)

    return UserRatingsResponse(
        summary=_summary_dto(user_id),
        ratings=[_received_dto(row) for row in ratings_db.get_received_ratings(user_id)],
    )
