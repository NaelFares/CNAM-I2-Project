"""Suivi d'un covoiturage, une fois la reservation acceptee.

La reservation elle-meme (demande, acceptation, annulation) releve de
`backend/api/routes/rides.py`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database import ride_selections as selections_db
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.ride_selection import RideSelection
from backend.models.user import User
from backend.services import ride_tracking
from backend.services.photo_storage import build_photo_url

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import (
    RideTrackingDTO,
    RideTrackingListResponse,
    RideTrackingResponse,
)

router = APIRouter(prefix="/tracking", tags=["tracking"])


def _get_ride(ride_id: int) -> Ride:
    ride = db.get_ride_by_id(ride_id)
    if not ride:
        raise_api_error("TRACKING_RIDE_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)
    return ride


def _to_dto(selection: RideSelection, ride: Ride, viewer_id: int) -> RideTrackingDTO:
    """Construit la vue d'une reservation pour l'un de ses participants."""
    role = ride_tracking.role_of(selection, viewer_id, ride.user_id)
    if role is None:
        # Ne jamais confirmer l'existence d'une reservation a un tiers.
        raise_api_error("TRACKING_NOT_A_PARTICIPANT", http_status=status.HTTP_404_NOT_FOUND)

    counterpart_id = selection.passenger_id if role == "driver" else ride.user_id
    counterpart = db.get_user_by_id(counterpart_id)

    return RideTrackingDTO(
        id=selection.id,
        ride_id=selection.ride_id,
        ride_time=ride.ride_time,
        ride_type=Ride.normalize_ride_type(ride.ride_type),
        my_role=role,
        counterpart_id=counterpart_id,
        # Un compte supprime ne doit pas faire planter l'ecran de suivi.
        counterpart_name=counterpart.name if counterpart else "Utilisateur inconnu",
        counterpart_photo_url=build_photo_url(counterpart.photo_filename) if counterpart else "",
        status=selection.status,
        next_step=ride_tracking.next_step_for(selection, role),
        driver_picked_up_at=selection.driver_picked_up_at,
        passenger_onboard_at=selection.passenger_onboard_at,
        driver_completed_at=selection.driver_completed_at,
        passenger_arrived_at=selection.passenger_arrived_at,
        )


@router.get("", response_model=RideTrackingListResponse)
def list_trackings(user: User = Depends(require_current_user)):
    """Toutes les reservations de l'utilisateur, comme passager et conducteur."""
    selections = (
        selections_db.get_selections_for_passenger(user.id)
        + selections_db.get_selections_for_driver(user.id)
    )

    trackings = []
    for selection in selections:
        ride = db.get_ride_by_id(selection.ride_id)
        if ride:
            trackings.append(_to_dto(selection, ride, user.id))

    # Les courses en cours d'abord, puis les plus recentes.
    trackings.sort(key=lambda t: (t.status in ("completed", "cancelled"), -t.id))
    return RideTrackingListResponse(trackings=trackings)


@router.post("/selections/{selection_id}/steps/{step}", response_model=RideTrackingResponse)
def confirm_step(step: str, selection_id: int, user: User = Depends(require_current_user)):
    """Confirme une etape du suivi, si l'utilisateur en est l'auteur legitime."""
    selection = selections_db.get_selection(selection_id)
    if not selection:
        raise_api_error("TRACKING_SELECTION_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)

    ride = _get_ride(selection.ride_id)
    decision = ride_tracking.evaluate_step(selection, step, user.id, ride.user_id)

    if not decision.allowed:
        # Un tiers recoit 404 plutot que 403 : lui repondre "interdit"
        # revelerait que cette reservation existe.
        http_status = (
            status.HTTP_404_NOT_FOUND
            if decision.error_code == "TRACKING_NOT_A_PARTICIPANT"
            else status.HTTP_409_CONFLICT
            if decision.error_code in ("TRACKING_SELECTION_CANCELLED", "TRACKING_PICKUP_REQUIRED")
            else status.HTTP_403_FORBIDDEN
        )
        raise_api_error(decision.error_code, http_status=http_status)

    updated = selections_db.confirm_step(selection_id, decision.column)
    if updated is None:
        # La reservation a ete annulee entre la lecture et l'ecriture.
        raise_api_error("TRACKING_SELECTION_CANCELLED", http_status=status.HTTP_409_CONFLICT)

    return RideTrackingResponse(
        tracking=_to_dto(updated, ride, user.id),
        feedback=make_feedback("TRACKING_STEP_CONFIRMED"),
    )
