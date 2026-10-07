"""Regles metier de la notation d'une course.

Ne fait aucun acces base et ne leve aucune HTTPException : repond seulement
"cette personne peut-elle noter cette course, et qui note-t-elle". Les routes
traduisent le verdict en reponse HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.models.ride_rating import MAX_SCORE, MIN_SCORE
from backend.models.ride_selection import RideSelection
from backend.services import ride_tracking


@dataclass
class RatingDecision:
    """Verdict sur une tentative de notation."""

    allowed: bool
    # L'autre participant, qui recoit la note.
    rated_id: Optional[int] = None
    error_code: Optional[str] = None


def is_valid_score(score: int) -> bool:
    return isinstance(score, int) and MIN_SCORE <= score <= MAX_SCORE


def evaluate_rating(
    selection: RideSelection,
    user_id: int,
    ride_owner_id: int,
    score: int,
    already_rated: bool,
) -> RatingDecision:
    """Determine si `user_id` peut noter cette course.

    `already_rated` est fourni par l'appelant (une lecture base) plutot que
    deduit ici : ce module reste sans dependance a la persistance.
    """
    role = ride_tracking.role_of(selection, user_id, ride_owner_id)

    # Un tiers ne doit rien apprendre de l'existence de cette course : la
    # route traduit ce refus en 404, pas en 403.
    if role is None:
        return RatingDecision(False, error_code="RATING_NOT_A_PARTICIPANT")

    if not is_valid_score(score):
        return RatingDecision(False, error_code="RATING_SCORE_INVALID")

    # Une course annulee ou refusee n'a pas eu lieu : il n'y a rien a noter.
    if selection.is_cancelled():
        return RatingDecision(False, error_code="RATING_SELECTION_CANCELLED")

    # Le coeur de la regle : seule une course dont les deux parties ont
    # confirme la fin peut etre notee. Sans cela, on pourrait noter quelqu'un
    # avec qui on n'a jamais roule.
    if not selection.is_completed():
        return RatingDecision(False, error_code="RATING_RIDE_NOT_COMPLETED")

    # La note est definitive : une seule par personne et par course.
    if already_rated:
        return RatingDecision(False, error_code="RATING_ALREADY_RATED")

    # On note l'autre participant, jamais soi-meme.
    rated_id = selection.passenger_id if role == "driver" else ride_owner_id
    return RatingDecision(True, rated_id=rated_id)


def can_rate_now(selection: RideSelection, already_rated: bool) -> bool:
    """Indique a l'interface s'il faut proposer le formulaire de notation."""
    return selection.is_completed() and not selection.is_cancelled() and not already_rated
