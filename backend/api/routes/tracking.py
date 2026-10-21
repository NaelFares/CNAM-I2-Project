"""Suivi d'un covoiturage, une fois la reservation acceptee.

La reservation elle-meme (demande, acceptation, annulation) releve de
`backend/api/routes/rides.py`."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from backend.database import ride_ratings as ratings_db
from backend.database import ride_selections as selections_db
from backend.database.manager import db
from backend.models.ride import Ride
from backend.models.ride_selection import RideSelection
from backend.models.user import User
from backend.services import ride_rating_rules, ride_tracking
from backend.services.photo_storage import build_photo_url

from backend.api.deps import require_current_user
from backend.api.feedback import make_feedback, raise_api_error
from backend.api.schemas import (
    RideRatingCreateRequest,
    RideRatingResponse,
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


def _to_dto(
    selection: RideSelection,
    ride: Ride,
    viewer_id: int,
    my_rating: int | None = None,
) -> RideTrackingDTO:
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
        can_rate=ride_rating_rules.can_rate_now(selection, already_rated=my_rating is not None),
        my_rating=my_rating,
    )


@router.get("", response_model=RideTrackingListResponse)
def list_trackings(user: User = Depends(require_current_user)):
    """Toutes les reservations de l'utilisateur, comme passager et conducteur."""
    selections = (
        selections_db.get_selections_for_passenger(user.id)
        + selections_db.get_selections_for_driver(user.id)
    )

    rated_ids = ratings_db.get_rated_selection_ids(user.id)

    trackings = []
    for selection in selections:
        ride = db.get_ride_by_id(selection.ride_id)
        if ride:
            # On ne relit pas chaque note : seule compte l'existence, et le
            # detail (score) n'est utile que sur l'ecran de notation.
            already = selection.id in rated_ids
            rating = ratings_db.get_rating_by_rater(selection.id, user.id) if already else None
            trackings.append(
                _to_dto(selection, ride, user.id, my_rating=rating.score if rating else None)
            )

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

    existing = ratings_db.get_rating_by_rater(selection_id, user.id)
    return RideTrackingResponse(
        tracking=_to_dto(updated, ride, user.id, my_rating=existing.score if existing else None),
        feedback=make_feedback("TRACKING_STEP_CONFIRMED"),
    )


@router.post(
    "/selections/{selection_id}/rating",
    response_model=RideRatingResponse,
    status_code=status.HTTP_201_CREATED,
)
def rate_ride(
    selection_id: int,
    payload: RideRatingCreateRequest,
    user: User = Depends(require_current_user),
):
    """Note la course, une fois celle-ci terminee des deux cotes.

    La note est definitive : une seule par personne et par course.
    """
    selection = selections_db.get_selection(selection_id)
    if not selection:
        raise_api_error("RATING_SELECTION_NOT_FOUND", http_status=status.HTTP_404_NOT_FOUND)

    ride = _get_ride(selection.ride_id)
    already = ratings_db.get_rating_by_rater(selection_id, user.id) is not None
    decision = ride_rating_rules.evaluate_rating(
        selection, user.id, ride.user_id, payload.score, already_rated=already
    )

    if not decision.allowed:
        # Un tiers recoit 404 plutot que 403 : lui repondre "interdit"
        # revelerait que cette course existe.
        http_status = (
            status.HTTP_404_NOT_FOUND
            if decision.error_code == "RATING_NOT_A_PARTICIPANT"
            else status.HTTP_400_BAD_REQUEST
            if decision.error_code == "RATING_SCORE_INVALID"
            else status.HTTP_409_CONFLICT
        )
        raise_api_error(decision.error_code, http_status=http_status)

    rating = ratings_db.create_rating(
        ride_selection_id=selection_id,
        rater_id=user.id,
        rated_id=decision.rated_id,
        score=payload.score,
        comment=payload.comment,
    )
    if rating is None:
        # Course notee entre la verification et l'insertion : la contrainte
        # unique a tranche, et la premiere note reste la bonne.
        raise_api_error("RATING_ALREADY_RATED", http_status=status.HTTP_409_CONFLICT)

    return RideRatingResponse(
        rating=rating.to_dict(),
        feedback=make_feedback("RATING_CREATED"),
    )
