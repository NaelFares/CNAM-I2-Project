"""Matching endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import matching_service
from backend.services.routing import routing_service

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import MatchDTO, MatchesResponse, MatchSearchRequest, MatchSearchResponse

router = APIRouter(prefix="/matches", tags=["matches"])


def _check_ladies_only_allowed(user: User, ladies_only: bool):
    """L'option est reservee aux utilisatrices : c'est un espace entre femmes,
    pas un filtre de preference ouvert a tous. Verifie cote serveur, le front
    se contentant de masquer la case."""
    if ladies_only and not user.is_woman():
        raise_api_error("MATCHES_LADIES_ONLY_FORBIDDEN", http_status=status.HTTP_403_FORBIDDEN)


@router.post("/find", response_model=MatchesResponse)
def find_matches(ladies_only: bool = False, user: User = Depends(require_current_user)):
    _check_ladies_only_allowed(user, ladies_only)

    my_rides = db.get_rides_by_user(user.id)
    all_rides = db.get_all_rides()
    matches = matching_service.find_matches(
        current_user=user, my_rides=my_rides, all_rides=all_rides, ladies_only=ladies_only
    )

    return MatchesResponse(
        matches=[MatchDTO(**match) for match in matches],
        feedback=make_feedback("MATCHES_FOUND", count=len(matches)),
    )


@router.post("/search", response_model=MatchSearchResponse)
def search_matches(body: MatchSearchRequest, user: User = Depends(require_current_user)):
    _check_ladies_only_allowed(user, body.ladies_only)

    transient_ride = Ride(
        user_id=user.id,
        event_id=0,
        ride_type=body.ride_type,
        ride_time=body.ride_time,
        start_lat=body.origin_lat,
        start_lon=body.origin_lon,
        end_lat=body.dest_lat,
        end_lon=body.dest_lon,
    )
    all_rides = db.get_all_rides()
    matches = matching_service.find_matches(
        current_user=user,
        my_rides=[transient_ride],
        all_rides=all_rides,
        ladies_only=body.ladies_only,
    )
    geometry = routing_service.get_route_geometry(
        (body.origin_lat, body.origin_lon), (body.dest_lat, body.dest_lon)
    ) or []

    return MatchSearchResponse(
        matches=[MatchDTO(**match) for match in matches],
        search_route_geometry=[list(point) for point in geometry],
        feedback=make_feedback("MATCHES_FOUND", count=len(matches)),
    )
