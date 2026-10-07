"""Acces base aux notes de course et aux moyennes."""

from __future__ import annotations

from typing import Dict, List, Optional

from psycopg2.extras import RealDictCursor

from backend.database.manager import db
from backend.models.ride_rating import MAX_COMMENT_LENGTH, RatingSummary, RideRating


def create_rating(
    ride_selection_id: int,
    rater_id: int,
    rated_id: int,
    score: int,
    comment: str = "",
) -> Optional[RideRating]:
    """Enregistre une note. Retourne None si elle existe deja.

    `ON CONFLICT DO NOTHING` s'appuie sur la contrainte unique
    (ride_selection_id, rater_id) : deux envois simultanes ne creent pas
    deux notes, et la premiere reste la bonne puisqu'elle est definitive.
    """
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        INSERT INTO ride_ratings (ride_selection_id, rater_id, rated_id, score, comment)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (ride_selection_id, rater_id) DO NOTHING
        RETURNING *
        """,
        (ride_selection_id, rater_id, rated_id, score, (comment or "").strip()[:MAX_COMMENT_LENGTH]),
    )
    row = cursor.fetchone()
    conn.commit()
    conn.close()
    return RideRating.from_dict(row) if row else None


def get_rating_by_rater(ride_selection_id: int, rater_id: int) -> Optional[RideRating]:
    """Note deja donnee par cet utilisateur sur cette course, le cas echeant."""
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        "SELECT * FROM ride_ratings WHERE ride_selection_id = %s AND rater_id = %s",
        (ride_selection_id, rater_id),
    )
    row = cursor.fetchone()
    conn.close()
    return RideRating.from_dict(row) if row else None


def get_rated_selection_ids(rater_id: int) -> set:
    """Courses deja notees par cet utilisateur.

    Charge en une requete plutot qu'une par course : la liste de suivi doit
    savoir, pour chaque ligne, s'il reste une note a donner.
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ride_selection_id FROM ride_ratings WHERE rater_id = %s",
        (rater_id,),
    )
    rows = cursor.fetchall()
    conn.close()
    return {row[0] for row in rows}


def get_summary(user_id: int) -> RatingSummary:
    """Moyenne et nombre de notes recues par un utilisateur."""
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT AVG(score)::float AS average, COUNT(*) AS count
        FROM ride_ratings WHERE rated_id = %s
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    conn.close()
    return RatingSummary.from_dict(row or {})


def get_summaries(user_ids: List[int]) -> Dict[int, RatingSummary]:
    """Moyennes de plusieurs utilisateurs en une requete.

    Evite le N+1 quand on affiche la reputation sur une liste de resultats.
    """
    if not user_ids:
        return {}
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT rated_id, AVG(score)::float AS average, COUNT(*) AS count
        FROM ride_ratings WHERE rated_id = ANY(%s)
        GROUP BY rated_id
        """,
        (list(user_ids),),
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["rated_id"]: RatingSummary.from_dict(row) for row in rows}


def get_received_ratings(user_id: int, limit: int = 20) -> List[RideRating]:
    """Dernieres notes recues, pour les afficher sur un profil."""
    conn = db.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(
        """
        SELECT * FROM ride_ratings
        WHERE rated_id = %s
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    conn.close()
    return [RideRating.from_dict(row) for row in rows]
