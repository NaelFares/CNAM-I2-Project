"""Regles metier du suivi d'un covoiturage.

Quatre confirmations, deux par partie. Chacune n'est autorisee qu'a son
auteur legitime : le conducteur du trajet confirme la prise en charge et la
fin de course, le passager de la reservation confirme sa montee a bord et
son arrivee. Personne ne confirme a la place de l'autre -- sinon la double
confirmation n'atteste plus que les deux parties sont d'accord.

Ce module ne fait aucun acces BD et ne leve aucune HTTPException : il
repond seulement "cette action est-elle permise, et dans quelle colonne
l'ecrire". Les routes traduisent son verdict en reponse HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from backend.models.ride_selection import RideSelection

# Etapes telles que l'API les nomme.
STEP_PICKED_UP = "picked_up"      # conducteur : j'ai recupere le passager
STEP_ON_BOARD = "on_board"        # passager   : je suis dans le vehicule
STEP_COMPLETED = "completed"      # conducteur : la course est terminee
STEP_ARRIVED = "arrived"          # passager   : je suis arrive a destination

TrackingStep = Literal["picked_up", "on_board", "completed", "arrived"]

# Etape -> (colonne horodatee, role autorise a la confirmer).
_STEPS: dict[str, tuple[str, str]] = {
    STEP_PICKED_UP: ("driver_picked_up_at", "driver"),
    STEP_ON_BOARD: ("passenger_onboard_at", "passenger"),
    STEP_COMPLETED: ("driver_completed_at", "driver"),
    STEP_ARRIVED: ("passenger_arrived_at", "passenger"),
}

# Les deux etapes de fin supposent une prise en charge deja actee.
_COMPLETION_STEPS = (STEP_COMPLETED, STEP_ARRIVED)


@dataclass
class StepDecision:
    """Verdict sur une tentative de confirmation."""

    allowed: bool
    column: Optional[str] = None
    # Code du catalogue de messages, renseigne uniquement si refuse.
    error_code: Optional[str] = None


def role_of(selection: RideSelection, user_id: int, ride_owner_id: int) -> Optional[str]:
    """Role de l'utilisateur vis-a-vis de cette reservation, ou None.

    Un conducteur ne peut pas reserver son propre trajet, les deux roles
    sont donc exclusifs ; le conducteur est teste en premier par principe.
    """
    if user_id == ride_owner_id:
        return "driver"
    if user_id == selection.passenger_id:
        return "passenger"
    return None


def evaluate_step(
    selection: RideSelection,
    step: str,
    user_id: int,
    ride_owner_id: int,
) -> StepDecision:
    """Determine si `user_id` peut confirmer `step` sur cette reservation."""
    if step not in _STEPS:
        return StepDecision(False, error_code="TRACKING_STEP_UNKNOWN")

    column, required_role = _STEPS[step]
    actual_role = role_of(selection, user_id, ride_owner_id)

    # Un tiers ne doit rien apprendre de l'existence de cette reservation :
    # la route traduit ce refus en 404, pas en 403.
    if actual_role is None:
        return StepDecision(False, error_code="TRACKING_NOT_A_PARTICIPANT")

    if actual_role != required_role:
        return StepDecision(False, error_code="TRACKING_STEP_FORBIDDEN")

    if selection.is_cancelled():
        return StepDecision(False, error_code="TRACKING_SELECTION_CANCELLED")

    if step in _COMPLETION_STEPS and not selection.can_confirm_completion():
        return StepDecision(False, error_code="TRACKING_PICKUP_REQUIRED")

    return StepDecision(True, column=column)


def next_step_for(selection: RideSelection, role: str) -> Optional[str]:
    """Prochaine etape que ce role doit confirmer, ou None s'il a fini.

    Sert a piloter l'interface : un seul bouton a la fois, celui qui a du
    sens pour l'utilisateur a cet instant.
    """
    if selection.is_cancelled():
        return None

    if role == "driver":
        if selection.driver_picked_up_at is None:
            return STEP_PICKED_UP
        if selection.driver_completed_at is None:
            # La fin n'a de sens qu'une fois la prise en charge actee des
            # deux cotes : sinon on attend la confirmation du passager.
            return STEP_COMPLETED if selection.is_pickup_confirmed() else None
        return None

    if role == "passenger":
        if selection.passenger_onboard_at is None:
            return STEP_ON_BOARD
        if selection.passenger_arrived_at is None:
            return STEP_ARRIVED if selection.is_pickup_confirmed() else None
        return None

    return None
