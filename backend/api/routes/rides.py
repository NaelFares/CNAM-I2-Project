"""Ride generation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.core.config import config
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.user import User
from backend.services.matching import MatchingService

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import (
    DriverOfferDTO,
    DriverOffersResponse,
    PassengerSelectionDTO,
    PassengerSelectionsResponse,
    OfferCreateRequest,
    OfferCreateResponse,
    RideDTO,
    RideOfferRequest,
    RideSelectRequest,
    RideOfferResponse,
    RideSelectionResponse,
    RidesGenerateResponse,
)

router = APIRouter(prefix="/rides", tags=["rides"])


def generate_rides_for_user(user: User) -> list[Ride]:
    # Un nouvel import remplace seulement les trajets en cours. Les trajets
    # archives restent disponibles dans l'historique.
    # Le choix "je prends ma voiture" est memorise par cours et par sens,
    # pour survivre a la regeneration des trajets.
    offered = {
        (ride.event_id, ride.ride_type)
        for ride in db.get_active_rides_by_user(user.id)
        if ride.is_offer
    }
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
            is_offer=(event.id, "to_campus") in offered,
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
            is_offer=(event.id, "from_campus") in offered,
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
def get_my_offers(user: User = Depends(require_current_user)):
    rides = db.get_driver_offers(user.id, archived=False)
    return DriverOffersResponse(
        rides=[DriverOfferDTO(**ride) for ride in rides]
    )


@router.get("/my-selections", response_model=PassengerSelectionsResponse)
def get_my_selections(user: User = Depends(require_current_user)):
    rides = db.get_passenger_selections(user.id, archived=False)
    return PassengerSelectionsResponse(
        rides=[PassengerSelectionDTO(**ride) for ride in rides]
    )


@router.get("/history")
def get_ride_history(user: User = Depends(require_current_user)):
    """Trajets passes, des deux cotes : proposes et reserves."""
    return {
        "offers": [
            DriverOfferDTO(**ride)
            for ride in db.get_driver_offers(user.id, archived=True)
            if ride["is_offer"]
        ],
        "selections": [
            PassengerSelectionDTO(**ride)
            for ride in db.get_passenger_selections(user.id, archived=True)
        ],
    }


@router.post("/offers", response_model=OfferCreateResponse, status_code=status.HTTP_201_CREATED)
def create_offer(payload: OfferCreateRequest, user: User = Depends(require_current_user)):
    """Proposer un trajet independamment de l'emploi du temps."""
    # Comparaison a ~100 m pres : au-dela de la precision d'une adresse saisie.
    if (
        abs(payload.start_lat - payload.end_lat) < 0.001
        and abs(payload.start_lon - payload.end_lon) < 0.001
    ):
        raise_api_error("RIDE_OFFER_SAME_PLACE")

    result = db.create_offer(Ride(
        user_id=user.id,
        event_id=None,
        ride_type=payload.ride_type,
        # Heure arrondie a la minute : c'est l'unite des controles de conflit.
        ride_time=payload.ride_time.replace(second=0, microsecond=0, tzinfo=None),
        start_lat=payload.start_lat,
        start_lon=payload.start_lon,
        end_lat=payload.end_lat,
        end_lon=payload.end_lon,
        is_offer=True,
        start_address=payload.start_address.strip(),
        end_address=payload.end_address.strip(),
    ))
    outcome = result["status"]
    if outcome == "no_car":
        raise_api_error("RIDE_OFFER_NO_CAR", http_status=status.HTTP_409_CONFLICT)
    if outcome == "past":
        raise_api_error("RIDE_OFFER_PAST")
    if outcome == "time_conflict":
        raise_api_error("RIDE_OFFER_SAME_TIME", http_status=status.HTTP_409_CONFLICT)

    return OfferCreateResponse(ride_id=result["ride_id"], feedback=make_feedback("RIDE_OFFER_CREATED"))


