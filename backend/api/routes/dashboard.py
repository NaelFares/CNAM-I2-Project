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
    rides_count = len(db.get_rides_by_user(user.id))

    # Matches are computed on demand, keep lightweight summary by default.
    return DashboardSummaryResponse(
        events_count=events_count,
        rides_count=rides_count,
        matches_count=0,
        profile_completed=bool(user.name and user.email),
    )
