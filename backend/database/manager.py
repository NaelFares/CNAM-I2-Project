"""Service de gestion de la base de données PostgreSQL – opérations CRUD."""
import time
from typing import List, Optional

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import Json, RealDictCursor

from backend.core.config import config
from backend.models.user import User
from backend.models.event import Event
from backend.models.ride import Ride
from backend.core.geo import haversine_distance


def _apart(lat, lon, ref_lat, ref_lon, same_place_km: float = 0.3):
    """Vrai si le point (lat, lon) est distinct du point de reference (plus
    de 300 m, meme seuil que le matching) ; None si le point est inconnu."""
    if lat is None or lon is None:
        return None
    return haversine_distance(lat, lon, ref_lat, ref_lon) > same_place_km


class Database:
    def __init__(self):
        self.db_url = config.DATABASE_URL

    def get_connection(self) -> psycopg2.extensions.connection:
        for attempt in range(10):
            try:
                conn = psycopg2.connect(self.db_url, connect_timeout=5)
                conn.autocommit = False
                return conn
            except OperationalError:
                if attempt == 9:
                    raise
                time.sleep(2)
        raise OperationalError("Impossible de se connecter à la base de données")

    # Utilisateurs
    """Crée un nouvel utilisateur"""

    def create_user(self, user: User) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, hashed_password, car_seats,
                               gender, photo_filename, music_preference, music_genres,
                               smoking_preference,
                               start_address, start_lat, start_lon, time_tolerance_min,
                               school_address, school_lat, school_lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user.name,
                user.email,
                user.hashed_password,
                user.car_seats,
                user.gender,
                user.photo_filename,
                user.music_preference,
                list(user.music_genres),
                user.smoking_preference,
                user.start_address,
                user.start_lat,
                user.start_lon,
                user.time_tolerance_min,
                user.school_address,
                user.school_lat,
                user.school_lon,
            ),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return user_id

    def get_user_by_email(self, email: str) -> Optional[User]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User.from_dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User.from_dict(row)
        return None

    def get_all_users(self) -> List[User]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        conn.close()
        return [User.from_dict(row) for row in rows]

    def delete_user(self, user_id: int):
        """Supprime un utilisateur (les events/rides liés doivent être supprimés avant, pas de cascade en BD)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        conn.close()

    def update_user(self, user: User):
        """Met à jour un utilisateur.

        `photo_filename` est volontairement exclu : la photo se change par son
        propre endpoint, et l'inclure ici ferait effacer la photo à chaque
        sauvegarde du formulaire de profil, qui ne la transporte pas.
        Voir `update_user_photo`.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s, car_seats = %s,
                gender = %s, music_preference = %s, music_genres = %s, smoking_preference = %s,
                start_address = %s, start_lat = %s, start_lon = %s,
                time_tolerance_min = %s, school_address = %s, school_lat = %s, school_lon = %s
            WHERE id = %s
            """,
            (
                user.name,
                user.email,
                user.car_seats,
                user.gender,
                user.music_preference,
                list(user.music_genres),
                user.smoking_preference,
                user.start_address,
                user.start_lat,
                user.start_lon,
                user.time_tolerance_min,
                user.school_address,
                user.school_lat,
                user.school_lon,
                user.id,
            ),
        )
        conn.commit()
        conn.close()

    def update_user_photo(self, user_id: int, photo_filename: str):
        """Met à jour la seule photo de profil (chaîne vide = suppression)."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET photo_filename = %s WHERE id = %s",
            (photo_filename, user_id),
        )
        conn.commit()
        conn.close()

    # Cours
    def create_event(self, event: Event) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO events (user_id, title, start_time, end_time, location, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                event.user_id,
                event.title,
                event.start_time,
                event.end_time,
                event.location,
                event.description,
            ),
        )
        event_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return event_id

    def get_events_by_user(self, user_id: int) -> List[Event]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM events WHERE user_id = %s ORDER BY start_time", (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Event.from_dict(row) for row in rows]

    def delete_events_by_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    # Trajets
    def create_ride(self, ride: Ride) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rides (user_id, event_id, ride_type, ride_time, start_lat, start_lon, end_lat, end_lon,
                               status, archived_at, is_offer, start_address, end_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                ride.user_id,
                ride.event_id,
                ride.ride_type,
                ride.ride_time,
                ride.start_lat,
                ride.start_lon,
                ride.end_lat,
                ride.end_lon,
                ride.status,
                ride.archived_at,
                ride.is_offer,
                ride.start_address,
                ride.end_address,
            ),
        )
        ride_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return ride_id

    def get_rides_by_user(self, user_id: int) -> List[Ride]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM rides WHERE user_id = %s ORDER BY ride_time", (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Ride.from_dict(row) for row in rows]

    def get_ride_by_id(self, ride_id: int) -> Optional[Ride]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM rides WHERE id = %s", (ride_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return Ride.from_dict(row)
        return None

    def get_active_rides_by_user(self, user_id: int) -> List[Ride]:
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT * FROM rides
            WHERE user_id = %s AND status = 'active'
            ORDER BY ride_time
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [Ride.from_dict(row) for row in rows]

    def get_all_rides(self) -> List[Ride]:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM rides ORDER BY ride_time")
        rows = cursor.fetchall()
        conn.close()
        return [Ride.from_dict(row) for row in rows]

    def get_all_active_rides(self) -> List[Ride]:
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM rides WHERE status = 'active' ORDER BY ride_time")
        rows = cursor.fetchall()
        conn.close()
        return [Ride.from_dict(row) for row in rows]

    def delete_rides_by_user(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rides WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    def delete_active_rides_by_user(self, user_id: int):
        """Supprime les trajets en cours issus du planning, avant leur regeneration.

        Les trajets crees a la main (event_id NULL) sont epargnes : ils ne
        dependent pas de l'emploi du temps, et les supprimer effacerait en
        cascade les reservations de leurs passagers. L'historique (archive)
        est preserve.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM rides WHERE user_id = %s AND status = 'active' AND event_id IS NOT NULL",
            (user_id,),
        )
        conn.commit()
        conn.close()

    def archive_expired_rides(self) -> int:
        """Archive les trajets termines depuis au moins trois heures."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE rides
            SET status = 'archived', archived_at = NOW()
            WHERE status = 'active'
              AND ride_time < LOCALTIMESTAMP - INTERVAL '3 hours'
            """
        )
        count = cursor.rowcount
        conn.commit()
        conn.close()
        return count

    # Réservations
    def get_ride_selection_counts(self) -> dict[int, int]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ride_id, COUNT(*)
            FROM ride_selections
            WHERE status = 'accepted'
            GROUP BY ride_id
            """
        )
        counts = {int(ride_id): int(count) for ride_id, count in cursor.fetchall()}
        conn.close()
        return counts

    def get_ride_request_counts(self) -> dict[int, int]:
        """Nombre de demandes en attente ou acceptées, pour le seed de démonstration."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT ride_id, COUNT(*) FROM ride_selections
            WHERE status IN ('pending', 'accepted')
            GROUP BY ride_id
            """
        )
        counts = {int(ride_id): int(count) for ride_id, count in cursor.fetchall()}
        conn.close()
        return counts

    def get_passenger_selected_ride_ids(self, passenger_id: int) -> set[int]:
        """Retourne les trajets actifs déjà demandés par un passager, même refusés."""
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT rs.ride_id
            FROM ride_selections rs
            JOIN rides r ON r.id = rs.ride_id
            WHERE rs.passenger_id = %s AND r.status = 'active'
            """,
            (passenger_id,),
        )
        ride_ids = {int(row[0]) for row in cursor.fetchall()}
        conn.close()
        return ride_ids

    def get_passenger_reserved_times(self, passenger_id: int) -> set:
        """Créneaux déjà réservés, à la minute affichée dans l'application."""
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT date_trunc('minute', r.ride_time)
            FROM ride_selections rs
            JOIN rides r ON r.id = rs.ride_id
            WHERE rs.passenger_id = %s AND r.status = 'active'
              AND rs.status IN ('pending', 'accepted')
            """,
            (passenger_id,),
        )
        reserved_times = {row[0] for row in cursor.fetchall()}
        conn.close()
        return reserved_times

    def get_offer_times(self, user_id: int) -> set:
        """Creneaux ou l'utilisateur propose deja sa voiture, a la minute.

        Pendant de get_passenger_reserved_times : sur ces creneaux, il ne peut
        pas chercher de place chez quelqu'un d'autre.
        """
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT date_trunc('minute', ride_time)
            FROM rides
            WHERE user_id = %s AND is_offer AND status = 'active'
            """,
            (user_id,),
        )
        times = {row[0] for row in cursor.fetchall()}
        conn.close()
        return times

    def count_active_offers(self, user_id: int) -> int:
        """Trajets actuellement proposes par l'utilisateur."""
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM rides WHERE user_id = %s AND is_offer AND status = 'active'",
            (user_id,),
        )
        value = int(cursor.fetchone()[0])
        conn.close()
        return value

    def create_offer(self, ride: Ride) -> dict:
        """Cree un trajet propose a la main, hors emploi du temps.

        Verdicts : created (avec ride_id), no_car, past (heure deja passee),
        time_conflict (l'utilisateur a deja, a la meme minute, une demande
        comme passager ou un autre trajet propose : on ne conduit pas deux
        voitures a la fois).
        """
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Meme ordre de verrouillage que select_ride et set_ride_offer.
            cursor.execute("SELECT id, car_seats FROM users WHERE id = %s FOR UPDATE", (ride.user_id,))
            owner = cursor.fetchone()
            if not owner or not owner["car_seats"]:
                return {"status": "no_car"}

            cursor.execute("SELECT %s::timestamp <= LOCALTIMESTAMP AS is_past", (ride.ride_time,))
            if cursor.fetchone()["is_past"]:
                return {"status": "past"}

            cursor.execute(
                """
                SELECT 1 FROM rides
                WHERE user_id = %s AND is_offer AND status = 'active'
                  AND date_trunc('minute', ride_time) = date_trunc('minute', %s::timestamp)
                UNION ALL
                SELECT 1
                FROM ride_selections rs
                JOIN rides reserved ON reserved.id = rs.ride_id
                WHERE rs.passenger_id = %s
                  AND reserved.status = 'active'
                  AND rs.status IN ('pending', 'accepted')
                  AND date_trunc('minute', reserved.ride_time) = date_trunc('minute', %s::timestamp)
                LIMIT 1
                """,
                (ride.user_id, ride.ride_time, ride.user_id, ride.ride_time),
            )
            if cursor.fetchone():
                return {"status": "time_conflict"}

            cursor.execute(
                """
                INSERT INTO rides (user_id, event_id, ride_type, ride_time,
                                   start_lat, start_lon, end_lat, end_lon,
                                   status, is_offer, start_address, end_address)
                VALUES (%s, NULL, %s, %s, %s, %s, %s, %s, 'active', TRUE, %s, %s)
                RETURNING id
                """,
                (
                    ride.user_id, ride.ride_type, ride.ride_time,
                    ride.start_lat, ride.start_lon, ride.end_lat, ride.end_lon,
                    ride.start_address, ride.end_address,
                ),
            )
            ride_id = cursor.fetchone()["id"]
            conn.commit()
            return {"status": "created", "ride_id": ride_id}
        finally:
            conn.close()

    def withdraw_offer(self, ride_id: int, user_id: int) -> dict:
        """Retire un trajet propose ("Annuler ce trajet").

        Un trajet cree a la main est supprime ; un trajet de l'emploi du temps
        redevient une simple recherche. Refuse tant qu'il a des demandes en
        attente ou des passagers acceptes : il faut d'abord les refuser, pour
        que personne ne decouvre trop tard qu'il n'a plus de voiture.

        Verdicts : withdrawn, not_found, has_passengers.
        """
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cursor.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (user_id,))
            cursor.fetchone()
            cursor.execute(
                """
                SELECT id, event_id FROM rides
                WHERE id = %s AND user_id = %s AND is_offer AND status = 'active'
                FOR UPDATE
                """,
                (ride_id, user_id),
            )
            ride = cursor.fetchone()
            if not ride:
                return {"status": "not_found"}

            cursor.execute(
                """
                SELECT 1 FROM ride_selections
                WHERE ride_id = %s AND status IN ('pending', 'accepted')
                LIMIT 1
                """,
                (ride_id,),
            )
            if cursor.fetchone():
                return {"status": "has_passengers"}

            if ride["event_id"] is None:
                cursor.execute("DELETE FROM rides WHERE id = %s", (ride_id,))
            else:
                cursor.execute("UPDATE rides SET is_offer = FALSE WHERE id = %s", (ride_id,))
            conn.commit()
            return {"status": "withdrawn"}
        finally:
            conn.close()

    def set_ride_offer(self, ride_id: int, user_id: int, is_offer: bool) -> dict:
        """Bascule un trajet entre offre (je prends ma voiture) et recherche.

        Verdicts : updated, not_found, unavailable, no_car (pas de places
        renseignees), time_conflict (une reservation comme passager sur le
        meme creneau), has_passengers (impossible de retirer une offre qui a
        des demandes en cours ou des passagers acceptes).
        """
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Meme ordre de verrouillage que select_ride : le compte d'abord.
            # Sans cela, proposer ce trajet et reserver une place au meme
            # creneau dans un autre onglet pourraient passer tous les deux.
            cursor.execute("SELECT id, car_seats FROM users WHERE id = %s FOR UPDATE", (user_id,))
            owner = cursor.fetchone()
            cursor.execute(
                """
                SELECT id, status, ride_time, is_offer,
                       ride_time <= LOCALTIMESTAMP AS is_past
                FROM rides
                WHERE id = %s AND user_id = %s
                FOR UPDATE
                """,
                (ride_id, user_id),
            )
            ride = cursor.fetchone()
            if not ride or not owner:
                return {"status": "not_found"}
            if ride["status"] != "active" or ride["is_past"]:
                return {"status": "unavailable"}
            if bool(ride["is_offer"]) == bool(is_offer):
                return {"status": "updated"}

            if is_offer:
                if not owner["car_seats"]:
                    return {"status": "no_car"}
                cursor.execute(
                    """
                    SELECT 1
                    FROM ride_selections rs
                    JOIN rides reserved ON reserved.id = rs.ride_id
                    WHERE rs.passenger_id = %s
                      AND reserved.status = 'active'
                      AND rs.status IN ('pending', 'accepted')
                      AND date_trunc('minute', reserved.ride_time) = date_trunc('minute', %s::timestamp)
                    LIMIT 1
                    """,
                    (user_id, ride["ride_time"]),
                )
                if cursor.fetchone():
                    return {"status": "time_conflict"}
            else:
                cursor.execute(
                    """
                    SELECT 1 FROM ride_selections
                    WHERE ride_id = %s AND status IN ('pending', 'accepted')
                    LIMIT 1
                    """,
                    (ride_id,),
                )
                if cursor.fetchone():
                    return {"status": "has_passengers"}

            cursor.execute("UPDATE rides SET is_offer = %s WHERE id = %s", (bool(is_offer), ride_id))
            conn.commit()
            return {"status": "updated"}
        finally:
            conn.close()

    def get_max_active_occupancy_for_driver(self, user_id: int) -> int:
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(MAX(occupied), 0)
            FROM (
                SELECT r.id, COUNT(rs.id) AS occupied
                FROM rides r
                LEFT JOIN ride_selections rs ON rs.ride_id = r.id AND rs.status = 'accepted'
                WHERE r.user_id = %s AND r.status = 'active'
                GROUP BY r.id
            ) AS active_occupancy
            """,
            (user_id,),
        )
        value = int(cursor.fetchone()[0])
        conn.close()
        return value

    def select_ride(self, ride_id: int, passenger_id: int, stop: Optional[dict] = None) -> dict:
        """Crée une demande sans double réservation du créneau.

        `stop` : correspondance calculée par le matching (`pickup`, `dropoff`
        en (lat, lon), `passage_time`, `detour_min`), enregistrée avec la
        demande pour le conducteur et pour le cumul des détours.
        """
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Sérialise les réservations du même passager, y compris pour deux
            # trajets différents validés simultanément dans deux onglets.
            cursor.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (passenger_id,))
            cursor.fetchone()
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.user_id,
                    r.status,
                    r.ride_time,
                    r.is_offer,
                    u.car_seats,
                    r.ride_time <= LOCALTIMESTAMP AS is_past
                FROM rides r
                JOIN users u ON u.id = r.user_id
                WHERE r.id = %s
                FOR UPDATE OF r
                """,
                (ride_id,),
            )
            ride = cursor.fetchone()
            if not ride:
                return {"status": "not_found"}
            if ride["user_id"] == passenger_id:
                return {"status": "own_ride"}
            if (
                ride["status"] != "active"
                or not ride["is_offer"]
                or ride["is_past"]
            ):
                return {"status": "unavailable"}

            cursor.execute(
                "SELECT 1 FROM ride_selections WHERE ride_id = %s AND passenger_id = %s",
                (ride_id, passenger_id),
            )
            if cursor.fetchone():
                return {"status": "already_selected"}

            cursor.execute(
                """
                SELECT 1
                FROM ride_selections rs
                JOIN rides reserved ON reserved.id = rs.ride_id
                WHERE rs.passenger_id = %s
                  AND reserved.status = 'active'
                  AND rs.status IN ('pending', 'accepted')
                  AND ABS(EXTRACT(EPOCH FROM reserved.ride_time - %s::timestamp)) < %s * 60
                LIMIT 1
                """,
                (passenger_id, ride["ride_time"], config.SLOT_CONFLICT_MIN),
            )
            if cursor.fetchone():
                return {"status": "time_conflict"}

            # Pas de reservation sur un creneau ou l'on propose deja sa
            # voiture : on ne peut pas etre conducteur et passager a la fois.
            cursor.execute(
                """
                SELECT 1 FROM rides
                WHERE user_id = %s AND is_offer AND status = 'active'
                  AND ABS(EXTRACT(EPOCH FROM ride_time - %s::timestamp)) < %s * 60
                LIMIT 1
                """,
                (passenger_id, ride["ride_time"], config.SLOT_CONFLICT_MIN),
            )
            if cursor.fetchone():
                return {"status": "time_conflict"}

            cursor.execute(
                "SELECT COUNT(*) FROM ride_selections WHERE ride_id = %s AND status = 'accepted'",
                (ride_id,),
            )
            occupied = int(cursor.fetchone()["count"])
            capacity = int(ride["car_seats"] or 0)
            if capacity <= occupied:
                return {"status": "full"}

            stop = stop or {}
            pickup, dropoff = stop.get("pickup"), stop.get("dropoff")
            cursor.execute(
                """
                INSERT INTO ride_selections (
                    ride_id, passenger_id, status,
                    pickup_lat, pickup_lon, dropoff_lat, dropoff_lon, passage_time, detour_min
                )
                VALUES (%s, %s, 'pending', %s, %s, %s, %s, %s, %s)
                """,
                (
                    ride_id, passenger_id,
                    pickup[0] if pickup else None, pickup[1] if pickup else None,
                    dropoff[0] if dropoff else None, dropoff[1] if dropoff else None,
                    stop.get("passage_time"), stop.get("detour_min"),
                ),
            )
            conn.commit()
            return {
                "status": "selected",
                "available_seats": capacity - occupied,
            }
        finally:
            conn.close()

    def decide_ride_selection(
        self, ride_id: int, passenger_id: int, driver_id: int, decision: str
    ) -> dict:
        """Accepte ou refuse une demande appartenant au conducteur connecté."""
        if decision not in ("accept", "reject"):
            raise ValueError("Invalid ride selection decision")
        self.archive_expired_rides()
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        try:
            # Même ordre de verrouillage que select_ride pour éviter les conflits.
            cursor.execute("SELECT id FROM users WHERE id = %s FOR UPDATE", (passenger_id,))
            cursor.fetchone()
            cursor.execute(
                """
                SELECT r.id, r.status, r.ride_time, u.car_seats,
                       r.ride_time <= LOCALTIMESTAMP AS is_past
                FROM rides r
                JOIN users u ON u.id = r.user_id
                WHERE r.id = %s AND r.user_id = %s
                FOR UPDATE OF r
                """,
                (ride_id, driver_id),
            )
            ride = cursor.fetchone()
            if not ride:
                return {"status": "not_found"}
            if ride["status"] != "active" or ride["is_past"]:
                return {"status": "unavailable"}

            cursor.execute(
                """
                SELECT id, status FROM ride_selections
                WHERE ride_id = %s AND passenger_id = %s
                FOR UPDATE
                """,
                (ride_id, passenger_id),
            )
            selection = cursor.fetchone()
            if not selection:
                return {"status": "not_found"}
            if selection["status"] == "rejected" or (
                decision == "accept" and selection["status"] == "accepted"
            ):
                return {"status": "already_decided"}

            cursor.execute(
                "SELECT COUNT(*) FROM ride_selections WHERE ride_id = %s AND status = 'accepted'",
                (ride_id,),
            )
            occupied = int(cursor.fetchone()["count"])
            capacity = int(ride["car_seats"] or 0)
            if decision == "accept":
                if occupied >= capacity:
                    return {"status": "full"}
                cursor.execute(
                    """
                    SELECT 1 FROM ride_selections rs
                    JOIN rides r ON r.id = rs.ride_id
                    WHERE rs.passenger_id = %s AND rs.status = 'accepted'
                      AND rs.ride_id <> %s AND r.status = 'active'
                      AND date_trunc('minute', r.ride_time) = date_trunc('minute', %s::timestamp)
                    LIMIT 1
                    """,
                    (passenger_id, ride_id, ride["ride_time"]),
                )
                if cursor.fetchone():
                    return {"status": "time_conflict"}

            new_status = "accepted" if decision == "accept" else "rejected"
            cursor.execute(
                "UPDATE ride_selections SET status = %s WHERE id = %s",
                (new_status, selection["id"]),
            )
            conn.commit()
            new_occupied = occupied + (1 if new_status == "accepted" else 0)
            if new_status == "rejected" and selection["status"] == "accepted":
                new_occupied -= 1
            return {
                "status": new_status,
                "available_seats": max(0, capacity - new_occupied),
            }
        finally:
            conn.close()

    def cancel_ride_selection(self, ride_id: int, passenger_id: int) -> dict:
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        # Verrouille la reservation avant de la supprimer : une confirmation
        # de suivi ne peut pas s'intercaler entre la verification et le DELETE.
        cursor.execute(
            """
            SELECT id, driver_picked_up_at, passenger_onboard_at,
                   driver_completed_at, passenger_arrived_at
            FROM ride_selections
            WHERE ride_id = %s AND passenger_id = %s
            FOR UPDATE
            """,
            (ride_id, passenger_id),
        )
        selection = cursor.fetchone()
        if not selection:
            conn.rollback()
            conn.close()
            return {"status": "not_found"}

        # Des qu'une etape du suivi est confirmee, la course a commence :
        # l'interface masque deja le bouton, mais l'API doit aussi refuser
        # un appel direct pour garder l'historique et les avis coherents.
        tracking_steps = (
            "driver_picked_up_at",
            "passenger_onboard_at",
            "driver_completed_at",
            "passenger_arrived_at",
        )
        if any(selection[step] is not None for step in tracking_steps):
            conn.rollback()
            conn.close()
            return {"status": "already_started"}

        cursor.execute("DELETE FROM ride_selections WHERE id = %s", (selection["id"],))

        cursor.execute(
            """
            SELECT u.car_seats - COUNT(rs.id) AS available_seats
            FROM rides r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN ride_selections rs ON rs.ride_id = r.id AND rs.status = 'accepted'
            WHERE r.id = %s
            GROUP BY u.car_seats
            """,
            (ride_id,),
        )
        row = cursor.fetchone()
        conn.commit()
        conn.close()
        return {
            "status": "cancelled",
            "available_seats": max(0, int(row["available_seats"] if row else 0)),
        }

    def get_selection_stop(self, ride_id: int, passenger_id: int) -> Optional[tuple]:
        """Prise en charge et depose d'une demande, en (lat, lon), ou None si
        la demande n'en a pas (reservation plus ancienne)."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
            FROM ride_selections WHERE ride_id = %s AND passenger_id = %s
            """,
            (ride_id, passenger_id),
        )
        row = cursor.fetchone()
        conn.close()
        if not row or row["pickup_lat"] is None or row["dropoff_lat"] is None:
            return None
        return ((row["pickup_lat"], row["pickup_lon"]), (row["dropoff_lat"], row["dropoff_lon"]))

    def get_accepted_stops(self, ride_ids: List[int]) -> dict[int, list]:
        """Arrets des passagers deja acceptes, par trajet conducteur :
        {ride_id: [(prise en charge, depose)]}, points en (lat, lon). Sert a
        additionner les detours quand la voiture se remplit."""
        if not ride_ids:
            return {}
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT ride_id, pickup_lat, pickup_lon, dropoff_lat, dropoff_lon
            FROM ride_selections
            WHERE ride_id = ANY(%s) AND status = 'accepted'
              AND pickup_lat IS NOT NULL AND dropoff_lat IS NOT NULL
            """,
            (list(ride_ids),),
        )
        stops: dict[int, list] = {}
        for row in cursor.fetchall():
            stops.setdefault(int(row["ride_id"]), []).append(
                ((row["pickup_lat"], row["pickup_lon"]), (row["dropoff_lat"], row["dropoff_lon"]))
            )
        conn.close()
        return stops

    def get_driver_offers(self, driver_id: int, archived: bool = False) -> list[dict]:
        self.archive_expired_rides()
        target_status = "archived" if archived else "active"
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
                r.*,
                u.car_seats,
                COUNT(rs.id) FILTER (WHERE rs.status = 'accepted') OVER (PARTITION BY r.id) AS occupied_seats,
                rs.selected_at,
                rs.status AS selection_status,
                p.id AS passenger_id,
                p.name AS passenger_name,
                p.email AS passenger_email,
                rs.pickup_lat, rs.pickup_lon, rs.dropoff_lat, rs.dropoff_lon,
                rs.passage_time, rs.detour_min
            FROM rides r
            JOIN users u ON u.id = r.user_id
            LEFT JOIN ride_selections rs ON rs.ride_id = r.id
            LEFT JOIN users p ON p.id = rs.passenger_id
            WHERE r.user_id = %s AND r.status = %s
            ORDER BY r.ride_time, rs.selected_at
            """,
            (driver_id, target_status),
        )
        rows = cursor.fetchall()
        conn.close()

        offers: dict[int, dict] = {}
        for row in rows:
            ride_id = int(row["id"])
            if ride_id not in offers:
                capacity = int(row["car_seats"] or 0)
                occupied = int(row["occupied_seats"] or 0)
                offers[ride_id] = {
                    "id": ride_id,
                    "ride_type": row["ride_type"],
                    "ride_time": row["ride_time"],
                    "start_lat": row["start_lat"],
                    "start_lon": row["start_lon"],
                    "end_lat": row["end_lat"],
                    "end_lon": row["end_lon"],
                    "status": row["status"],
                    "archived_at": row["archived_at"],
                    "is_offer": bool(row["is_offer"]),
                    # Trajet de l'emploi du temps (event_id) ou cree a la main (None).
                    "event_id": row["event_id"],
                    "start_address": row["start_address"] or "",
                    "end_address": row["end_address"] or "",
                    "car_seats": capacity,
                    "occupied_seats": occupied,
                    "available_seats": max(0, capacity - occupied),
                    "passengers": [],
                }
            if row["passenger_id"] is not None:
                offers[ride_id]["passengers"].append(
                    {
                        "id": int(row["passenger_id"]),
                        "name": row["passenger_name"],
                        "email": row["passenger_email"],
                        "selected_at": row["selected_at"],
                        "selection_status": row["selection_status"],
                        # Ce que le conducteur doit savoir avant d'accepter :
                        # quand il passe, ce que ca lui coute, et si le
                        # passager monte ou descend en chemin.
                        "passage_time": row["passage_time"],
                        "detour_min": row["detour_min"],
                        "pickup_on_the_way": _apart(row["pickup_lat"], row["pickup_lon"], row["start_lat"], row["start_lon"]),
                        "dropoff_on_the_way": _apart(row["dropoff_lat"], row["dropoff_lon"], row["end_lat"], row["end_lon"]),
                    }
                )
        return list(offers.values())

    def get_passenger_selections(self, passenger_id: int, archived: bool = False) -> list[dict]:
        self.archive_expired_rides()
        target_status = "archived" if archived else "active"
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
                rs.id AS selection_id,
                rs.selected_at,
                rs.status AS selection_status,
                r.id AS ride_id,
                r.ride_type,
                r.ride_time,
                r.start_lat,
                r.start_lon,
                r.end_lat,
                r.end_lon,
                r.status,
                d.id AS driver_id,
                d.name AS driver_name
            FROM ride_selections rs
            JOIN rides r ON r.id = rs.ride_id
            JOIN users d ON d.id = r.user_id
            WHERE rs.passenger_id = %s AND r.status = %s
            ORDER BY r.ride_time
            """,
            (passenger_id, target_status),
        )
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    # --- ROUTING CACHE ---
    def get_routing_cache(self, cache_key: str) -> Optional[dict]:
        """Retourne un calcul d'itineraire et comptabilise son utilisation."""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT geometry, distance_m, duration_s
            FROM routing_cache
            WHERE cache_key = %s
            """,
            (cache_key,),
        )
        row = cursor.fetchone()
        if row:
            cursor.execute(
                """
                UPDATE routing_cache
                SET last_used_at = NOW(), hit_count = hit_count + 1
                WHERE cache_key = %s
                """,
                (cache_key,),
            )
            conn.commit()
        conn.close()
        return dict(row) if row else None

    def upsert_routing_cache(
        self,
        cache_key: str,
        start: tuple[float, float],
        end: tuple[float, float],
        result: dict,
        via: Optional[tuple[float, float]] = None,
        provider: str = "ors",
        profile: str = "driving-car",
    ) -> None:
        """Enregistre ou actualise un calcul d'itineraire reutilisable."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO routing_cache (
                cache_key, provider, profile,
                start_lat, start_lon, via_lat, via_lon, end_lat, end_lon,
                geometry, distance_m, duration_s
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cache_key) DO UPDATE SET
                provider = EXCLUDED.provider,
                profile = EXCLUDED.profile,
                geometry = EXCLUDED.geometry,
                distance_m = EXCLUDED.distance_m,
                duration_s = EXCLUDED.duration_s,
                created_at = NOW(),
                last_used_at = NOW()
            """,
            (
                cache_key,
                provider,
                profile,
                start[0],
                start[1],
                via[0] if via else None,
                via[1] if via else None,
                end[0],
                end[1],
                Json(result.get("geometry", [])),
                float(result.get("distance_m", 0.0)),
                float(result.get("duration_s", 0.0)),
            ),
        )
        conn.commit()
        conn.close()


db = Database()