@router.delete("/{ride_id}/offer", response_model=RideOfferResponse)
def withdraw_offer(ride_id: int, user: User = Depends(require_current_user)):
    """Annuler un trajet propose (supprime s'il a ete cree a la main)."""
    result = db.withdraw_offer(ride_id, user.id)
    if result["status"] == "not_found":
        raise_api_error("RIDE_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)
    if result["status"] == "has_passengers":
        raise_api_error("RIDE_OFFER_HAS_PASSENGERS", http_status=status.HTTP_409_CONFLICT)
    return RideOfferResponse(
        ride_id=ride_id,
        is_offer=False,
        feedback=make_feedback("RIDE_OFFER_WITHDRAWN"),
    )


@router.put("/{ride_id}/offer", response_model=RideOfferResponse)
def set_ride_offer(ride_id: int, payload: RideOfferRequest, user: User = Depends(require_current_user)):
    """Interrupteur "Je prends ma voiture" sur un trajet de l'utilisateur."""
    result = db.set_ride_offer(ride_id, user.id, payload.is_offer)
    outcome = result["status"]

    if outcome == "not_found":
        raise_api_error("RIDE_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)
    if outcome == "unavailable":
        raise_api_error("RIDE_OFFER_UNAVAILABLE", http_status=status.HTTP_409_CONFLICT)
    if outcome == "no_car":
        raise_api_error("RIDE_OFFER_NO_CAR", http_status=status.HTTP_409_CONFLICT)
    if outcome == "time_conflict":
        raise_api_error("RIDE_OFFER_TIME_CONFLICT", http_status=status.HTTP_409_CONFLICT)
    if outcome == "has_passengers":
        raise_api_error("RIDE_OFFER_HAS_PASSENGERS", http_status=status.HTTP_409_CONFLICT)

    return RideOfferResponse(
        ride_id=ride_id,
        is_offer=payload.is_offer,
        feedback=make_feedback("RIDE_OFFER_ENABLED" if payload.is_offer else "RIDE_OFFER_DISABLED"),
    )


@router.post("/{ride_id}/select", response_model=RideSelectionResponse)
def select_ride(
    ride_id: int,
    body: RideSelectRequest | None = None,
    user: User = Depends(require_current_user),
):
    # Le corps est facultatif : les anciens clients reservent sans detail.
    result = db.select_ride(ride_id, user.id, body.model_dump() if body else None)
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


@router.post("/{ride_id}/passengers/{passenger_id}/accept", response_model=RideSelectionResponse)
def accept_passenger(
    ride_id: int,
    passenger_id: int,
    force: bool = False,
    user: User = Depends(require_current_user),
):
    # force=true : le conducteur a vu l'avertissement de detour et accepte quand meme.
    return _decide_passenger(ride_id, passenger_id, user.id, "accept", force=force)


@router.post("/{ride_id}/passengers/{passenger_id}/reject", response_model=RideSelectionResponse)
def reject_passenger(ride_id: int, passenger_id: int, user: User = Depends(require_current_user)):
    return _decide_passenger(ride_id, passenger_id, user.id, "reject")


def _decide_passenger(ride_id: int, passenger_id: int, driver_id: int, decision: str, force: bool = False):
    # Le detour total n'est connu qu'ici : les demandes en attente ont ete
    # calculees chacune seule, le conducteur choisit qui il accepte. C'est un
    # avertissement, pas une interdiction : il peut confirmer avec force=true.
    if decision == "accept" and not force:
        ride = db.get_ride_by_id(ride_id)
        stop = db.get_selection_stop(ride_id, passenger_id)
        if ride and ride.user_id == driver_id and stop:
            accepted = db.get_accepted_stops([ride_id]).get(ride_id, [])
            if MatchingService.accept_exceeds_total_detour(ride, stop, accepted):
                raise_api_error("RIDE_DETOUR_TOO_LONG", http_status=status.HTTP_409_CONFLICT)
    result = db.decide_ride_selection(ride_id, passenger_id, driver_id, decision)
    if result["status"] == "not_found":
        raise_api_error("RIDE_SELECTION_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)
    if result["status"] == "unavailable":
        raise_api_error("RIDE_UNAVAILABLE", http_status=status.HTTP_409_CONFLICT)
    if result["status"] == "already_decided":
        raise_api_error("RIDE_SELECTION_ALREADY_DECIDED", http_status=status.HTTP_409_CONFLICT)
    if result["status"] == "full":
        raise_api_error("RIDE_FULL", http_status=status.HTTP_409_CONFLICT)
    if result["status"] == "time_conflict":
        raise_api_error("RIDE_TIME_CONFLICT", http_status=status.HTTP_409_CONFLICT)
    return RideSelectionResponse(
        ride_id=ride_id,
        available_seats=result["available_seats"],
        feedback=make_feedback(
            "RIDE_SELECTION_ACCEPTED" if decision == "accept" else "RIDE_SELECTION_REJECTED"
        ),
    )


@router.delete("/{ride_id}/select", response_model=RideSelectionResponse)
def cancel_ride_selection(ride_id: int, user: User = Depends(require_current_user)):
    result = db.cancel_ride_selection(ride_id, user.id)
    if result["status"] == "not_found":
        raise_api_error(
            "RIDE_SELECTION_NOT_FOUND",
            http_status=status.HTTP_404_NOT_FOUND,
        )
    if result["status"] == "already_started":
        raise_api_error("TRACKING_CANCEL_TOO_LATE", http_status=status.HTTP_409_CONFLICT)

    return RideSelectionResponse(
        ride_id=ride_id,
        available_seats=result["available_seats"],
        feedback=make_feedback("RIDE_SELECTION_CANCELLED"),
    )
