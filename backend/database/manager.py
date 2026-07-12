"""Service de gestion de la base de données PostgreSQL – opérations CRUD."""
import time
from typing import List, Optional

import psycopg2
from psycopg2 import OperationalError
from psycopg2.extras import RealDictCursor

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
            INSERT INTO users (name, email, hashed_password, role, start_address, start_lat, start_lon, time_tolerance_min,
                               school_address, school_lat, school_lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user.name,
                user.email,
                user.hashed_password,
                user.role,
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
            SET name = %s, email = %s, role = %s, start_address = %s, start_lat = %s, start_lon = %s,
                time_tolerance_min = %s, school_address = %s, school_lat = %s, school_lon = %s
            WHERE id = %s
            """,
            (
                user.name,
                user.email,
                user.role,
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
            INSERT INTO rides (user_id, event_id, ride_type, ride_time, start_lat, start_lon, end_lat, end_lon)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
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

    def get_all_rides(self) -> List[Ride]:
        """Récupère tous les trajets"""
        conn = self.get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM rides ORDER BY ride_time")
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


# Instance globale

db = Database()
