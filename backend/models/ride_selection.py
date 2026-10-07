"""Reservation d'un trajet par un passager, et suivi du covoiturage.

Le suivi repose sur quatre confirmations independantes, chacune horodatee :

  1. le conducteur confirme avoir recupere le passager,
  2. le passager confirme etre monte dans le vehicule,
  3. le conducteur confirme la fin de la course,
  4. le passager confirme etre arrive a destination.

On stocke un instant plutot qu'un booleen pour savoir quand chaque partie a
confirme. Aucun statut n'est persiste : l'etat se deduit des horodatages
(cf. `status`), ce qui evite qu'un champ redondant se desynchronise.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Etapes exposees a l'API, de la plus avancee a la moins avancee.
STATUS_CANCELLED = "cancelled"
STATUS_COMPLETED = "completed"          # les deux parties ont confirme la fin
STATUS_ARRIVING = "arriving"            # une seule des deux l'a confirmee
STATUS_ON_BOARD = "on_board"            # les deux ont confirme la prise en charge
STATUS_PICKING_UP = "picking_up"        # une seule des deux l'a confirmee
STATUS_PENDING = "pending"              # reservee, rien de confirme


@dataclass
class RideSelection:
    """Un passager ayant reserve une place sur un trajet."""

    id: Optional[int] = None
    ride_id: int = 0
    passenger_id: int = 0
    selected_at: Optional[datetime] = None

    driver_picked_up_at: Optional[datetime] = None
    passenger_onboard_at: Optional[datetime] = None
    driver_completed_at: Optional[datetime] = None
    passenger_arrived_at: Optional[datetime] = None

    # Statut de la reservation, porte par le flux conducteur/passager :
    # pending (demande envoyee), accepted (conducteur a valide), rejected
    # (refuse ou annule). Le suivi ci-dessous ne concerne que les 'accepted'.
    selection_status: str = "pending"

    # --- Etat derive ---

    def is_cancelled(self) -> bool:
        """Reservation refusee par le conducteur ou annulee par le passager."""
        return self.selection_status == "rejected"

    def is_accepted(self) -> bool:
        """Seule une reservation acceptee peut faire l'objet d'un suivi."""
        return self.selection_status == "accepted"

    def is_pickup_confirmed(self) -> bool:
        """Prise en charge actee : les deux parties l'ont confirmee.

        Une seule confirmation ne suffit pas -- c'est tout l'interet de la
        double confirmation : le conducteur peut se tromper de personne, et
        le passager peut monter dans la mauvaise voiture.
        """
        return self.driver_picked_up_at is not None and self.passenger_onboard_at is not None

    def is_completed(self) -> bool:
        """Course terminee : conducteur et passager l'ont tous deux confirme."""
        return self.driver_completed_at is not None and self.passenger_arrived_at is not None

    @property
    def status(self) -> str:
        """Etat courant, deduit des horodatages (jamais stocke)."""
        if self.is_cancelled():
            return STATUS_CANCELLED
        if not self.is_accepted():
            # Demande encore en attente de la reponse du conducteur : aucune
            # etape de suivi n'a de sens avant son acceptation.
            return STATUS_PENDING
        if self.is_completed():
            return STATUS_COMPLETED
        if self.driver_completed_at or self.passenger_arrived_at:
            return STATUS_ARRIVING
        if self.is_pickup_confirmed():
            return STATUS_ON_BOARD
        if self.driver_picked_up_at or self.passenger_onboard_at:
            return STATUS_PICKING_UP
        return STATUS_PENDING

    def can_confirm_completion(self) -> bool:
        """La fin de course ne se confirme qu'apres une prise en charge actee.

        Sans cette regle, une course pourrait etre marquee terminee sans que
        personne ne soit jamais monte dans la voiture -- et alimenter ensuite
        un compteur de courses ou une note.
        """
        return self.is_pickup_confirmed() and self.is_accepted()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ride_id": self.ride_id,
            "passenger_id": self.passenger_id,
            "selected_at": self.selected_at,
            "driver_picked_up_at": self.driver_picked_up_at,
            "passenger_onboard_at": self.passenger_onboard_at,
            "driver_completed_at": self.driver_completed_at,
            "passenger_arrived_at": self.passenger_arrived_at,
            "selection_status": self.selection_status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RideSelection":
        return cls(
            id=data.get("id"),
            ride_id=data.get("ride_id", 0),
            passenger_id=data.get("passenger_id", 0),
            selected_at=data.get("selected_at"),
            driver_picked_up_at=data.get("driver_picked_up_at"),
            passenger_onboard_at=data.get("passenger_onboard_at"),
            driver_completed_at=data.get("driver_completed_at"),
            passenger_arrived_at=data.get("passenger_arrived_at"),
            selection_status=data.get("status") or "pending",
        )
