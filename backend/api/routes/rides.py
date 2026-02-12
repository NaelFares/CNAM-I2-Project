"""Ride generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.core.config import config
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback
from backend.api.schemas import RideDTO, RidesGenerateResponse

router = APIRouter(prefix="/rides", tags=["rides"])


@router.post("/generate", response_model=RidesGenerateResponse)
def generate_rides(user: User = Depends(require_current_user)):
    db.delete_rides_by_user(user.id)

    rides = []
    events_obj = db.get_events_by_user(user.id)
    campus_lat, campus_lon = config.get_campus_coords()

    for event in events_obj:
        ride_go = Ride(
            user_id=user.id,
            event_id=event.id,
            ride_type="to_campus",
            ride_time=event.start_time,
            start_lat=user.start_lat,
            start_lon=user.start_lon,
            end_lat=campus_lat,
            end_lon=campus_lon,
        )
        ride_go.id = db.create_ride(ride_go)
        rides.append(ride_go)

        ride_back = Ride(
            user_id=user.id,
            event_id=event.id,
            ride_type="from_campus",
            ride_time=event.end_time,
            start_lat=campus_lat,
            start_lon=campus_lon,
            end_lat=user.start_lat,
            end_lon=user.start_lon,
        )
        ride_back.id = db.create_ride(ride_back)
        rides.append(ride_back)

    return RidesGenerateResponse(
        rides=[RideDTO(**ride.to_dict()) for ride in rides],
        feedback=make_feedback("RIDES_GENERATE_SUCCESS", count=len(rides)),
    )
