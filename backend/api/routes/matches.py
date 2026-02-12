"""Matching endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.database.manager import db
from backend.models.user import User
from backend.services.matching import matching_service

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback
from backend.api.schemas import MatchDTO, MatchesResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/find", response_model=MatchesResponse)
def find_matches(user: User = Depends(require_current_user)):
    my_rides = db.get_rides_by_user(user.id)
    all_rides = db.get_all_rides()
    matches = matching_service.find_matches(current_user=user, my_rides=my_rides, all_rides=all_rides)

    return MatchesResponse(
        matches=[MatchDTO(**match) for match in matches],
        feedback=make_feedback("MATCHES_FOUND", count=len(matches)),
    )
