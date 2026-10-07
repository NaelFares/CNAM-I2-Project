"""Reputation d'un utilisateur : moyenne, palier et notes recues."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database import ride_ratings as ratings_db
from backend.database.manager import db
from backend.models.user import User
from backend.services.reputation import compute_tier

from backend.api.deps import require_current_user
from backend.api.feedback import raise_api_error
from backend.api.schemas import (
    RatingSummaryDTO,
    ReceivedRatingDTO,
    UserRatingsResponse,
)

router = APIRouter(prefix="/ratings", tags=["ratings"])


def _summary_dto(user_id: int) -> RatingSummaryDTO:
    """Moyenne et palier d'un utilisateur.

    Le nombre de courses retenu pour le palier est le nombre de notes
    recues, et non le nombre de reservations : une course notee est une
    course dont l'autre participant atteste qu'elle a bien eu lieu.
    """
    summary = ratings_db.get_summary(user_id)
    tier = compute_tier(summary.count, summary.average)
    return RatingSummaryDTO(
        average=summary.average,
        count=summary.count,
        tier_key=tier.key,
        tier_label=tier.label,
    )


@router.get("/me", response_model=UserRatingsResponse)
def my_ratings(user: User = Depends(require_current_user)):
    """Ma reputation et les notes que j'ai recues."""
    return UserRatingsResponse(
        summary=_summary_dto(user.id),
        ratings=[
            ReceivedRatingDTO(score=r.score, comment=r.comment, created_at=r.created_at)
            for r in ratings_db.get_received_ratings(user.id)
        ],
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
        ratings=[
            ReceivedRatingDTO(score=r.score, comment=r.comment, created_at=r.created_at)
            for r in ratings_db.get_received_ratings(user_id)
        ],
    )
