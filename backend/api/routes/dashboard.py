"""Dashboard summary endpoints."""

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

    if user.is_driver():
        matches_count = sum(
            offer["occupied_seats"] for offer in db.get_driver_offers(user.id)
        )
    else:
        matches_count = len(db.get_passenger_selections(user.id))

    return DashboardSummaryResponse(
        events_count=events_count,
        rides_count=rides_count,
        matches_count=matches_count,
        profile_completed=bool(user.name and user.email),
    )
