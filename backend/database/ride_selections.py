"""Acces BD au suivi d'une reservation acceptee.

La creation, l'acceptation et l'annulation d'une reservation relevent du
flux existant (`backend/api/routes/rides.py`). Ce module ne couvre que les
quatre confirmations du suivi, qui n'ont de sens qu'une fois le passager
accepte par le conducteur.
"""

from __future__ import annotations

from typing import List, Optional

from psycopg2.extras import RealDictCursor

from backend.database.manager import db
from backend.models.ride_selection import RideSelection

# Colonnes autorisees pour une confirmation. Le nom vient d'une constante du
# code appelant, jamais d'une entree utilisateur, mais l'interpolation d'un
# nom de colonne ne pouvant pas etre parametree par psycopg2, on verifie
# explicitement l'appartenance a cette liste avant de construire la requete.
CONFIRMATION_COLUMNS = (
    "driver_picked_up_at",
    "passenger_onboard_at",
    "driver_completed_at",
    "passenger_arrived_at",
)


def get_selection(selection_id: int) -> Optional[RideSelection]:
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM ride_selections WHERE id = %s", (selection_id,))
    row = cursor.fetchone()
    conn.close()
    return RideSelection.from_dict(row) if row else None


def get_selections_for_passenger(passenger_id: int) -> List[RideSelection]:
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT * FROM ride_selections
        WHERE passenger_id = %s AND status = 'accepted'
        ORDER BY selected_at DESC
        """,
        (passenger_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [RideSelection.from_dict(row) for row in rows]


def get_selections_for_driver(driver_id: int) -> List[RideSelection]:
    """Reservations recues sur les trajets proposes par ce conducteur."""
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT s.* FROM ride_selections s
        JOIN rides r ON r.id = s.ride_id
        WHERE r.user_id = %s AND s.status = 'accepted'
        ORDER BY s.selected_at DESC
        """,
        (driver_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [RideSelection.from_dict(row) for row in rows]


def confirm_step(selection_id: int, column: str) -> Optional[RideSelection]:
    """Horodate une etape si elle ne l'est pas deja, et retourne la ligne.

    `COALESCE` rend l'operation idempotente : re-confirmer une etape ne
    deplace pas son horodatage, donc un double clic ne reecrit pas l'heure
    reelle de la prise en charge.
    """
    if column not in CONFIRMATION_COLUMNS:
        raise ValueError(f"Colonne de confirmation inconnue: {column!r}")

    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        f"""
        UPDATE ride_selections
        SET {column} = COALESCE({column}, NOW())
        WHERE id = %s AND status = 'accepted' 
        RETURNING *
        """,
        (selection_id,),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return RideSelection.from_dict(row) if row else None
