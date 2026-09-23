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


class Database:
    def __init__(self):
        self.db_url = config.DATABASE_URL

    def get_connection(self) -> psycopg2.extensions.connection:
        """Crée une connexion à la base de données"""
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

    # --- USERS ---
    """Crée un nouvel utilisateur"""

    def create_user(self, user: User) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO users (name, email, hashed_password, role, car_seats, start_address, start_lat, start_lon, time_tolerance_min,
                               school_address, school_lat, school_lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user.name,
                user.email,
                user.hashed_password,
                user.role,
                user.car_seats,
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
        """Récupère un utilisateur par email"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User.from_dict(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Récupère un utilisateur par ID"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User.from_dict(row)
        return None

    def get_all_users(self) -> List[User]:
        """Récupère tous les utilisateurs"""
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
        """Met à jour un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s, role = %s, car_seats = %s, start_address = %s, start_lat = %s, start_lon = %s,
                time_tolerance_min = %s, school_address = %s, school_lat = %s, school_lon = %s
            WHERE id = %s
            """,
            (
                user.name,
                user.email,
                user.role,
                user.car_seats,
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

    # --- EVENTS ---
    def create_event(self, event: Event) -> int:
        """Crée un nouvel événement"""
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
        """Récupère tous les événements d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM events WHERE user_id = %s ORDER BY start_time", (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Event.from_dict(row) for row in rows]

    def delete_events_by_user(self, user_id: int):
        """Supprime tous les événements d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM events WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    # --- RIDES ---
    def create_ride(self, ride: Ride) -> int:
        """Crée un nouveau trajet"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO rides (user_id, event_id, ride_type, ride_time, start_lat, start_lon, end_lat, end_lon, status, archived_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            ),
        )
        ride_id = cursor.fetchone()[0]
        conn.commit()
        conn.close()
        return ride_id

    def get_rides_by_user(self, user_id: int) -> List[Ride]:
        """Récupère tous les trajets d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            "SELECT * FROM rides WHERE user_id = %s ORDER BY ride_time", (user_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [Ride.from_dict(row) for row in rows]

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
        """Récupère tous les trajets"""
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
        """Supprime tous les trajets d'un utilisateur"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rides WHERE user_id = %s", (user_id,))
        conn.commit()
        conn.close()

    def delete_active_rides_by_user(self, user_id: int):
        """Supprime uniquement les propositions en cours et preserve l'historique."""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM rides WHERE user_id = %s AND status = 'active'",
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

    # --- RIDE SELECTIONS ---
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

    def select_ride(self, ride_id: int, passenger_id: int) -> dict:
        """Crée une demande sans double réservation du créneau."""
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
                    u.role AS owner_role,
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
                or ride["owner_role"] != "driver"
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
                  AND date_trunc('minute', reserved.ride_time) = date_trunc('minute', %s::timestamp)
                LIMIT 1
                """,
                (passenger_id, ride["ride_time"]),
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

            cursor.execute(
                """
                INSERT INTO ride_selections (ride_id, passenger_id, status)
                VALUES (%s, %s, 'pending')
                """,
                (ride_id, passenger_id),
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
        cursor.execute(
            """
            DELETE FROM ride_selections
            WHERE ride_id = %s AND passenger_id = %s
            RETURNING id
            """,
            (ride_id, passenger_id),
        )
        deleted = cursor.fetchone()
        if not deleted:
            conn.rollback()
            conn.close()
            return {"status": "not_found"}

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
                p.email AS passenger_email
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

# Instance globale

db = Database()
