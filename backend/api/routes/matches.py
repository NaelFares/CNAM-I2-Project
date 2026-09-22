"""Matching endpoints."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, status

from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import matching_service
from backend.services.routing import (
    RoutingQuotaExceededError,
    RoutingRateLimitError,
    routing_service,
)

from backend.api.deps import require_passenger
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import MatchDTO, MatchesResponse, MatchSearchRequest, MatchSearchResponse

router = APIRouter(prefix="/matches", tags=["matches"])


@router.post("/find", response_model=MatchesResponse)
def find_matches(user: User = Depends(require_passenger)):
    now = datetime.now()
    my_rides = [
        ride for ride in db.get_active_rides_by_user(user.id)
        if ride.ride_time and ride.ride_time >= now
    ]
    all_rides = [
        ride for ride in db.get_all_active_rides()
        if ride.ride_time and ride.ride_time >= now
    ]
    selection_counts = db.get_ride_selection_counts()
    selected_ride_ids = db.get_passenger_selected_ride_ids(user.id)
    reserved_times = db.get_passenger_reserved_times(user.id)
    try:
        matches = matching_service.find_matches(
            current_user=user,
            my_rides=my_rides,
            all_rides=all_rides,
            selection_counts=selection_counts,
            selected_ride_ids=selected_ride_ids,
            reserved_times=reserved_times,
        )
    except RoutingQuotaExceededError:
        raise_api_error(
            "MATCHES_ROUTING_QUOTA_EXCEEDED",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except RoutingRateLimitError:
        raise_api_error(
            "MATCHES_ROUTING_RATE_LIMITED",
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    return MatchesResponse(
        matches=[MatchDTO(**match) for match in matches],
        feedback=make_feedback("MATCHES_FOUND", count=len(matches)),
    )


@router.post("/search", response_model=MatchSearchResponse)
def search_matches(body: MatchSearchRequest, user: User = Depends(require_passenger)):
    transient_ride = Ride(
        user_id=user.id,
        event_id=None,
        ride_type=body.ride_type,
        ride_time=body.ride_time,
        start_lat=body.origin_lat,
        start_lon=body.origin_lon,
        end_lat=body.dest_lat,
        end_lon=body.dest_lon,
    )
    now = datetime.now()
    all_rides = [
        ride for ride in db.get_all_active_rides()
        if ride.ride_time and ride.ride_time >= now
    ]
    selection_counts = db.get_ride_selection_counts()
    selected_ride_ids = db.get_passenger_selected_ride_ids(user.id)
    reserved_times = db.get_passenger_reserved_times(user.id)
    try:
        matches = matching_service.find_matches(
            current_user=user,
            my_rides=[transient_ride],
            all_rides=all_rides,
            selection_counts=selection_counts,
            selected_ride_ids=selected_ride_ids,
            reserved_times=reserved_times,
        )
        geometry = routing_service.get_route_geometry(
            (body.origin_lat, body.origin_lon),
            (body.dest_lat, body.dest_lon),
        ) or []
    except RoutingQuotaExceededError:
        raise_api_error(
            "MATCHES_ROUTING_QUOTA_EXCEEDED",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except RoutingRateLimitError:
        raise_api_error(
            "MATCHES_ROUTING_RATE_LIMITED",
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

    return MatchSearchResponse(
        matches=[MatchDTO(**match) for match in matches],
        search_route_geometry=[list(point) for point in geometry],
        feedback=make_feedback("MATCHES_FOUND", count=len(matches)),
    )
