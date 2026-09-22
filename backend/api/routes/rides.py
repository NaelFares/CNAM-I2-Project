"""Ride generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.core.config import config
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User

from backend.api.deps import require_current_user, require_driver, require_passenger
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import (
    DriverOfferDTO,
    DriverOffersResponse,
    PassengerSelectionDTO,
    PassengerSelectionsResponse,
    RideDTO,
    RideSelectionResponse,
    RidesGenerateResponse,
)

router = APIRouter(prefix="/rides", tags=["rides"])


def generate_rides_for_user(user: User) -> list[Ride]:
    # Un nouvel import remplace seulement les trajets en cours. Les trajets
    # archives restent disponibles dans l'historique.
    db.delete_active_rides_by_user(user.id)

    rides = []
    events_obj = db.get_events_by_user(user.id)

    # Destination = adresse école de l'utilisateur, sinon campus global de la config
    if user.has_school_location():
        dest_lat, dest_lon = user.school_lat, user.school_lon
    else:
        dest_lat, dest_lon = config.get_campus_coords()

    for event in events_obj:
        ride_go = Ride(
            user_id=user.id,
            event_id=event.id,
            ride_type="to_campus",
            ride_time=event.start_time,
            start_lat=user.start_lat,
            start_lon=user.start_lon,
            end_lat=dest_lat,
            end_lon=dest_lon,
        )
        ride_go.id = db.create_ride(ride_go)
        rides.append(ride_go)

        ride_back = Ride(
            user_id=user.id,
            event_id=event.id,
            ride_type="from_campus",
            ride_time=event.end_time,
            start_lat=dest_lat,
            start_lon=dest_lon,
            end_lat=user.start_lat,
            end_lon=user.start_lon,
        )
        ride_back.id = db.create_ride(ride_back)
        rides.append(ride_back)

    return rides


@router.post("/generate", response_model=RidesGenerateResponse)
def generate_rides(user: User = Depends(require_current_user)):
    rides = generate_rides_for_user(user)
    return RidesGenerateResponse(
        rides=[RideDTO(**ride.to_dict()) for ride in rides],
        feedback=make_feedback("RIDES_GENERATE_SUCCESS", count=len(rides)),
    )


@router.get("/my-offers", response_model=DriverOffersResponse)
def get_my_offers(user: User = Depends(require_driver)):
    rides = db.get_driver_offers(user.id, archived=False)
    return DriverOffersResponse(
        rides=[DriverOfferDTO(**ride) for ride in rides]
    )


@router.get("/my-selections", response_model=PassengerSelectionsResponse)
def get_my_selections(user: User = Depends(require_passenger)):
    rides = db.get_passenger_selections(user.id, archived=False)
    return PassengerSelectionsResponse(
        rides=[PassengerSelectionDTO(**ride) for ride in rides]
    )


@router.get("/history")
def get_ride_history(user: User = Depends(require_current_user)):
    if user.is_driver():
        rides = db.get_driver_offers(user.id, archived=True)
        return DriverOffersResponse(
            rides=[DriverOfferDTO(**ride) for ride in rides]
        )

    rides = db.get_passenger_selections(user.id, archived=True)
    return PassengerSelectionsResponse(
        rides=[PassengerSelectionDTO(**ride) for ride in rides]
    )


@router.post("/{ride_id}/select", response_model=RideSelectionResponse)
def select_ride(ride_id: int, user: User = Depends(require_passenger)):
    result = db.select_ride(ride_id, user.id)
    selection_status = result["status"]

    if selection_status == "not_found":
        raise_api_error("RIDE_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)
    if selection_status == "own_ride":
        raise_api_error("RIDE_OWN_SELECTION")
    if selection_status == "unavailable":
        raise_api_error("RIDE_UNAVAILABLE", http_status=status.HTTP_409_CONFLICT)
    if selection_status == "already_selected":
        raise_api_error("RIDE_ALREADY_SELECTED", http_status=status.HTTP_409_CONFLICT)
    if selection_status == "time_conflict":
        raise_api_error("RIDE_TIME_CONFLICT", http_status=status.HTTP_409_CONFLICT)
    if selection_status == "full":
        raise_api_error("RIDE_FULL", http_status=status.HTTP_409_CONFLICT)

    return RideSelectionResponse(
        ride_id=ride_id,
        available_seats=result["available_seats"],
        feedback=make_feedback("RIDE_SELECTION_SUCCESS"),
    )


@router.delete("/{ride_id}/select", response_model=RideSelectionResponse)
def cancel_ride_selection(ride_id: int, user: User = Depends(require_passenger)):
    result = db.cancel_ride_selection(ride_id, user.id)
    if result["status"] == "not_found":
        raise_api_error(
            "RIDE_SELECTION_NOT_FOUND",
            http_status=status.HTTP_404_NOT_FOUND,
        )

    return RideSelectionResponse(
        ride_id=ride_id,
        available_seats=result["available_seats"],
        feedback=make_feedback("RIDE_SELECTION_CANCELLED"),
    )
