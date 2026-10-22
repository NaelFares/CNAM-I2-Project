"""Résumé du tableau de bord."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.database.manager import db
from backend.models.user import User

from backend.api.deps import require_current_user
from backend.api.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(user: User = Depends(require_current_user)):
    events_count = len(db.get_events_by_user(user.id))
    rides_count = len(db.get_active_rides_by_user(user.id))

    # Covoiturages confirmes, des deux cotes : passagers acceptes sur mes
    # trajets proposes, et places obtenues chez d'autres conducteurs.
    as_driver = sum(
        offer["occupied_seats"]
        for offer in db.get_driver_offers(user.id)
        if offer["is_offer"]
    )
    as_passenger = sum(
        ride["selection_status"] == "accepted"
        for ride in db.get_passenger_selections(user.id)
    )
    matches_count = as_driver + as_passenger

    return DashboardSummaryResponse(
        events_count=events_count,
        rides_count=rides_count,
        matches_count=matches_count,
        profile_completed=bool(user.name and user.email),
    )
