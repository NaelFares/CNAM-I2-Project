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


def count_completed_rides(user_id: int) -> dict:
    """Nombre de courses terminees par cet utilisateur, par role.

    Une course compte quand les deux parties ont confirme la fin : c'est le
    seul etat incontestable, et il ne peut pas etre gonfle unilateralement.

    Retourne {"driver": n, "passenger": n}. Les deux roles sont comptes
    separement, un utilisateur pouvant changer de role au fil du temps.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) FILTER (WHERE r.user_id = %s) AS as_driver,
            COUNT(*) FILTER (WHERE s.passenger_id = %s) AS as_passenger
        FROM ride_selections s
        JOIN rides r ON r.id = s.ride_id
        WHERE s.status = 'accepted'
          AND s.driver_completed_at IS NOT NULL
          AND s.passenger_arrived_at IS NOT NULL
          AND (r.user_id = %s OR s.passenger_id = %s)
        """,
        (user_id, user_id, user_id, user_id),
    )
    row = cursor.fetchone()
    conn.close()
    return {"driver": int(row[0] or 0), "passenger": int(row[1] or 0)}


def count_completed_rides_as_driver(user_ids: List[int]) -> dict:
    """Courses terminees comme conducteur, pour plusieurs utilisateurs.

    Requete groupee : afficher le palier sur une liste de resultats ne doit
    pas declencher une lecture par ligne.
    """
    if not user_ids:
        return {}
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT r.user_id, COUNT(*)
        FROM ride_selections s
        JOIN rides r ON r.id = s.ride_id
        WHERE s.status = 'accepted'
          AND s.driver_completed_at IS NOT NULL
          AND s.passenger_arrived_at IS NOT NULL
          AND r.user_id = ANY(%s)
        GROUP BY r.user_id
        """,
        (list(user_ids),),
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0]: int(row[1]) for row in rows}
